import json
import gzip
import logging
import os
from datetime import datetime, timedelta
from config import COMPRESSED_DATA_FOLDER
from database import get_db  # db 대신 get_db 함수를 import

logger = logging.getLogger(__name__)

def compress_old_data(days_old=30):
    try:
        db = get_db()  # 데이터베이스 연결 가져오기
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # 오래된 게시물 조회
        db.cursor.execute("SELECT * FROM posts WHERE date < ?", (cutoff_date.strftime('%Y-%m-%d'),))
        old_posts = db.cursor.fetchall()

        for post in old_posts:
            post_id = post[0]
            post_data = {
                'post': post,
                'comments': db.get_comments(post_id),
                'images': db.get_images(post_id)
            }

            # JSON으로 변환
            json_data = json.dumps(post_data, ensure_ascii=False)

            # gzip으로 압축
            compressed_file_path = os.path.join(COMPRESSED_DATA_FOLDER, f"post_{post_id}.json.gz")
            with gzip.open(compressed_file_path, 'wt', encoding='utf-8') as f:
                f.write(json_data)

            logger.info(f"게시물 {post_id} 압축 완료: {compressed_file_path}")

            # 데이터베이스에서 삭제
            db.cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            db.cursor.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
            db.cursor.execute("DELETE FROM images WHERE post_id = ?", (post_id,))

        db.conn.commit()
        logger.info("오래된 데이터 압축 및 정리 완료")

    except Exception as e:
        logger.error(f"데이터 압축 중 오류 발생: {e}")
        db.conn.rollback()

def decompress_data(compressed_file_path):
    try:
        with gzip.open(compressed_file_path, 'rt', encoding='utf-8') as f:
            json_data = f.read()
        return json.loads(json_data)
    except Exception as e:
        logger.error(f"데이터 압축 해제 중 오류 발생: {e}")
        return None
