from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 브라우저 창을 띄우지 않고 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def crawl_comments(url):
    driver = setup_driver()
    driver.get(url)
    
    # 댓글 영역이 로드될 때까지 대기
    WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.CLASS_NAME, "view_comment"))
    )
    
    # 페이지 스크롤
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # time.sleep(2)  # 댓글이 모두 로드될 때까지 기다림
    
    # 페이지 소스 가져오기
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    # 댓글 추출
    comments = []
    for comment in soup.find_all('p', class_='usertxt'):
        comment_text = comment.get_text(strip=True)
        comment_text = re.sub(r'\s+', ' ', comment_text)  # 연속된 공백 제거
        comments.append(comment_text)
    
    driver.quit()
    return comments

def save_comments_to_file(comments, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for comment in comments:
            f.write(comment + '\n')

# 크롤링 실행
url = "https://gall.dcinside.com/mgallery/board/view/?id=vr&no=4244818"
comments = crawl_comments(url)

# 결과 저장
if comments:
    save_comments_to_file(comments, 'comments.txt')
    print(f"{len(comments)}개의 댓글을 comments.txt 파일에 저장했습니다.")
else:
    print("추출된 댓글이 없습니다.")
