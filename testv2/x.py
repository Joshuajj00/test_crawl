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
import requests
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    logger.debug("Setting up Chrome driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    logger.debug("Chrome driver setup complete.")
    return driver

def save_page_source(driver, filename):
    logger.info(f"Saving page source to {filename}")
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)

def save_comments_js(url, filename):
    logger.info(f"Attempting to download comments.js from {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"comments.js saved to {filename}")
        else:
            logger.warning(f"Failed to download comments.js. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error downloading comments.js: {str(e)}")

def crawl_comments(url):
    logger.info(f"Starting to crawl comments from: {url}")
    driver = setup_driver()
    driver.get(url)
    logger.debug(f"Navigated to {url}")
    
    # 페이지 소스 저장
    save_page_source(driver, 'page_source.html')
    
    # comments.js 파일 저장
    comments_js_url = "https://gall.dcinside.com/js/comment.js"
    save_comments_js(comments_js_url, 'comments.js')
    
    logger.debug("Waiting for comment section to load...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "view_comment"))
    )
    logger.debug("Comment section loaded.")
    
    logger.debug("Scrolling to bottom of page...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    logger.debug("Page scrolled. Waiting for 2 seconds for content to load.")
    
    logger.debug("Getting page source...")
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    logger.debug("Page source retrieved and parsed with BeautifulSoup.")
    
    comments = []
    comment_elements = soup.find_all('li', class_='ub-content')
    logger.info(f"Found {len(comment_elements)} comment elements.")
    
    for index, comment in enumerate(comment_elements, 1):
        logger.debug(f"Processing comment {index}...")
        
        author = comment.find('span', class_='nickname')
        if author:
            author_name = author.get_text(strip=True)
            author_id = author.get('data-uid', '')
            author_ip = author.get('data-ip', '')
            if author_id:
                author_info = f"{author_name}({author_id})"
            else:
                author_info = f"{author_name}({author_ip})"
        else:
            author_info = "Unknown"
        logger.debug(f"Author info: {author_info}")
        
        date = comment.find('span', class_='date_time')
        date_info = date.get_text(strip=True) if date else "Unknown"
        logger.debug(f"Date info: {date_info}")
        
        content = comment.find('p', class_='usertxt')
        content_text = content.get_text(strip=True) if content else ""
        content_text = re.sub(r'\s+', ' ', content_text)
        logger.debug(f"Content text: {content_text[:50]}...")  # 로그에는 내용의 일부만 표시
        
        images = comment.find_all('img', class_='written_dccon')
        image_links = [img['src'] for img in images] if images else []
        logger.debug(f"Found {len(image_links)} image links.")
        
        comment_info = {
            'author': author_info,
            'date': date_info,
            'content': content_text,
            'images': image_links
        }
        comments.append(comment_info)
        logger.debug(f"Processed comment {index}.")
    
    driver.quit()
    logger.debug("Chrome driver closed.")
    logger.info(f"Crawling complete. Retrieved {len(comments)} comments.")
    return comments

def save_comments_to_file(comments, filename):
    logger.info(f"Saving {len(comments)} comments to file: {filename}")
    with open(filename, 'w', encoding='utf-8') as f:
        for index, comment in enumerate(comments, 1):
            logger.debug(f"Writing comment {index} to file...")
            f.write(f"작성자: {comment['author']}\n")
            f.write(f"작성시간: {comment['date']}\n")
            f.write(f"내용: {comment['content']}\n")
            if comment['images']:
                f.write("이미지 링크:\n")
                for img in comment['images']:
                    f.write(f"- {img}\n")
            f.write("\n" + "-"*50 + "\n\n")
    logger.info(f"Comments successfully saved to {filename}")

# 크롤링 실행
url = "https://gall.dcinside.com/mgallery/board/view/?id=vr&no=4244818"
logger.info(f"Starting crawling process for URL: {url}")
comments = crawl_comments(url)

# 결과 저장
if comments:
    save_comments_to_file(comments, 'detailed_comments.txt')
    logger.info(f"{len(comments)}개의 댓글을 detailed_comments.txt 파일에 저장했습니다.")
else:
    logger.warning("추출된 댓글이 없습니다.")

logger.info("Crawling process completed.")
