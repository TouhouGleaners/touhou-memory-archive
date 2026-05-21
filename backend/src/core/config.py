from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent / ".env")

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "bili_videos.db"