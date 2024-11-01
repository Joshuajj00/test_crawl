# api/utils.py
from datetime import datetime

def parse_time(time_str):
    # 문자열 형태의 시간을 datetime 객체로 변환하는 함수
    # 예시 구현
    return datetime.strptime(time_str, '%Y.%m.%d %H:%M:%S')
