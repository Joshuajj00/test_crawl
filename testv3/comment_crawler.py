# comment_crawler.py

import requests
from bs4 import BeautifulSoup
import logging
from config import HEADERS
import time
import random

logger = logging.getLogger(__name__)

def crawl_comments(post_url):
    logger.info(f"댓글 크롤링 시작: {post_url}")
    response = requests.get(post_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    comments = crawl_comments(post_url)
    page = 1

    while True:
        logger.debug(f"댓글 페이지 {page} 크롤링 중...")
        comment_elements = soup.select('.comment_wrap .comment_list .ub-content')

        if not comment_elements:
            logger.debug("더 이상 댓글이 없습니다.")
            break

        for comment_element in comment_elements:
            author_element = comment_element.select_one('.nick')
            content_element = comment_element.select_one('.comment')
            date_element = comment_element.select_one('.date_time')

            if author_element and content_element and date_element:
                author = author_element.text.strip()
                content = content_element.text.strip()
                date = date_element.text.strip()

                comment_data = {
                    'author': author,
                    'content': content,
                    'date': date
                }
                comments.append(comment_data)
            else:
                logger.warning("댓글 요소를 찾을 수 없습니다.")

        # 다음 페이지로 이동
        next_page_element = soup.select_one('.comment_wrap .pagination a.page_next')
        if next_page_element and 'href' in next_page_element.attrs:
            next_page_url = next_page_element['href']
            response = requests.get(next_page_url, headers=HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')
            page += 1

            # 요청 사이에 지연 시간 추가
            delay = random.uniform(1, 2)
            time.sleep(delay)
        else:
            logger.debug("댓글의 마지막 페이지에 도달했습니다.")
            break

    logger.info(f"총 {len(comments)}개의 댓글을 크롤링했습니다.")
    return comments
