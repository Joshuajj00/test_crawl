import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def crawl_dcgallery_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    for row in soup.select('tr.ub-content'):
        post = {}
        post['number'] = row.select_one('.gall_num').text.strip()
        post['title'] = row.select_one('.gall_tit a').text.strip()
        post['author'] = row.select_one('.gall_writer').text.strip()
        post['date'] = row.select_one('.gall_date').text.strip()
        post['views'] = row.select_one('.gall_count').text.strip()
        post['votes'] = row.select_one('.gall_recommend').text.strip()
        posts.append(post)
    
    return posts

def save_to_csv(posts, filename):
    df = pd.DataFrame(posts)
    df.to_csv(filename, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    url = "https://gall.dcinside.com/mgallery/board/lists/?id=vr"
    posts = crawl_dcgallery_page(url)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vr_gallery_{timestamp}.csv"
    
    save_to_csv(posts, filename)
    print(f"크롤링 완료. 결과가 {filename}에 저장되었습니다.")
