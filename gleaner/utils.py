import re
import requests
import pandas as pd
from .config import HEADERS, URL_PATTERNS


def sanitize_filename(name: str) -> str:
    """
    清洗文件名，去除 Windows 非法字符，并限制长度
    """
    if not name:
        return "Untitled"
    
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', str(name))  # 替换非法字符(< > : " / \ | ? *)为下划线
    cleaned = cleaned.strip()  # 去除首尾空格

    if not cleaned:  # 防止清洗后变为空字符串
        return "Untitled"
    
    if len(cleaned) > 100:  # 限制长度
        cleaned = cleaned[:100] + "..."
        
    return cleaned

def extract_origin_id(text: str) -> tuple[str, str] | None:
    """从简介文本中提取原视频 (平台, ID)"""
    if not text or not isinstance(text, str):
        return None
    
    matches = []
    for platform, pattern in URL_PATTERNS:
        for m in pattern.finditer(text):
            matches.append({
                'pos': m.start(),
                'platform': platform,
                'id': m.group(1)
            })

    if not matches:
        return None
    
    # 优先取在文本中出现位置靠前的链接
    first_match = sorted(matches, key=lambda x: x['pos'])[0]
    return (first_match['platform'], first_match['id'])

def check_bilibili_alive(bvid: str, session: requests.Session = None) -> bool:
    """
    检测 B站 视频是否存活
    Returns: True(存活/网络错误), False(明确失效)
    """
    if pd.isna(bvid) or not bvid:
        return False
    
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    
    try:
        requester = session if session else requests
        resp = requester.get(api_url, headers=HEADERS, timeout=5)
        
        if resp.status_code != 200:
            print(f"  [API警告] HTTP {resp.status_code}")
            return True # 保守策略：网络错误视为存活
            
        data = resp.json()
        if data['code'] == 0:
            return True
            
        return False
    except Exception as e:
        print(f"  [网络波动] {e}")
        return True