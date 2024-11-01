import sqlite3
import logging
from threading import local
from config import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.local = local()

    def get_db(self):
        if not hasattr(self.local, 'db'):
            self.local.db = Database()
        return self.local.db

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                number TEXT,
                title TEXT,
                author TEXT,
                date TEXT,
                views INTEGER,
                votes INTEGER,
                content TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS crawling_progress (
                id INTEGER PRIMARY KEY,
                current_page INTEGER,
                total_pages INTEGER,
                total_processed INTEGER
            )
        ''')


        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY,
                post_id INTEGER,
                author TEXT,
                content TEXT,
                date TEXT,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                post_id INTEGER,
                file_path TEXT,
                md5_hash TEXT UNIQUE,
                FOREIGN KEY (post_id) REFERENCES posts (id)
            )
        ''')

        self.conn.commit()

    def insert_post(self, post_data):
        try:
            self.cursor.execute('''
                INSERT INTO posts (number, title, author, date, views, votes, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (post_data['number'], post_data['title'], post_data['author'],
                post_data['date'], post_data['views'], post_data['votes'],
                post_data['content']))
            self.conn.commit()
            return self.cursor.lastrowid  # 삽입된 행의 ID 반환
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (게시물 삽입): {e}")
            return None

    def insert_comment(self, post_id, comment_data):
        try:
            self.cursor.execute('''
                INSERT INTO comments (post_id, author, content, date)
                VALUES (?, ?, ?, ?)
                ''', (post_id, comment_data['author'], comment_data['content'], comment_data['date']))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (댓글 삽입): {e}")
            return None


    def get_post_by_number(self, number):
        try:
            self.cursor.execute("SELECT * FROM posts WHERE number = ?", (number,))
            result = self.cursor.fetchone()
            if result:
                return dict(zip([column[0] for column in self.cursor.description], result))
            return None
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (게시물 번호로 조회): {e}")
            return None


    def insert_image(self, post_id, file_path, md5_hash):
        try:
            filename = os.path.basename(file_path)
            self.cursor.execute('''
                INSERT INTO images (post_id, file_path, md5_hash)
                VALUES (?, ?, ?)
            ''', (post_id, filename, md5_hash))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.warning(f"이미지 삽입 중 무결성 오류 발생: {e}. 이미 존재하는 이미지일 수 있습니다.")
            return None
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"데이터베이스 오류 (이미지 삽입): {e}")
            return None


    def get_posts_with_details(self, page, per_page):
        offset = (page - 1) * per_page
        self.cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT p.*, COUNT(c.id) as comment_count,
            (SELECT GROUP_CONCAT(file_path, '|') FROM images WHERE post_id = p.id) as image_paths
            FROM posts p
            LEFT JOIN comments c ON p.id = c.post_id
            GROUP BY p.id
            ORDER BY p.date DESC LIMIT ? OFFSET ?
        """, (per_page, offset))
        posts = [dict(row) for row in self.cursor.fetchall()]
        return posts, total_posts



    def get_recent_posts(self, limit):
        self.cursor.execute("SELECT * FROM posts ORDER BY date DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_post(self, post_id):
        try:
            self.cursor.execute("""
                SELECT p.*, COUNT(c.id) as comment_count,
                (SELECT GROUP_CONCAT(file_path, '|') FROM images WHERE post_id = p.id) as image_paths
                FROM posts p
                LEFT JOIN comments c ON p.id = c.post_id
                WHERE p.id = ?
                GROUP BY p.id
            """, (post_id,))
            result = self.cursor.fetchone()
            if result:
                return dict(result)
            return None
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (게시물 조회): {e}")
            return None

    def get_posts(self, page=1, per_page=20):
        try:
            offset = (page - 1) * per_page
            self.cursor.execute("""
                SELECT p.*, COUNT(c.id) as comment_count
                FROM posts p
                LEFT JOIN comments c ON p.id = c.post_id
                GROUP BY p.id
                ORDER BY p.date DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            columns = [column[0] for column in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (게시물 목록 조회): {e}")
            return []

    def get_total_posts(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM posts")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (총 게시물 수 조회): {e}")
            return 0

    def get_comment_count(self, post_id):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (댓글 수 조회): {e}")
            return 0

    def get_comments(self, post_id):
        try:
            self.cursor.execute("SELECT * FROM comments WHERE post_id = ?", (post_id,))
            columns = [column[0] for column in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (댓글 조회): {e}")
            return None


    def get_images(self, post_id):
        try:
            self.cursor.execute("SELECT * FROM images WHERE post_id = ?", (post_id,))
            columns = [column[0] for column in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (이미지 조회): {e}")
            return None
    
    def close(self):
        self.conn.close()

    def update_post(self, post_id, post_data):
        try:
            self.cursor.execute('''
                UPDATE posts 
                SET title = ?, author = ?, date = ?, views = ?, votes = ?, content = ?
                WHERE id = ?
            ''', (post_data['title'], post_data['author'], post_data['date'],
                  post_data['views'], post_data['votes'], post_data['content'], post_id))
            self.conn.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (게시물 업데이트): {e}")
            return 0

    def update_crawling_progress(self, current_page, total_pages, total_processed):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO crawling_progress (id, current_page, total_pages, total_processed)
                VALUES (1, ?, ?, ?)
            ''', (current_page, total_pages, total_processed))
            self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (크롤링 진행도 업데이트): {e}")

    def get_crawling_progress(self):
        try:
            self.cursor.execute("SELECT * FROM crawling_progress WHERE id = 1")
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (크롤링 진행도 조회): {e}")
            return None
            
    def get_total_comments(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM comments")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (총 댓글 수 조회): {e}")
            return 0
            
            
    def get_last_crawled_time(self):
        try:
            self.cursor.execute("SELECT MAX(date) FROM posts")
            result = self.cursor.fetchone()[0]
            return result if result else "N/A"
        except sqlite3.Error as e:
            logger.error(f"데이터베이스 오류 (마지막 크롤링 시간 조회): {e}")
            return "N/A"



# 데이터베이스 매니저 인스턴스 생성
db_manager = DatabaseManager()

# 데이터베이스 접근을 위한 함수
def get_db():
    return db_manager.get_db()
