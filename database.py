import sqlite3

from config import DB_PATH, INIT_SQL_PATH
from video import Video, VideoPart


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
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def get_users(self) -> list[int]:
        self.cursor.execute("SELECT mid FROM users")
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def save_video_info(self, video: Video):
        sql = """
        INSERT OR REPLACE INTO 
        videos (aid, bvid, mid, title, description, pic, created, touhou_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (video.aid, video.bvid, video.mid, video.title, video.description, 
                  video.pic, video.created, video.touhou_status)
        self.cursor.execute(sql, params)
        self.conn.commit()

    def save_parts_info(self, aid: int, video_parts: list[VideoPart]):
        sql = """
        INSERT OR REPLACE INTO 
        video_parts (cid, aid, page, part, duration, ctime)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        for part in video_parts:
            params = (part.cid, aid, part.page, part.part, part.duration, part.ctime)
            self.cursor.execute(sql, params)

        self.conn.commit()
    
    def save_video_tags(self, aid: int, tags: list[str]):
        tags_str = ','.join(tags)
        sql = "UPDATE videos SET tags = ? WHERE aid = ?"
        params = (tags_str, aid)
        self.cursor.execute(sql, params)
        self.conn.commit()

    def update_video_status(self, aid: int, touhou_status: int):
        sql = "UPDATE videos SET touhou_status = ? WHERE aid = ?"
        self.cursor.execute(sql, (touhou_status, aid))
        self.conn.commit()
    
    def get_users_with_names(self) -> list[tuple]:
        self.cursor.execute("SELECT mid, name FROM users")
        return self.cursor.fetchall()
    
    def add_user(self, mid: int, name: str):
        self.cursor.execute("SELECT 1 FROM users WHERE mid = ?", (mid,))
        if self.cursor.fetchone():
            raise ValueError("用户已存在")
        
        self.cursor.execute("INSERT INTO users (mid, name) VALUES (?, ?)", (mid, name))
        self.conn.commit()

    def delete_user(self, mid: int):
        self.cursor.execute("DELETE FROM users WHERE mid = ?",(mid,))
        if self.cursor.rowcount == 0:
            raise ValueError("用户不存在")
        self.conn.commit()
