import os
import re
from tqdm import tqdm

from config import DB_PATH, DELAY_SECONDS
from database import Database, init_db
from fetcher import fetch_video_list, fetch_video_parts, fetch_video_tags


def is_touhou(tags: list[str]) -> int:
    """自动检测是否为东方视频 是:1 否:2"""
    touhou_keywords = {
        "东方Project", "东方project", "东方PROJECT",
        "東方Project", "東方project", "東方PROJECT",
        "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
    }
    return 1 if any(keyword in tag for tag in tags for keyword in touhou_keywords) else 2


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    
    db = Database()

    users = db.get_users()

    for user in users:
        vlist = fetch_video_list(user)

        for video in tqdm(vlist, desc=f"Processing user {user}"):
            # 保存视频基本信息
            db.save_video_info(video)

            # 保存分P信息
            parts = fetch_video_parts(video.bvid)
            db.save_parts_info(video.aid, parts)

            # 过滤并保存标签信息
            tags = fetch_video_tags(video.bvid)
            pattern = re.compile(r'^\$发现《.+?》\^$')
            filtered_tags = [tag for tag in tags if not pattern.match(tag)]
            video.tags = filtered_tags
            db.save_video_tags(video.aid, video.tags)

            # 检测视频内容并更新状态
            touhou_status = is_touhou(filtered_tags)
            video.touhou_status = touhou_status
            db.update_video_status(video.aid, touhou_status)

    db.close()