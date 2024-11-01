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

def download_image(image_url, post_number, file_index, headers):
    # 파일 이름 및 저장할 경로 정하기
    filename, ext = os.path.splitext(image_url)
    if not ext:
        ext = '.jpg'  # 기본 확장자 설정
    
    # 다운받을 이름맟 파일
    created_file_name = f"{post_number}_image_{file_index}{ext}"
    created_file_path = os.path.join(IMAGES_FOLDER, created_file_name);
    if os.path.exists(created_file_path):
        return created_file_path;
    

    response = requests.get(image_url,headers = HEADERS);
    logger.info(f"content: {response.content}");

    if response.status_code == 200:
        with open(created_file_path, 'wb') as f:
            f.write(response.content)
        return created_file_name  # 파일 이름만 반환
    return None