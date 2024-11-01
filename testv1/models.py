# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Gallery(db.Model):
    __tablename__ = 'galleries'
    id = db.Column(db.String(50), primary_key=True)  # 변경된 부분
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=True)
    posts = db.relationship('Post', backref='gallery', lazy=True)

class CrawlingTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gallery_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    gallery_id = db.Column(db.String(50), db.ForeignKey('galleries.id'), nullable=False)  # 변경된 부분
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)
    images = db.relationship('Image', secondary='post_images', backref=db.backref('posts', lazy=True))

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)  # 이 부분은 변경하지 않아도 됩니다.
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(200), nullable=False)

class PostImage(db.Model):
    __tablename__ = 'post_images'
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), primary_key=True)
