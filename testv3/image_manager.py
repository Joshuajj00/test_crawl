import os
import hashlib
import logging
import requests
from config import IMAGES_FOLDER, HEADERS
from urllib.parse import urlparse
from database import get_db

logger = logging.getLogger(__name__)

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def manage_image(post_id, file_path):
    try:
        md5_hash = calculate_md5(file_path)
        db = get_db()
        
        existing_image = db.cursor.execute("SELECT file_path FROM images WHERE md5_hash = ?", (md5_hash,)).fetchone()

        if existing_image:
            # 중복 이미지 발견, 심볼릭 링크 생성
            if os.path.exists(file_path) and file_path != existing_image[0]:
                os.remove(file_path)
                os.symlink(existing_image[0], file_path)
                logger.info(f"중복 이미지 발견. 심볼릭 링크 생성: {file_path} -> {existing_image[0]}")
        else:
            # 새로운 이미지, 데이터베이스에 저장
            db.insert_image(post_id, file_path, md5_hash)
            logger.info(f"새로운 이미지 저장: {file_path}")
        
        return file_path

    except Exception as e:
        logger.error(f"이미지 관리 중 오류 발생: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return None

def download_image(image_url, post_number, original_filename):
    response = requests.get(image_url)
    if response.status_code == 200:
        # 파일 확장자 추출
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.jpg'  # 기본 확장자 설정
        
        # 새 파일 이름 생성 (중복 방지)
        new_filename = f"{post_number}_{original_filename}"
        file_path = os.path.join(IMAGES_FOLDER, new_filename)
        
        # 파일 이름 중복 확인 및 처리
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(new_filename)
            new_filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(IMAGES_FOLDER, new_filename)
            counter += 1

        with open(file_path, 'wb') as f:
            f.write(response.content)
        return new_filename  # 파일 이름만 반환
    return None