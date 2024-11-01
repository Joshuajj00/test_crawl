import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random

def crawl_post_content(post_url, headers):
    response = requests.get(post_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.select_one('div.writing_view_box')
    return content.text.strip() if content else "내용을 불러올 수 없습니다."

def crawl_dcgallery_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    rows = soup.select('tr.ub-content')
    total_posts = len(rows)
    
    for index, row in enumerate(rows, 1):
        post = {}
        post['number'] = row.select_one('.gall_num').text.strip()
        title_element = row.select_one('.gall_tit a')
        post['title'] = title_element.text.strip()
        post['author'] = row.select_one('.gall_writer').text.strip()
        post['date'] = row.select_one('.gall_date').text.strip()
        post['views'] = row.select_one('.gall_count').text.strip()
        post['votes'] = row.select_one('.gall_recommend').text.strip()
        
        # 게시물 내용 크롤링
        post_url = title_element.get('href')
        if post_url and not post_url.startswith('javascript:'):
            post_url = "https://gall.dcinside.com" + post_url
            post['content'] = crawl_post_content(post_url, headers)
        else:
            post['content'] = "내용을 불러올 수 없습니다."
        
        posts.append(post)
        
        print(f"진행 중: {index}/{total_posts} 게시물 처리 완료")
        
        # 1500ms에서 2000ms 사이의 랜덤한 시간 동안 대기
        time.sleep(random.uniform(1.5, 2.0))
    
    return posts

def save_to_csv(posts, filename):
    df = pd.DataFrame(posts)
    df.to_csv(filename, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    url = "https://gall.dcinside.com/mgallery/board/lists/?id=vr"
    print("크롤링을 시작합니다...")
    posts = crawl_dcgallery_page(url)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vr_gallery_with_content_{timestamp}.csv"
    
    save_to_csv(posts, filename)
    print(f"크롤링 완료. 결과가 {filename}에 저장되었습니다.")
