import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

SECRET_KEY: str = os.environ["SECRET_KEY"]
