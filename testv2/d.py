import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import random
import os
from urllib.parse import urlparse
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def download_image(url, folder_path, post_number, file_name):
    try:
        logger.debug(f"이미지 다운로드 시도: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://gall.dcinside.com/'
        }
        response = requests.get(url, stream=True, headers=headers)
        if response.status_code == 200:
            file_path = os.path.join(folder_path, f"{post_number}_{file_name}")
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            logger.info(f"이미지 다운로드 성공: {file_path}")
            return file_path
        else:
            logger.warning(f"이미지 다운로드 실패. 상태 코드: {response.status_code}, URL: {url}")
    except Exception as e:
        logger.error(f"이미지 다운로드 중 오류 발생: {str(e)}, URL: {url}")
    return None


def crawl_post_content(post_url, headers, images_folder, post_number):
    logger.debug(f"게시물 내용 크롤링 시작: {post_url}")
    response = requests.get(post_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.select_one('div.writing_view_box')
    
    if content:
        text_content = content.get_text(strip=True)
        logger.debug(f"게시물 {post_number} 텍스트 내용 추출 완료")
        
        # 원본 첨부파일 정보 추출
        file_box = soup.select_one('div.appending_file_box')
        image_info = []
        if file_box:
            for file_link in file_box.select('li a'):
                file_name = file_link.text
                file_url = file_link['href']
                image_info.append((file_name, file_url))
        
        logger.debug(f"게시물 {post_number}에서 발견된 첨부파일 수: {len(image_info)}")
        
        image_paths = []
        for file_name, file_url in image_info:
            logger.debug(f"첨부파일 발견: {file_name}, URL: {file_url}")
            image_path = download_image(file_url, images_folder, post_number, file_name)
            if image_path:
                image_paths.append(image_path)
        
        return text_content, image_paths
    else:
        logger.warning(f"게시물 {post_number} 내용을 찾을 수 없음")
        return "내용을 불러올 수 없습니다.", []


def crawl_dcgallery_page(url, images_folder):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    logger.info(f"갤러리 페이지 크롤링 시작: {url}")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    rows = soup.select('tr.ub-content')
    total_posts = len(rows)
    logger.info(f"총 {total_posts}개의 게시물 발견")
    
    for index, row in enumerate(rows, 1):
        post = {}
        post['number'] = row.select_one('.gall_num').text.strip()
        
        # 글번호가 숫자가 아니거나 4243000 미만인 경우 건너뛰기
        try:
            post_number = int(post['number'])
            if post_number < 4243000:
                logger.info(f"글번호 {post_number}는 4243000 미만이므로 건너뜁니다.")
                continue
        except ValueError:
            logger.warning(f"글번호를 숫자로 변환할 수 없습니다: {post['number']}")
            continue
        
        title_element = row.select_one('.gall_tit a')
        post['title'] = title_element.text.strip()
        post['author'] = row.select_one('.gall_writer').text.strip()
        post['date'] = row.select_one('.gall_date').text.strip()
        post['views'] = row.select_one('.gall_count').text.strip()
        post['votes'] = row.select_one('.gall_recommend').text.strip()
        
        post_url = title_element.get('href')
        if post_url and not post_url.startswith('javascript:'):
            post_url = "https://gall.dcinside.com" + post_url
            logger.debug(f"게시물 URL: {post_url}")
            post['content'], post['image_paths'] = crawl_post_content(post_url, headers, images_folder, post['number'])
        else:
            logger.warning(f"게시물 {post['number']}의 URL을 찾을 수 없음")
            post['content'] = "내용을 불러올 수 없습니다."
            post['image_paths'] = []
        
        posts.append(post)
        
        logger.info(f"진행 중: {index}/{total_posts} 게시물 처리 완료")
        
        time.sleep(random.uniform(1.5, 2.0))
    
    return posts

def save_to_csv(posts, filename):
    logger.info(f"CSV 파일 저장 시작: {filename}")
    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=['number', 'title', 'author', 'date', 'views', 'votes', 'content', 'image_paths'])
        writer.writeheader()
        for post in posts:
            post['image_paths'] = '|'.join(post['image_paths'])
            writer.writerow(post)
    logger.info("CSV 파일 저장 완료")

if __name__ == "__main__":
    url = "https://gall.dcinside.com/mgallery/board/lists/?id=vr"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_folder = f"vr_gallery_data_{timestamp}"
    images_folder = os.path.join(base_folder, "images")
    os.makedirs(images_folder, exist_ok=True)
    
    logger.info("크롤링 시작")
    posts = crawl_dcgallery_page(url, images_folder)
    
    filename = os.path.join(base_folder, "vr_gallery_data.csv")
    
    save_to_csv(posts, filename)
    logger.info(f"크롤링 완료. 결과가 {filename}에 저장되었습니다.")
    logger.info(f"이미지는 {images_folder} 폴더에 저장되었습니다.")
