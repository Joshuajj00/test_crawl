import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config import HEADERS, DELAY, MAX_PAGES, MIN_POSTING_ID
from database import get_db
from image_manager import manage_image, download_image
from comment_crawler import crawl_comments


logger = logging.getLogger(__name__)

def setup_driver():
    logger.debug("Chrome driver 설정 중...")
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    logger.debug("Chrome driver 설정 완료.")
    return driver
   
def is_document_loaded(driver):
    logger.info("Checking if {} page is loaded.".format(driver.current_url))
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'

def wait_until_document_loaded(driver):
    WebDriverWait(driver, 2).until(
        lambda driver: driver.execute_script('return document.readyState') == 'complete'
    )

def crawl_comments(post_url, post_number):
    driver = setup_driver()
    try:
        driver.get(post_url)
        wait_until_document_loaded(driver);

        comments = []
        comment_elements = driver.find_elements(By.CSS_SELECTOR, '.reply_content')
        
        for comment in comment_elements:
            author = comment.find_element(By.CSS_SELECTOR, '.reply_writer')
            content = comment.find_element(By.CSS_SELECTOR, '.reply_txt')
            
            comment_data = {
                'author': author.text,
                'author_id': author.get_attribute('data-uid'),
                'author_ip': author.get_attribute('data-ip'),
                'content': content.text
            }
            comments.append(comment_data)

        return comments
    finally:
        driver.quit()


def crawl_post_content(post_url, post_number):
    logger.debug(f"게시물 내용 크롤링 시작: {post_url}")
    response = requests.get(post_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.select_one('div.writing_view_box')
    
    if content:
        text_content = content.get_text(strip=True)
        logger.debug(f"게시물 {post_number} 텍스트 내용 추출 완료")
        
        image_elements = content.select('img.tx-content-image')
        image_urls = [img['src'] for img in image_elements if 'src' in img.attrs]
        
        file_box = soup.select_one('div.appending_file_box')
        if file_box:
            for file_link in file_box.select('li a'):
                file_url = file_link['href']
                if file_url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif','.webp')):
                    image_urls.append(file_url)
        
        logger.debug(f"게시물 {post_number}에서 발견된 이미지 수: {len(image_urls)}")
        
        image_paths = []
        for index, image_url in enumerate(image_urls):
            logger.debug(f"이미지 발견: URL: {image_url}")
            image_path = download_image(image_url, post_number, index, HEADERS)
            if image_path:
                image_paths.append(image_path)
        
        return text_content, image_paths
    else:
        logger.warning(f"게시물 {post_number} 내용을 찾을 수 없음")
        return "내용을 불러올 수 없습니다.", []

def crawl_gallery_page(url, db):
    logger.info(f"갤러리 페이지 크롤링 시작: {url}")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    rows = soup.select('tr.ub-content')
    total_posts = len(rows)
    logger.info(f"총 {total_posts}개의 게시물 발견")
    
    for index, row in enumerate(rows, 1):
        post = {}
        post['number'] = row.select_one('.gall_num').text.strip()
        
        try:
            post_number = int(post['number'])
            if post_number < MIN_POSTING_ID:
                logger.info(f"글번호 {post_number}는 {MIN_POSTING_ID} 미만이므로 건너뜁니다.")
                continue
        except ValueError:
            logger.warning(f"글번호를 숫자로 변환할 수 없습니다: {post['number']}")
            continue
        
        title_element = row.select_one('.gall_tit a')
        author_element = row.select_one('.gall_writer')
        post['title'] = title_element.text.strip()
        post['author'] = author_element.text.strip()
        post['author_id'] = author_element.get('data-uid', '')
        post['author_ip'] = author_element.get('data-ip', '')
        post['date'] = row.select_one('.gall_date').text.strip()
        post['views'] = int(row.select_one('.gall_count').text.strip())
        post['votes'] = int(row.select_one('.gall_recommend').text.strip())
        
        # 기존 코드...
        post_url = title_element.get('href')
        if post_url and not post_url.startswith('javascript:'):
            post_url = "https://gall.dcinside.com" + post_url
            # 게시물 내용 크롤링
            post['content'], post['image_paths'] = crawl_post_content(post_url, post['number'])
            # 댓글 크롤링
            comments = crawl_comments(post_url, post['number'])
            post['comments'] = comments
            logger.info(f"게시물 {post['number']}에서 {len(comments)}개의 댓글을 크롤링했습니다.")

        # 나머지 코드...
        else:
            logger.warning(f"게시물 {post['number']}의 URL을 찾을 수 없음")
            post['content'] = "내용을 불러올 수 없습니다."
            post['image_paths'] = []
            post['comments'] = []
        
        existing_post = db.get_post_by_number(post['number'])
        
        if existing_post:
            # 기존 게시물 업데이트
            if (existing_post['views'] != post['views'] or
                existing_post['votes'] != post['votes'] or
                len(db.get_comments(existing_post['id'])) != len(post['comments'])):
                db.update_post(existing_post['id'], post)
                logger.info(f"게시물 {post['number']} 업데이트됨")
            else:
                logger.info(f"게시물 {post['number']} 변경 없음, 건너뜁니다")
            post_id = existing_post['id']
        else:
            # 새 게시물 삽입
            post_id = db.insert_post(post)
            logger.info(f"새 게시물 {post['number']} 삽입됨")
        
        # 댓글 삽입 또는 업데이트
        for comment in post['comments']:
            db.insert_comment(post_id, comment)
        
        posts.append(post)
        
        logger.info(f"진행 중: {index}/{total_posts} 게시물 처리 완료")
        
        delay = random.uniform(DELAY * 0.5, DELAY * 1.5)
        time.sleep(delay)
    
    # 게시글을 최신순으로 정렬
    posts.sort(key=lambda x: int(x['number']), reverse=True)
    
    return posts

def crawl_gallery(gallery_url, output_folder):
    db = get_db()
    total_processed = 0
    for page in range(1, MAX_PAGES + 1):
        url = f"{gallery_url}&page={page}"
        posts = crawl_gallery_page(url, db)
        total_processed += len(posts)
        logger.info(f"{page}/{MAX_PAGES} 페이지 크롤링 완료")
        # 진행도 업데이트
        db.update_crawling_progress(page, MAX_PAGES, total_processed)
    
    logger.info(f"크롤링 완료. 총 {total_processed}개의 게시물 처리됨.")