import sqlite3
from pathlib import Path
from contextlib import contextmanager

from core.config import DB_PATH
from crawler.config import INIT_SQL_PATH
from crawler.models import Video


def init_db(db_path: Path = DB_PATH, init_sql_path: Path = INIT_SQL_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(init_sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()


class Database:
    def __init__(self, db_path: Path = DB_PATH):
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
        try:
            self.cursor.execute("BEGIN")
            yield
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def save_video_info(self, video: Video):
        sql = """
        INSERT OR REPLACE INTO videos (
            aid, bvid, mid, title, description, cover_url, duration,
            published_at, created_at,
            category_id, category_name, copyright, state,
            view_count, danmaku_count, reply_count, favorite_count,
            coin_count, share_count, like_count,
            tags, touhou_status, season_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        tags_str = ','.join(video.tags)
        params = (
            video.aid, video.bvid, video.mid, video.title, video.description,
            video.cover_url, video.duration,
            video.published_at, video.created_at,
            video.category_id, video.category_name, video.copyright, video.state,
            video.view_count, video.danmaku_count, video.reply_count, video.favorite_count,
            video.coin_count, video.share_count, video.like_count,
            tags_str, video.touhou_status, video.season_id,
        )
        self.cursor.execute(sql, params)

        if video.parts:
            parts_sql = """
            INSERT OR REPLACE INTO video_parts (cid, aid, idx, title, duration)
            VALUES (?, ?, ?, ?, ?)
            """
            parts_params = [
                (part.cid, video.aid, part.index, part.title, part.duration)
                for part in video.parts
            ]
            self.cursor.executemany(parts_sql, parts_params)
