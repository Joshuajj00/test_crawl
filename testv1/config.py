import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@localhost/dc_crawler')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_AGENT = 'Your User Agent'
    MAX_CONCURRENT_TASKS = 5
    REQUEST_TIMEOUT = 10
