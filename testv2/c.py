import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import random
import os
from urllib.parse import urlparse

def download_image(url, folder_path, post_number):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # 파일 이름 생성 (URL의 마지막 부분 사용)
            file_name = os.path.join(folder_path, f"{post_number}_{os.path.basename(urlparse(url).path)}")
            with open(file_name, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return file_name
    except Exception as e:
        print(f"이미지 다운로드 중 오류 발생: {str(e)}")
    return None

def crawl_post_content(post_url, headers, images_folder, post_number):
    response = requests.get(post_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.select_one('div.writing_view_box')
    
    if content:
        text_content = content.get_text(strip=True)
        
        # 이미지 URL 추출 및 다운로드
        images = content.select('img.txc-image')
        image_paths = []
        for img in images:
            if 'src' in img.attrs:
                image_url = img['src']
                image_path = download_image(image_url, images_folder, post_number)
                if image_path:
                    image_paths.append(image_path)
        
        return text_content, image_paths
    else:
        return "내용을 불러올 수 없습니다.", []

def crawl_dcgallery_page(url, images_folder):
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
            post['content'], post['image_paths'] = crawl_post_content(post_url, headers, images_folder, post['number'])
        else:
            post['content'] = "내용을 불러올 수 없습니다."
            post['image_paths'] = []
        
        posts.append(post)
        
        print(f"진행 중: {index}/{total_posts} 게시물 처리 완료")
        
        # 1500ms에서 2000ms 사이의 랜덤한 시간 동안 대기
        time.sleep(random.uniform(1.5, 2.0))
    
    return posts

def save_to_csv(posts, filename):
    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=['number', 'title', 'author', 'date', 'views', 'votes', 'content', 'image_paths'])
        writer.writeheader()
        for post in posts:
            post['image_paths'] = '|'.join(post['image_paths'])  # 이미지 경로를 하나의 문자열로 결합
            writer.writerow(post)

if __name__ == "__main__":
    url = "https://gall.dcinside.com/mgallery/board/lists/?id=vr"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_folder = f"vr_gallery_data_{timestamp}"
    images_folder = os.path.join(base_folder, "images")
    os.makedirs(images_folder, exist_ok=True)
    
    print("크롤링을 시작합니다...")
    posts = crawl_dcgallery_page(url, images_folder)
    
    filename = os.path.join(base_folder, "vr_gallery_data.csv")
    
    save_to_csv(posts, filename)
    print(f"크롤링 완료. 결과가 {filename}에 저장되었습니다.")
    print(f"이미지는 {images_folder} 폴더에 저장되었습니다.")

