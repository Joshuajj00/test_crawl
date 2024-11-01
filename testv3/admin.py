from flask import Blueprint, render_template, request, jsonify, send_file
from database import get_db
from gallery_crawler import crawl_gallery
from comment_crawler import crawl_comments
from config import OUTPUT_FOLDER
import csv
import io
import threading


admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@admin.route('/panel')
def admin_panel():
    db = get_db()
    progress = db.get_crawling_progress()
    return render_template('admin/panel.html', progress=progress)

@admin.route('/crawling_status')
def crawling_status():
    db = get_db()
    total_posts = db.get_total_posts()
    total_comments = db.get_total_comments()
    last_crawled = db.get_last_crawled_time()

    return jsonify({
        'total_posts': total_posts,
        'total_comments': total_comments,
        'last_crawled': last_crawled
    })


@admin.route('/start_crawling', methods=['POST'])
def start_crawling():
    crawl_type = request.form.get('type')
    target_url = request.form.get('target_url')

    def crawl_task():
        if crawl_type == 'gallery':
            crawl_gallery(target_url, OUTPUT_FOLDER)
        elif crawl_type == 'comments':
            crawl_comments(target_url)
        else:
            logger.error('Invalid crawl type')

    threading.Thread(target=crawl_task).start()
    return jsonify({'message': '크롤링 작업이 시작되었습니다.'})
    
@admin.route('/export_csv')
def export_csv():
    db = get_db()
    db.cursor.execute("SELECT * FROM posts")
    posts = db.cursor.fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'number', 'title', 'author', 'date', 'views', 'votes', 'content'])  # CSV 헤더
    for post in posts:
        writer.writerow(post)
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        attachment_filename='posts_export.csv'
    )
