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
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def crawl_comments(url):
    driver = setup_driver()
    driver.get(url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "view_comment"))
    )
    
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    comments = []
    for comment in soup.find_all('li', class_='ub-content'):
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
        
        date = comment.find('span', class_='date_time')
        date_info = date.get_text(strip=True) if date else "Unknown"
        
        content = comment.find('p', class_='usertxt')
        content_text = content.get_text(strip=True) if content else ""
        content_text = re.sub(r'\s+', ' ', content_text)
        
        images = comment.find_all('img', class_='written_dccon')
        image_links = [img['src'] for img in images] if images else []
        
        comment_info = {
            'author': author_info,
            'date': date_info,
            'content': content_text,
            'images': image_links
        }
        comments.append(comment_info)
    
    driver.quit()
    return comments

def save_comments_to_file(comments, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for comment in comments:
            f.write(f"작성자: {comment['author']}\n")
            f.write(f"작성시간: {comment['date']}\n")
            f.write(f"내용: {comment['content']}\n")
            if comment['images']:
                f.write("이미지 링크:\n")
                for img in comment['images']:
                    f.write(f"- {img}\n")
            f.write("\n" + "-"*50 + "\n\n")

# 크롤링 실행
url = "https://gall.dcinside.com/mgallery/board/view/?id=vr&no=4244818"
comments = crawl_comments(url)

# 결과 저장
if comments:
    save_comments_to_file(comments, 'detailed_comments.txt')
    print(f"{len(comments)}개의 댓글을 detailed_comments.txt 파일에 저장했습니다.")
else:
    print("추출된 댓글이 없습니다.")
