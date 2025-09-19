import json
import sqlite3
import pytz
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


DB_PATH = Path(__file__).parent.parent / "bili_videos.db"
DATA_REPO_DIR = Path(__file__).parent.parent.parent / "touhou-memory-archive-data"


def export_to_data_repo():
    repo_path = Path(DATA_REPO_DIR)
    repo_path.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        videos = get_all_videos(conn)
        shanghai_now = datetime.now(pytz.timezone("Asia/Shanghai"))
        
        docs_data_dir = repo_path / "docs" / "data"
        docs_data_dir.mkdir(exist_ok=True)
        docs_data_file = docs_data_dir / "videos.json"
        save_json(videos, docs_data_file)
        
        archive_dir = repo_path / "archives" / shanghai_now.strftime("%Y-%m")
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archive_dir / f"videos_{shanghai_now.strftime('%Y%m%d')}.json"
        save_json(videos, archive_file)
        
        print(f"导出成功！共导出 {len(videos)} 个视频")
        print(f"最新数据: {docs_data_file.resolve()}")
        print(f"归档数据: {archive_file.resolve()}")
        return True
    finally:
        conn.close()

def get_all_videos(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """获取所有视频数据，包括分P信息"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            v.aid, v.bvid, v.mid, v.title, v.description, 
            v.pic, v.created, v.tags, v.touhou_status,
            u.name AS uploader_name
        FROM videos v
        LEFT JOIN users u ON v.mid = u.mid
        ORDER BY v.created DESC
    """)
    
    videos = []
    for row in cursor.fetchall():
        video = dict(row)
        video["tags"] = video["tags"].split(',') if video["tags"] else []  # 处理标签
        video["parts"] = get_video_parts(conn, video["aid"])  # 添加分P信息
        if "mid" in video:
            del video["mid"]  # 精简不需要的mid
        videos.append(video)
    return videos

def get_video_parts(conn: sqlite3.Connection, aid: int) -> List[Dict[str, Any]]:
    """获取视频的分P信息 - 仅包含基本字段"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cid, page, part, duration, ctime 
        FROM video_parts 
        WHERE aid = ? 
        ORDER BY page
    """, (aid,))
    
    return [dict(row) for row in cursor.fetchall()]

def save_json(data: List[Dict], file_path: Path):
    """保存数据到JSON文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    export_to_data_repo()
