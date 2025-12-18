import sqlite3
from typing import Generator

from backend.core.config import DB_PATH 


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()