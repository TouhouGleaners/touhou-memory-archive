import sqlite3

from crawler.config import DB_PATH, INIT_SQL_PATH
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
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def get_users(self) -> list[int]:
        self.cursor.execute("SELECT mid FROM users")
        rows = self.cursor.fetchall()
        return [row[0] for row in rows]

    def begin_transaction(self):
        """开始事务"""
        self.cursor.execute("BEGIN")

    def commit_transaction(self):
        """提交事务"""
        self.conn.commit()

    def rollback_transaction(self):
        """回滚事务"""
        self.conn.rollback()

    def save_video_info(self, video: Video):
        """保存视频基本信息（不自动提交）"""
        sql = """
        INSERT OR REPLACE INTO 
        videos (aid, bvid, mid, title, description, pic, created, touhou_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (video.aid, video.bvid, video.mid, video.title, video.description, 
                  video.pic, video.created, video.touhou_status)
        self.cursor.execute(sql, params)

    def save_parts_info(self, aid: int, video_parts: list[VideoPart]):
        """保存视频分P信息（不自动提交）"""
        sql = """
        INSERT OR REPLACE INTO 
        video_parts (cid, aid, page, part, duration, ctime)
        VALUES (?, ?, ?, ?, ?, ?)
        """

        for part in video_parts:
            params = (part.cid, aid, part.page, part.part, part.duration, part.ctime)
            self.cursor.execute(sql, params)
    
    def save_video_tags(self, aid: int, tags: list[str]):
        """保存视频标签（不自动提交）"""
        tags_str = ','.join(tags)
        sql = "UPDATE videos SET tags = ? WHERE aid = ?"
        params = (tags_str, aid)
        self.cursor.execute(sql, params)

    def update_video_status(self, aid: int, touhou_status: int):
        """更新视频状态（不自动提交）"""
        sql = "UPDATE videos SET touhou_status = ? WHERE aid = ?"
        self.cursor.execute(sql, (touhou_status, aid))

    @staticmethod
    def get_all_videos_for_api() -> list[dict]:
        """
        为 API 设计的函数：从数据库中获取所有视频信息，
        并将其格式化为前端需要的结构。
        """
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created DESC")
        rows = cursor.fetchall()

        videos_list = []
        if not rows:
            conn.close()
            return []
        for row in rows:
            video_data = dict(row)
            current_aid = video_data['aid']

            parts_cursor = conn.cursor()
            parts_cursor.execute("SELECT * FROM video_parts WHERE aid = ?", (current_aid,))
            parts_rows = parts_cursor.fetchall()
            video_data['parts'] = [dict(p_row) for p_row in parts_rows]
            # 将 tags 字符串按逗号分割为列表
            tags_str = video_data.get('tags')
            if tags_str:
                video_data['tags'] = [tag.strip() for tag in tags_str.split(',')]
            else:
                video_data['tags'] = []

            videos_list.append(video_data)

        conn.close()
        return videos_list

    # TODO: add new user
