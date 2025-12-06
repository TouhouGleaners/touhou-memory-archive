import re
from pathlib import Path


# --- ffmpeg ---
FFMPEG_PATH = Path(__file__).parent / "ffmpeg.exe"
# --- 网络配置 ---
PROXY_URL = "http://127.0.0.1:7890"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# --- Excel 列索引配置 (根据实际情况修改) ---
COL_IDX_BV = 1    # BV号所在列 (0起始)
COL_IDX_TITLE = 7  # 标题所在列
COL_IDX_DESC = 22 # 简介所在列

# --- 正则表达式预编译 ---
# 格式: (平台名, 正则对象)
URL_PATTERNS = [
    ('youtube', re.compile(r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be|m\.youtube\.com)/(?:shorts/|watch\?v=|v/|embed/|watch\?.+?v=)?([a-zA-Z0-9_-]{11})')),
    ('twitter', re.compile(r'(?:twitter\.com|x\.com)/(?:[a-zA-Z0-9_-]+/status/|i/videos/)(\d+)')),
    ('nico',    re.compile(r'(?:nicovideo\.jp|sp\.nicovideo\.jp|nico\.ms|nico\.jp)/watch/((?:sm|nm|so)\d+)'))
]