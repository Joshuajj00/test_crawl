def crawl_dcgallery_page(url, images_folder):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    logger.info(f"갤러리 페이지 크롤링 시작: {url}")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    posts = []
    rows = soup.select('tr.ub-content')
    total_posts = len(rows)
    logger.info(f"총 {total_posts}개의 게시물 발견")
    
    for index, row in enumerate(rows, 1):
        post = {}
        post['number'] = row.select_one('.gall_num').text.strip()
        
        # 글번호가 숫자가 아니거나 4243000 미만인 경우 건너뛰기
        try:
            post_number = int(post['number'])
            if post_number < 4243000:
                logger.info(f"글번호 {post_number}는 4243000 미만이므로 건너뜁니다.")
                continue
        except ValueError:
            logger.warning(f"글번호를 숫자로 변환할 수 없습니다: {post['number']}")
            continue
        
        title_element = row.select_one('.gall_tit a')
        post['title'] = title_element.text.strip()
        post['author'] = row.select_one('.gall_writer').text.strip()
        post['date'] = row.select_one('.gall_date').text.strip()
        post['views'] = row.select_one('.gall_count').text.strip()
        post['votes'] = row.select_one('.gall_recommend').text.strip()
        
        post_url = title_element.get('href')
        if post_url and not post_url.startswith('javascript:'):
            post_url = "https://gall.dcinside.com" + post_url
            logger.debug(f"게시물 URL: {post_url}")
            post['content'], post['image_paths'] = crawl_post_content(post_url, headers, images_folder, post['number'])
        else:
            logger.warning(f"게시물 {post['number']}의 URL을 찾을 수 없음")
            post['content'] = "내용을 불러올 수 없습니다."
            post['image_paths'] = []
        
        posts.append(post)
        
        logger.info(f"진행 중: {index}/{total_posts} 게시물 처리 완료")
        
        time.sleep(random.uniform(1.5, 2.0))
    
    return posts
