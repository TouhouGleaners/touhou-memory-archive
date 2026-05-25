import asyncio
import logging

import aiohttp

from domain.database import init_db
from domain.schemas import VideoSchema

from crawler.api.bili_api import BiliAPI
from crawler.discovery import VideoDiscovery
from .config import MAX_CONCURRENCY, MAX_QUEUE_SIZE
from crawler.database import get_all_user_mids
from crawler.rate_limit import DelayManager
from crawler.processor import VideoService


logger = logging.getLogger(__name__)


async def process_video_worker(
    queue: asyncio.Queue,
    service: VideoService,
    semaphore: asyncio.Semaphore
):
    """消费者 Worker: 从队列中获取视频，并委托给 Service 进行处理。"""
    while True:
        video: VideoSchema = await queue.get()
        if video is None:
            break
        try:
            await service.process_video(video, semaphore)
        except Exception as e:
            pass
        finally:
            queue.task_done()


async def main():
    init_db()
    logger.info("数据库初始化完成")

    users = get_all_user_mids()
    if not users:
        logger.warning("数据库中没有用户，程序退出。")
        return

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    delay_manager = DelayManager.get_instance()

    async with aiohttp.ClientSession() as http_session:
        bili_api = BiliAPI(http_session)
        video_discovery = VideoDiscovery(bili_api)
        video_service = VideoService(bili_api)

        for user in users:
            logger.info(f"--- 开始处理用户 {user} ---")

            video_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

            async def run_producer():
                try:
                    async for video in video_discovery.get_user_all_videos(user, delay_manager):
                        await video_queue.put(video)
                except asyncio.CancelledError:
                    logger.info(f"用户 {user} 生产任务被取消")
                    raise
                except Exception as e:
                    logger.critical(f"用户 {user} 任务中断: {e}")

            p_task = asyncio.create_task(run_producer())

            consumer_tasks = [
                asyncio.create_task(
                    process_video_worker(video_queue, video_service, semaphore)
                )
                for _ in range(MAX_CONCURRENCY)
            ]

            await p_task
            await video_queue.join()

            for _ in range(MAX_CONCURRENCY):
                await video_queue.put(None)

            await asyncio.gather(*consumer_tasks)
            logger.info(f"--- 用户 {user} 处理完成 ---")

            if user != users[-1]:
                switch_delay = delay_manager.get_user_switch_delay()
                logger.info(f"将在 {switch_delay:.2f} 秒后处理下一个用户...")
                await asyncio.sleep(switch_delay)

    logger.info("所有用户处理完毕，程序退出")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s][%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )
    asyncio.run(main())
