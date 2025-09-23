import os
import re
import asyncio
import aiohttp
import logging
from tqdm.asyncio import tqdm_asyncio

from config import DB_PATH, MAX_CONCURRENCY
from delay_manager import DelayManager
from database import Database, init_db
from fetcher import fetch_video_list, fetch_parts, fetch_tags
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
        
async def process_video_batch(videos: list[Video], session: aiohttp.ClientSession, db: Database, semaphore: asyncio.Semaphore) -> list[bool]:
    """批量处理视频，先获取所有标签和分P信息，再处理每个视频"""
    if not videos:
        return []
    
    # 并发获取标签和分P信息
    logger.info(f"开始批量获取 {len(videos)} 个视频的信息")
    tags_task = fetch_tags(videos, session)
    parts_task = fetch_parts(videos, session)
    tags_dict, parts_dict = await asyncio.gather(tags_task, parts_task)
    logger.info(f"成功获取 {len(tags_dict)} 个视频的标签和 {len(parts_dict)} 个视频的分P信息")

    # 为每个视频添加标签信息
    pattern = re.compile(r'^\$发现《.+?》\^$')
    for video in videos:
        if video.bvid in tags_dict:
            tags = tags_dict[video.bvid]
            video.tags = [tag for tag in tags if not pattern.match(tag)]
        if video.bvid in parts_dict:
            video.parts = parts_dict[video.bvid]
    
    # 创建视频处理任务
    async def save_video(video: Video) -> bool:
        async with semaphore:
            try:
                # 开始事务
                db.begin_transaction()
                try:
                    # 保存视频基本信息
                    db.save_video_info(video)
                    if hasattr(video, 'parts'):
                        db.save_parts_info(video.aid, video.parts)
                    
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
                logger.error(f"保存视频 {video.bvid} 失败: {str(e)}")
                return False
    
    # 使用进度条并发处理所有任务
    tasks = [save_video(video) for video in videos]
    results = []
    for f in tqdm_asyncio.as_completed(tasks, desc="保存视频信息", total=len(tasks)):
        try:
            result = await f
            results.append(result)
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
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

    delay_manager = DelayManager.get_instance()

    async with aiohttp.ClientSession() as session:
        for user in users:
            logger.info(f"开始处理用户 {user}")
            try:
                vlist = await fetch_video_list(user, session)
                logger.info(f"用户 {user} 共有 {len(vlist)} 个视频")

                # 更新用户视频数量（用于下个用户间的延迟计算）
                delay_manager.update_video_count(len(vlist))

                if not vlist:
                    logger.warning(f"用户 {user} 没有获取到视频，跳过")
                    continue

                # 批量处理所有视频
                results = await process_video_batch(vlist, session, db, semaphore)
                success_count = sum(1 for r in results if r)
                logger.info(f"用户 {user} 处理完成: {success_count}/{len(vlist)} 个视频成功")

                # 用户处理完后，应用用户间延迟
                if user != users[-1]:
                    switch_delay = delay_manager.get_user_switch_delay()
                    logger.info(f"将在 {switch_delay:.1f} 秒后处理下一个用户...")
                    await asyncio.sleep(switch_delay)
            except Exception as e:
                logger.error(f"处理用户 {user} 失败: {str(e)}")
                
    db.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    asyncio.run(main())