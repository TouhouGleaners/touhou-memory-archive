import os
import asyncio
import aiohttp
import logging

from .config import DB_PATH, MAX_CONCURRENCY, MAX_QUEUE_SIZE
from .delay_manager import DelayManager
from .database import Database, init_db
from .bili_api_client import BiliApiClient
from ..shared.models.video import Video
from .service import VideoService

logger = logging.getLogger(__name__)


async def process_video_worker(
    queue: asyncio.Queue,
    service: VideoService,
    semaphore: asyncio.Semaphore
):
    """消费者 Worker: 从队列中获取视频，并委托给 Service 进行处理。"""
    while True:
        video: Video = await queue.get()
        if video is None:
            break
        try:
            await service.process_video(video, semaphore)
        except Exception as e:
            pass
        finally:
            queue.task_done()


async def main():
    if not os.path.exists(DB_PATH):
        init_db()
        logger.info("数据库初始化完成")
    db = Database()

    try:
        users = db.get_users()
        if not users:
            logger.warning("数据库中没有用户，程序退出。")
            return
    
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        delay_manager = DelayManager.get_instance()

        async with aiohttp.ClientSession() as session:
            bili_client = BiliApiClient(session)
            video_service = VideoService(bili_client, db)

            for user in users:
                logger.info(f"--- 开始处理用户 {user} ---")

                video_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

                # 启动生产者任务，填充队列，在内部更新delay_manager
                producer_task = asyncio.create_task(
                    bili_client.get_user_all_videos(user, video_queue, delay_manager)
                )

                # 启动一组消费者任务
                consumer_tasks = [
                    asyncio.create_task(
                        process_video_worker(video_queue, video_service, semaphore)
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
                    
        logger.info("所有用户处理完毕，程序退出")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    asyncio.run(main())