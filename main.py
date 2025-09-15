import os
import re
import asyncio
import aiohttp
import logging
from tqdm.asyncio import tqdm_asyncio

from config import DB_PATH, DELAY_SECONDS, MAX_CONCURRENCY
from database import Database, init_db
from fetcher import fetch_video_list, fetch_video_parts, fetch_video_tags, fetch_video_tags_batch
from video import Video

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
            # 并行获取分P信息和标签信息
            parts_task = fetch_video_parts(video.bvid, session)
            parts = await parts_task

            # 开始事务
            db.begin_transaction()
            try:
                # 一次性保存所有视频信息
                db.save_video_info(video)
                db.save_parts_info(video.aid, parts)
                
                # 检测视频内容并更新状态
                touhou_status = is_touhou(video.tags)
                video.touhou_status = touhou_status
                db.save_video_tags(video.aid, video.tags)
                db.update_video_status(video.aid, touhou_status)

                # 提交事务
                db.commit_transaction()
                return True
            except Exception as e:
                # 发生错误时回滚事务
                db.rollback_transaction()
                raise e
        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 失败: {str(e)}")
            return False
        
async def process_video_batch(videos: list[Video], session: aiohttp.ClientSession, db: Database, semaphore: asyncio.Semaphore) -> list[bool]:
    """批量处理视频，先获取所有标签，再并发处理每个视频"""
    if not videos:
        return []
    
    # 先批量获取所有视频的标签
    logger.info(f"开始批量获取 {len(videos)} 个视频的标签")
    tags_dict = await fetch_video_tags_batch(videos, session)
    logger.info(f"成功获取 {len(tags_dict)} 个视频的标签")

    # 为每个视频添加标签信息
    pattern = re.compile(r'^\$发现《.+?》\^$')
    for video in videos:
        if video.bvid in tags_dict:
            tags = tags_dict[video.bvid]
            video.tags = [tag for tag in tags if not pattern.match(tag)]
    
    # 创建视频处理任务
    tasks = [process_video(video, session, db, semaphore) for video in videos]
    
    # 使用进度条并发处理所有任务
    results = []
    for f in tqdm_asyncio.as_completed(tasks, desc="处理视频", total=len(tasks)):
        try:
            result = await f
            results.append(result)
        except Exception as e:
            logger.error(f"处理视频失败: {str(e)}")
            results.append(False)
    
    return results

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

                # 批量处理所有视频
                results = await process_video_batch(vlist, session, db, semaphore)
                success_count = sum(1 for r in results if r)
                logger.info(f"用户 {user} 处理完成: {success_count}/{len(vlist)} 个视频成功")
            except Exception as e:
                logger.error(f"处理用户 {user} 失败: {str(e)}")
                
    db.close()

if __name__ == "__main__":
    asyncio.run(main())