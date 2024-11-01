from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
import logging
from database import get_db

logger = logging.getLogger(__name__)

def setup_driver():
    logger.debug("Chrome driver 설정 시작...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    logger.debug("Chrome driver 설정 완료.")
    return driver

def extract_comments_data(html_content):
    logger.debug("댓글 데이터 추출 시작")
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', string=re.compile('var comment_data'))
    if script_tag:
        script_content = script_tag.string
        match = re.search(r'var comment_data = (\{.*?\});', script_content, re.DOTALL)
        if match:
            comment_data_json = match.group(1)
            try:
                import json
                comment_data = json.loads(comment_data_json)
                logger.debug(f"추출된 댓글 수: {len(comment_data.get('comments', []))}")
                return comment_data
            except json.JSONDecodeError as e:
                logger.error(f"JSON 디코딩 오류: {e}")
    logger.warning("댓글 데이터를 찾을 수 없음")
    return None

def crawl_comments_selenium(url):
    logger.info(f"Selenium을 사용하여 댓글 크롤링 시작: {url}")
    driver = setup_driver()
    try:
        logger.debug(f"페이지 로드 중: {url}")
        driver.get(url)
        logger.debug("페이지 로드 완료")

        logger.debug("댓글 영역 대기 중...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "comment_wrap"))
        )
        logger.debug("댓글 영역 로드됨")
        
        # 페이지 끝까지 스크롤
        logger.debug("페이지 스크롤 시작")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(5):  # 최대 5번 스크롤 시도
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logger.debug("페이지 스크롤 완료")

        page_source = driver.page_source
        comment_data = extract_comments_data(page_source)
        
        if not comment_data:
            logger.warning("댓글 데이터를 추출할 수 없습니다.")
            return []

        comments = []
        for comment in comment_data.get('comments', []):
            comment_info = {
                'author': comment.get('name', '익명'),
                'content': comment.get('memo', ''),
                'date': comment.get('date', '')
            }
            comments.append(comment_info)

        logger.info(f"{len(comments)}개의 댓글을 크롤링했습니다.")
        return comments

    except Exception as e:
        logger.error(f"댓글 크롤링 중 오류 발생: {str(e)}", exc_info=True)
        return []

    finally:
        logger.debug("WebDriver 종료")
        driver.quit()

def save_comments_to_db(post_id, comments):
    db = get_db()
    for comment in comments:
        db.insert_comment(post_id, comment)
    logger.info(f"{len(comments)}개의 댓글을 데이터베이스에 저장했습니다.")

def process_post_comments_selenium(post_url, post_id):
    comments = crawl_comments_selenium(post_url)
    save_comments_to_db(post_id, comments)
    return len(comments)