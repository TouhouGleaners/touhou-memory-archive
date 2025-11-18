import sqlite3
from contextlib import contextmanager

from .config import DB_PATH, INIT_SQL_PATH
from .video import Video, VideoPart


def init_db(db_path: str = DB_PATH, init_sql_path: str = INIT_SQL_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(init_sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def get_users(self) -> list[int]:
        self.cursor.execute("SELECT mid FROM users")
        rows = self.cursor.fetchall()
        return [row['mid'] for row in rows]

    @contextmanager
    def transaction(self):
        """提供一个安全的事务上下文管理器"""
        try:
            self.cursor.execute("BEGIN")
            yield
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def save_video_info(self, video: Video):
        """保存视频信息"""
        video_sql = """
        INSERT OR REPLACE INTO 
        videos (aid, bvid, mid, title, description, pic, created, tags, touhou_status, season_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        tags_str = ','.join(video.tags)
        video_params = (
            video.aid, video.bvid, video.mid, video.title, video.description, 
            video.pic, video.created, tags_str, video.touhou_status, video.season_id
        )
        self.cursor.execute(video_sql, video_params)
        
        if video.parts:
            parts_sql = """
            INSERT OR REPLACE INTO 
            video_parts (cid, aid, page, part, duration, ctime)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            parts_params = [
                (part.cid, video.aid, part.page, part.part, part.duration, part.ctime)
                for part in video.parts
            ]
            self.cursor.executemany(parts_sql, parts_params)

    # TODO: add new user
