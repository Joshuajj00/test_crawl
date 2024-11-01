import os
import logging

# 기본 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'dc_gallery_data')

# 갤러리 URL
GALLERY_URL = "https://gall.dcinside.com/mgallery/board/lists/?id=vr"

# 출력 폴더 설정
OUTPUT_FOLDER = os.path.join(DATA_DIR, "output")
IMAGES_FOLDER = os.path.join(DATA_DIR, "images")
COMPRESSED_DATA_FOLDER = os.path.join(DATA_DIR, "compressed")
LOG_FOLDER = os.path.join(DATA_DIR, "logs")

# 데이터베이스 설정
DB_PATH = os.path.join(DATA_DIR, "dc_gallery.db")

# 크롤링 설정
MAX_PAGES = 5  # 크롤링할 최대 페이지 수
DELAY = 2  # 요청 사이의 지연 시간 (초)

# User-Agent 설정
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# 헤더 설정
HEADERS = {
    'User-Agent': USER_AGENT,
    'Referer': 'https://gall.dcinside.com/'
}

# 로깅 설정
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# 출력 폴더 생성
for folder in [DATA_DIR, OUTPUT_FOLDER, IMAGES_FOLDER, COMPRESSED_DATA_FOLDER, LOG_FOLDER]:
    os.makedirs(folder, exist_ok=True)
