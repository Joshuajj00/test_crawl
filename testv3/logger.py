import logging
import os
from logging.handlers import RotatingFileHandler
from config import LOG_FOLDER, LOG_FORMAT, LOG_LEVEL

def setup_logger(name, log_file, level=LOG_LEVEL):
    formatter = logging.Formatter(LOG_FORMAT)
    
    file_handler = RotatingFileHandler(
        os.path.join(LOG_FOLDER, log_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger

# 각 모듈별 로거 설정
gallery_logger = setup_logger('gallery_crawler', 'gallery_crawler.log')
comment_logger = setup_logger('comment_crawler', 'comment_crawler.log')
image_logger = setup_logger('image_manager', 'image_manager.log')
database_logger = setup_logger('database', 'database.log')
web_logger = setup_logger('web_interface', 'web_interface.log')
admin_logger = setup_logger('admin', 'admin.log')
