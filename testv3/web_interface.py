from flask import Flask, render_template, send_from_directory, jsonify, request, abort
import os
from database import get_db
from config import IMAGES_FOLDER
from admin import admin

app = Flask(__name__)
app.register_blueprint(admin, url_prefix='/admin')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    posts, total_posts = db.get_posts_with_details(page, per_page)
    return render_template('posts.html', posts=posts, page=page, per_page=per_page, total_posts=total_posts)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    db = get_db()
    post = db.get_post(post_id)
    if not post:
        abort(404)
    comments = db.get_comments(post_id)
    images = db.get_images(post_id)
    return render_template('post_detail.html', post=post, comments=comments, images=images)
    
    
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route('/api/posts')
def api_posts():
    db = get_db()
    posts = db.get_recent_posts(100)
    return jsonify([dict(post) for post in posts])

if __name__ == '__main__':
    app.run(debug=True)