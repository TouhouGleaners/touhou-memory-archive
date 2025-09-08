import os
import re
from tqdm import tqdm

from config import DB_PATH, DELAY_SECONDS
from Database import Database, init_db
from fetcher import fetch_video_list, fetch_video_parts, fetch_video_tags


def is_touhou(tags: list[str]) -> bool:
    touhou_tags = {
        "东方Project",
        "东方project",
        "东方",
        "Touhou",
        "東方",
    }
    return any(tag in touhou_tags for tag in tags)


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    
    db = Database()

    users = db.get_users()

    for user in users:
        vlist = fetch_video_list(user)

        for video in tqdm(vlist, desc=f"Processing user {user}"):
            db.save_video_info(video)

            parts = fetch_video_parts(video.bvid)
            db.save_parts_info(video.aid, parts)

            tags = fetch_video_tags(video.bvid)
            
            pattern = re.compile(r'^\$发现《.+?》\^$')
            filtered_tags = list(filter(lambda tag: not pattern.match(tag), tags))
            video.tags = filtered_tags

            db.save_video_tags(video.aid, video.tags)
            # print(f"Video {video.bvid} tags: {tags}")
            # TODO: check is_touhou

    db.close()