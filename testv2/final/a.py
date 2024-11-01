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
    # 페이지 소스 저장
    save_page_source(driver, 'page_source.html')

    logger.debug("Waiting for comment section to load...")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "view_comment"))
        )
        logger.debug("Comment section loaded.")
    except Exception as e:
        logger.error("Comment section did not load properly.")
        driver.quit()
        return []

    logger.debug("Scrolling to bottom of page...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    logger.debug("Page scrolled. Waiting for 2 seconds for content to load.")

    logger.debug("Getting page source...")
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    logger.debug("Page source retrieved and parsed with BeautifulSoup.")

    comments = []
    # 댓글 리스트 찾기
    comment_elements = soup.find_all(['li', 'div'], class_=['ub-content', 'reply_info'])
    logger.info(f"Found {len(comment_elements)} comment elements.")

    for index, comment in enumerate(comment_elements, 1):
        logger.debug(f"Processing comment {index}...")

        # gall_writer ub-writer span을 찾아 data-uid 추출
        gall_writer = comment.find('span', class_='gall_writer ub-writer')
        data_uid = gall_writer.get('data-uid', '') if gall_writer else ''
        logger.debug(f"data-uid: {data_uid}")

        author_name = "Unknown"
        author_ip = ""
        gallog_url = ""

        if gall_writer:
            author_name = gall_writer.get('data-nick', 'Unknown')
            author_ip = gall_writer.get('data-ip', '')
            # 갤로그 URL 추출
            gallog_link = gall_writer.find('a', class_='writer_nikcon')
            if gallog_link and 'onclick' in gallog_link.attrs:
                onclick_attr = gallog_link['onclick']
                # onclick="window.open('//gallog.dcinside.com/qqwer2133');"
                match = re.search(r"window\.open\(['\"]?(//gallog\.dcinside\.com/[^'\";]+)['\"]?\)", onclick_attr)
                if match:
                    gallog_url = 'https:' + match.group(1) if match.group(1).startswith('//') else match.group(1)
        
        author_info = f"{author_name}({author_ip})" if author_ip else author_name
        if gallog_url:
            author_info += f" {gallog_url}"
        logger.debug(f"Author info: {author_info}")

        # 날짜 정보 추출
        date_element = comment.find('span', class_='date_time')
        date_info = date_element.get_text(strip=True) if date_element else "Unknown"
        logger.debug(f"Date info: {date_info}")

        # 내용 추출
        content_element = comment.find(['p', 'div'], class_=['usertxt', 'comment_dccon'])
        content_text = ""
        if content_element:
            if 'comment_dccon' in content_element.get('class', []):
                content_text = "디시콘 (이미지)"
            else:
                content_text = content_element.get_text(strip=True)
        content_text = re.sub(r'\s+', ' ', content_text)
        logger.debug(f"Content text: {content_text[:50]}...")

        # 이미지 링크 추출
        images = comment.find_all('img', class_='written_dccon')
        image_links = [img['src'] for img in images] if images else []
        logger.debug(f"Found {len(image_links)} image links.")

        comment_info = {
            'data_uid': data_uid,
            'author': author_info,
            'author_name': author_name,
            'author_ip': author_ip,
            'gallog_url': gallog_url,
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
            f.write(f"data-uid: {comment['data_uid']}\n")
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

