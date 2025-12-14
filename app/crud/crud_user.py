import sqlite3


def get_user_by_mid(db: sqlite3.Connection, mid: int):
    cursor = db.execute("SELECT * FROM users WHERE mid = ?", (mid,))
    user = cursor.fetchone()
    return dict(user) if user else None