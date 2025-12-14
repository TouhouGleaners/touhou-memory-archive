import sqlite3
from typing import Generator

from crawler.config import DB_PATH

def get_db() -> Generator:
    """
    FastAPI 依赖项：获取数据库连接
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()