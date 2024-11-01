# crawler.py
import asyncio
from api.dc_api import DCInsideAPI
from config import Config
from models import db, Gallery, Post, Comment, Image
from app import app

async def crawl_galleries():
    async with app.app_context():
        galleries = Gallery.query.all()
        tasks = []
        for gallery in galleries:
            tasks.append(crawl_gallery(gallery))
        await asyncio.gather(*tasks)

async def crawl_gallery(gallery):
    api = DCInsideAPI(app)
    try:
        posts = await api.fetch_post_list(gallery.id)
        for post_data in posts:
            # 데이터베이스에 게시물 저장
            pass
    finally:
        await api.close()

if __name__ == '__main__':
    asyncio.run(crawl_galleries())
