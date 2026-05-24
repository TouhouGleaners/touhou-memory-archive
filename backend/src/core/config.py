from pathlib import Path

from dotenv import load_dotenv


_BACKEND_DIR = Path(__file__).parent.parent.parent

load_dotenv(_BACKEND_DIR / ".env")

# 数据库路径
DB_PATH = _BACKEND_DIR / "bili_videos.db"
