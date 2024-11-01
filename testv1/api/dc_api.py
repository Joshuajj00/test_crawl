import requests
from bs4 import BeautifulSoup
from datetime import datetime

class DCInsideAPI:
    def __init__(self, app):
        self.app = app
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': app.config['USER_AGENT']})

    def fetch_post_list(self, gallery_id, page=1):
        url = f'https://gall.dcinside.com/board/lists/?id={gallery_id}&page={page}'
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = []

        for row in soup.select('tr.ub-content'):
            post = {}
            post['id'] = row.select_one('.gall_num').text.strip()
            post['title'] = row.select_one('.gall_tit a').text.strip()
            post['author'] = row.select_one('.gall_writer').text.strip()
            post['date'] = row.select_one('.gall_date').text.strip()
            post['view_count'] = row.select_one('.gall_count').text.strip()
            post['comment_count'] = row.select_one('.gall_comment').text.strip()
            posts.append(post)

        return posts

    def fetch_post_detail(self, gallery_id, post_id):
        url = f'https://gall.dcinside.com/board/view/?id={gallery_id}&no={post_id}'
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        post = {}
        post['id'] = post_id
        post['title'] = soup.select_one('.title_subject').text.strip()
        post['author'] = soup.select_one('.gall_writer').text.strip()
        post['content'] = soup.select_one('.write_div').text.strip()
        post['date'] = soup.select_one('.gall_date').text.strip()
        post['view_count'] = soup.select_one('.gall_count').text.strip()
        post['comment_count'] = soup.select_one('.gall_comment').text.strip()
        
        # 이미지 URL 추출
        post['images'] = [img['src'] for img in soup.select('.write_div img')]

        return post

    def fetch_comments(self, gallery_id, post_id):
        url = f'https://gall.dcinside.com/board/view/?id={gallery_id}&no={post_id}'
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        comments = []

        for comment in soup.select('.comment_box'):
            c = {}
            c['id'] = comment['data-no']
            c['author'] = comment.select_one('.nickname').text.strip()
            c['content'] = comment.select_one('.comment_memo').text.strip()
            c['date'] = comment.select_one('.date_time').text.strip()
            comments.append(c)

        return comments

    def close(self):
        self.session.close()
