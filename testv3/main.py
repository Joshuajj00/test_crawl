import argparse
import logging
from gallery_crawler import crawl_gallery
from comment_crawler import crawl_comments
from config import GALLERY_URL, OUTPUT_FOLDER
from database import get_db  # db 대신 get_db 함수를 import
from compression import compress_old_data
from web_interface import app as web_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='DC Inside Gallery Crawler')
    parser.add_argument('--gallery', action='store_true', help='Crawl gallery posts')
    parser.add_argument('--comments', action='store_true', help='Crawl comments')
    parser.add_argument('--post-url', type=str, help='URL of the post to crawl comments from')
    parser.add_argument('--compress', action='store_true', help='Compress old data')
    parser.add_argument('--web', action='store_true', help='Start web interface')
    args = parser.parse_args()

    if args.gallery:
        logger.info("Starting gallery crawling...")
        crawl_gallery(GALLERY_URL, OUTPUT_FOLDER)
    
    if args.comments:
        if args.post_url:
            logger.info(f"Starting comment crawling for post: {args.post_url}")
            crawl_comments(args.post_url, OUTPUT_FOLDER)
        else:
            logger.error("Post URL is required for comment crawling. Use --post-url")

    if args.compress:
        logger.info("Starting data compression...")
        compress_old_data()

    if args.web:
        logger.info("Starting web interface...")
        web_app.run(host='0.0.0.0', port=5000, debug=True)

    if not (args.gallery or args.comments or args.compress or args.web):
        logger.warning("No action specified. Use --gallery, --comments, --compress, or --web")

    # 프로그램 종료 시 데이터베이스 연결 닫기
    db = get_db()
    db.close()



if __name__ == "__main__":
    web_app.run(debug=True, host='0.0.0.0', port=5000)
