from flask import Flask, render_template, request, jsonify, abort, redirect, url_for, flash
from config import Config
from models import db, Gallery, Post, Comment, Image, CrawlingTask
from api.dc_api import DCInsideAPI
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# 로깅 설정
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

with app.app_context():
	db.drop_all()
	db.create_all()


@app.route('/')
def index():
    galleries = Gallery.query.all()
    return render_template('index.html', galleries=galleries)

@app.route('/gallery/<string:gallery_id>')
def gallery_posts(gallery_id):
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    gallery = Gallery.query.filter_by(id=gallery_id).first_or_404()
    
    if sort == 'oldest':
        posts = Post.query.filter_by(gallery_id=gallery_id).order_by(Post.created_at.asc())
    elif sort == 'most_comments':
        posts = Post.query.filter_by(gallery_id=gallery_id).order_by(db.func.count(Comment.id).desc())
    else:  # newest
        posts = Post.query.filter_by(gallery_id=gallery_id).order_by(Post.created_at.desc())
    
    posts = posts.paginate(page=page, per_page=20)
    return render_template('gallery_posts.html', gallery=gallery, posts=posts, sort=sort)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)

@app.route('/admin')
def admin_dashboard():
    galleries = Gallery.query.all()
    tasks = CrawlingTask.query.order_by(CrawlingTask.created_at.desc()).limit(10).all()
    return render_template('admin_dashboard.html', galleries=galleries, tasks=tasks)

@app.route('/api/start_crawling/<string:gallery_id>', methods=['POST'])
def start_crawling(gallery_id):
    gallery = Gallery.query.get_or_404(gallery_id)
    task = CrawlingTask(gallery_id=gallery_id, status='pending')
    db.session.add(task)
    db.session.commit()
    # 비동기 작업을 동기적으로 실행
    crawl_gallery(gallery_id, task.id)
    return jsonify({"success": True, "message": f"{gallery.name} 갤러리 크롤링이 시작되었습니다.", "task_id": task.id})

def crawl_gallery(gallery_id, task_id):
    api = DCInsideAPI(app)
    task = CrawlingTask.query.get(task_id)
    task.status = 'running'
    db.session.commit()
    
    try:
        app.logger.info(f"Starting crawling for gallery {gallery_id}")
        posts = api.fetch_post_list(gallery_id)
        for post_data in posts:
            existing_post = Post.query.filter_by(id=post_data['id'], gallery_id=gallery_id).first()
            if existing_post:
                existing_post.title = post_data['title']
                existing_post.content = post_data['content']
                existing_post.updated_at = datetime.now()
                app.logger.info(f"Updated post {existing_post.id}")
            else:
                new_post = Post(
                    id=post_data['id'],
                    gallery_id=gallery_id,
                    title=post_data['title'],
                    author=post_data['author'],
                    content=post_data['content'],
                    created_at=post_data['created_at']
                )
                db.session.add(new_post)
                app.logger.info(f"Added new post {new_post.id}")
            
            comments = api.fetch_comments(gallery_id, post_data['id'])
            for comment_data in comments:
                existing_comment = Comment.query.filter_by(id=comment_data['id'], post_id=post_data['id']).first()
                if not existing_comment:
                    new_comment = Comment(
                        id=comment_data['id'],
                        post_id=post_data['id'],
                        author=comment_data['author'],
                        content=comment_data['content'],
                        created_at=comment_data['created_at']
                    )
                    db.session.add(new_comment)
                    app.logger.info(f"Added new comment {new_comment.id} for post {post_data['id']}")
            
            for image_url in post_data.get('images', []):
                existing_image = Image.query.filter_by(file_path=image_url).first()
                if not existing_image:
                    new_image = Image(file_path=image_url)
                    db.session.add(new_image)
                    new_post.images.append(new_image)
                    app.logger.info(f"Added new image {image_url} for post {post_data['id']}")
        
        db.session.commit()
        task.status = 'completed'
        task.completed_at = datetime.now()
        db.session.commit()
        app.logger.info(f"Crawling completed for gallery {gallery_id}")
    except Exception as e:
        app.logger.error(f"Crawling error for gallery {gallery_id}: {str(e)}")
        task.status = 'failed'
        task.error_message = str(e)
        db.session.commit()
    finally:
        api.close()

@app.route('/api/crawling_status')
def crawling_status():
    running_tasks = CrawlingTask.query.filter_by(status='running').count()
    pending_tasks = CrawlingTask.query.filter_by(status='pending').count()
    return jsonify({
        "running_tasks": running_tasks,
        "pending_tasks": pending_tasks,
    })

@app.route('/add_gallery', methods=['POST'])
def add_gallery():
    name = request.form.get('name')
    url = request.form.get('url')
    gallery_id = request.form.get('gallery_id')
    
    new_gallery = Gallery(id=gallery_id, name=name, url=url)
    db.session.add(new_gallery)
    try:
        db.session.commit()
        flash('갤러리가 성공적으로 추가되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'갤러리 추가 중 오류가 발생했습니다: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter(Post.title.contains(query) | Post.content.contains(query)).paginate(page=page, per_page=20)
    return render_template('search_results.html', posts=posts, query=query)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

