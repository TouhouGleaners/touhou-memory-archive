import os
import re
import asyncio
import aiohttp
import logging
from tqdm.asyncio import tqdm_asyncio

from config import DB_PATH, DELAY_SECONDS, MAX_CONCURRENCY
from database import Database, init_db
from fetcher import fetch_video_list, fetch_video_parts, fetch_video_tags

logger = logging.getLogger(__name__)


def is_touhou(tags: list[str]) -> int:
    """自动检测是否为东方视频 是:1 否:2"""
    touhou_keywords = {
        "东方Project", "东方project", "东方PROJECT",
        "東方Project", "東方project", "東方PROJECT",
        "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
    }
    return 1 if any(keyword in tag for tag in tags for keyword in touhou_keywords) else 2

async def process_video(video, session, db, semaphore):
    """处理单个视频"""
    async with semaphore:
        try:
            # 保存视频基本信息
            db.save_video_info(video)

            # 保存分P信息
            parts = await fetch_video_parts(video.bvid, session)
            db.save_parts_info(video.aid, parts)

            # 过滤并保存标签信息
            tags = await fetch_video_tags(video.bvid, session)
            pattern = re.compile(r'^\$发现《.+?》\^$')
            filtered_tags = [tag for tag in tags if not pattern.match(tag)]
            video.tags = filtered_tags
            db.save_video_tags(video.aid, video.tags)

            # 检测视频内容并更新状态
            touhou_status = is_touhou(filtered_tags)
            video.touhou_status = touhou_status
            db.update_video_status(video.aid, touhou_status)

            return True
        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 失败: {str(e)}")
            return False
        
async def main():
    if not os.path.exists(DB_PATH):
        init_db()
        logger.info("数据库初始化完成")

    db = Database()
    users = db.get_users()
    logger.info(f"获取到 {len(users)} 个用户: {users}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        for user in users:
            logger.info(f"开始处理用户 {user}")
            try:
                vlist = await fetch_video_list(user, session)
                logger.info(f"用户 {user} 共有 {len(vlist)} 个视频")

                if not vlist:
                    logger.warning(f"用户 {user} 没有获取到视频，跳过")
                    continue

                tasks = [process_video(video, session, db, semaphore) for video in vlist]

                # 使用异步进度条处理所有任务
                results = []
                for f in tqdm_asyncio.as_completed(tasks, desc=f"处理用户 {user} 的视频", total=len(tasks)):
                    result = await f
                    results.append(result)
                
                success_count = sum(results)
                logger.info(f"用户 {user} 处理完成: {success_count}/{len(vlist)} 个视频成功")
            except Exception as e:
                logger.error(f"处理用户 {user} 失败: {str(e)}")
                
    db.close()

if __name__ == "__main__":
    asyncio.run(main())