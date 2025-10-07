import os
import re
import asyncio
import aiohttp
import logging

from .config import DB_PATH, MAX_CONCURRENCY, MAX_QUEUE_SIZE
from .delay_manager import DelayManager
from .database import Database, init_db
from .fetcher import fetch_video_list, fetch_parts, fetch_tags
from .video import Video

logger = logging.getLogger(__name__)


def is_touhou(tags: list[str]) -> int:
    """自动检测是否为东方视频 是:1 否:2"""
    touhou_keywords = {
        "东方Project", "东方project", "东方PROJECT",
        "東方Project", "東方project", "東方PROJECT",
        "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
    }
    return 1 if any(keyword in tag for tag in tags for keyword in touhou_keywords) else 2

async def process_video_worker(
    queue: asyncio.Queue,
    session: aiohttp.ClientSession,
    db: Database,
    semaphore: asyncio.Semaphore
):
    """
    消费者 Worker: 从队列中获取并处理单个视频，直至队列为空并收到结束信号
    """
    while True:
        video: Video = await queue.get()
        if video is None:
            break
        try:
            # 并发获取标签和分P信息
            tags_tasks = fetch_tags([video], session, semaphore)
            parts_tasks = fetch_parts([video], session, semaphore)
            tags_dict, parts_dict = await asyncio.gather(tags_tasks, parts_tasks)

            video_tags = tags_dict.get(video.bvid, [])
            video_parts = parts_dict.get(video.bvid, [])
            pattern = re.compile(r'^\$发现《.+?》\^$')
            video.tags = [tag for tag in video_tags if not pattern.match(tag)]
            video.parts = video_parts

            db.begin_transaction()
            try:
                db.save_video_info(video)
                if video.parts:
                    db.save_parts_info(video.aid, video.parts)
                
                touhou_status = is_touhou(video.tags)
                db.save_video_tags(video.aid, video.tags)
                db.update_video_status(video.aid, touhou_status)
                db.commit_transaction()
            except Exception as e:
                db.rollback_transaction()
                raise e
        except Exception as e:
            logger.error(f"Worker处理视频 {video.bvid} 失败: {str(e)}")
        finally:
            queue.task_done()


async def main():
    if not os.path.exists(DB_PATH):
        init_db()
        logger.info("数据库初始化完成")
    db = Database()

    users = db.get_users()
    if not users:
        logger.warning("数据库中没有用户，程序退出。")
        return
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    delay_manager = DelayManager.get_instance()

    async with aiohttp.ClientSession() as session:
        for user in users:
            logger.info(f"--- 开始处理用户 {user} ---")

            video_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

            # 启动生产者任务，填充队列，在内部更新delay_manager
            producer_task = asyncio.create_task(
                fetch_video_list(user, session, video_queue, delay_manager)
            )

            # 启动一组消费者任务
            consumer_tasks = [
                asyncio.create_task(
                    process_video_worker(video_queue, session, db, semaphore)
                )
                for _ in range(MAX_CONCURRENCY)
            ]

            await producer_task         # 等待生产者完成（所有视频bvid都已放入队列)
            await video_queue.join()    # 生产者完成后，等待队列被消费者完全清空

            # 发送结束信号(None)给所有消费者
            for _ in range(MAX_CONCURRENCY):
                await video_queue.put(None)

            # 等待所有消费者任务都确认退出
            await asyncio.gather(*consumer_tasks)
            logger.info(f"--- 用户 {user} 处理完成 ---")

            # 在处理下一个用户前，应用动态延迟
            if user != users[-1]:
                switch_delay = delay_manager.get_user_switch_delay()
                logger.info(f"将在 {switch_delay:.2f} 秒后处理下一个用户...")
                await asyncio.sleep(switch_delay)
                
    db.close()
    logger.info("所有用户处理完毕，程序退出")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    asyncio.run(main())