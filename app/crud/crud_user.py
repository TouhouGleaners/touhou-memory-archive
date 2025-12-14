import sqlite3
from typing import Any


def get_user_by_mid(db: sqlite3.Connection, mid: int) -> dict[str, Any] | None:
    cursor = db.execute("SELECT * FROM users WHERE mid = ?", (mid,))
    user = cursor.fetchone()
    return dict(user) if user else None