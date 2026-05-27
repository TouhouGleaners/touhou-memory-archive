import asyncio
import logging

import aiohttp

from domain.database import init_db

from crawler.api.bili_api import BiliAPI
from crawler.config import MAX_CONCURRENCY, MAX_QUEUE_SIZE
from crawler.discovery import VideoDiscovery
from crawler.enricher import Enricher
from crawler.extractor import Extractor
from crawler.loader import load
from crawler.rate_limit import DelayManager
from crawler.transformer import transform
from crawler.database import get_all_user_mids


logger = logging.getLogger(__name__)


async def process_video_worker(
    queue: asyncio.Queue,
    enricher: Enricher,
    semaphore: asyncio.Semaphore,
):
    """消费者 Worker：从队列取 PartialVideo，走 enrich → transform → load 流程。"""
    while True:
        partial = await queue.get()
        if partial is None:
            break
        try:
            enriched = await enricher.enrich(partial, semaphore)
            video = transform(enriched)
            load(video)
        except Exception as e:
            logger.error(f"处理视频 {partial.bvid} 失败: {e}")
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
        discovery = VideoDiscovery(bili_api)
        extractor = Extractor(discovery)
        enricher = Enricher(bili_api)

        for user in users:
            logger.info(f"--- 开始处理用户 {user} ---")

            video_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)

            async def run_producer():
                try:
                    async for partial in extractor.extract_user_videos(user, delay_manager):
                        await video_queue.put(partial)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.critical(f"用户 {user} 提取阶段中断: {e}")

            p_task = asyncio.create_task(run_producer())

            consumer_tasks = [
                asyncio.create_task(
                    process_video_worker(video_queue, enricher, semaphore)
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
