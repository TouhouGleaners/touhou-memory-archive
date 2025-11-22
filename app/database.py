import sqlite3
from crawler.config import DB_PATH

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_all_videos(db: sqlite3.Connection) -> list[sqlite3.Row]:
    """获取所有视频信息"""
    cursor = db.execute("SELECT * FROM videos ORDER BY created DESC")
    videos = cursor.fetchall()
    return videos if videos else []

def get_video_parts(db: sqlite3.Connection, aid: int) -> list[sqlite3.Row]:
    """根据 aid 获取视频所有分P"""
    cursor = db.execute("SELECT * FROM video_parts WHERE aid = ?", (aid,))
    parts = cursor.fetchall()
    return parts if parts else []

def get_user_by_mid(db: sqlite3.Connection, mid: int) -> sqlite3.Row | None:
    """根据 mid 获取单个 UP 主信息"""
    cursor = db.execute("SELECT * FROM users WHERE mid = ?", (mid,))
    user = cursor.fetchone()
    return user

def get_touhou_videos(db: sqlite3.Connection) -> list[sqlite3.Row]:
    """获取所有东方视频信息"""
    cursor = db.execute("SELECT * FROM videos WHERE touhou_status IN (1, 3) ORDER BY created DESC")
    videos = cursor.fetchall()
    return videos if videos else []