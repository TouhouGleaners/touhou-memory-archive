import asyncio
import logging
from typing import AsyncGenerator

from crawler.api.bili_api import BiliAPI
from crawler.api.models import SpaceVideoItem, SeasonArchiveItem
from crawler.config import PRODUCER_PAGE_DELAY_SECONDS
from crawler.converters import space_item_to_video, season_item_to_video
from domain.schemas import VideoSchema

from .rate_limit import DelayManager


logger = logging.getLogger(__name__)


class VideoDiscovery:
    """负责视频列表发现：用户空间分页、合集展开"""

    def __init__(self, api: BiliAPI):
        self.api = api

    async def get_user_all_videos(
        self,
        mid: int,
        delay_manager: DelayManager,
        page_size: int = 50
    ) -> AsyncGenerator[VideoSchema, None]:
        """
        分页获取用户所有视频，自动展开合集。

        每页之间有 PRODUCER_PAGE_DELAY_SECONDS 的延迟以规避风控。
        第一页会更新 delay_manager 的视频总数，用于后续用户切换延迟计算。
        """
        page = 1
        processed_seasons = set()

        logger.info(f"开始获取用户 {mid} 的视频列表...")

        while True:
            try:
                data = await self.api.get_user_video_list(mid, page, page_size)
            except Exception as e:
                logger.error(f"获取列表失败: {e}")
                break

            vlist = data.get('list', {}).get('vlist', [])
            page_info = data.get('page', {})
            total_videos = page_info.get('count', 0)

            if page == 1:
                delay_manager.update_video_count(total_videos)

            if not vlist:
                break

            for v_data in vlist:
                try:
                    item = SpaceVideoItem.model_validate(v_data)
                    video = space_item_to_video(item)
                except Exception:
                    continue

                if video.season_id and video.season_id not in processed_seasons:
                    processed_seasons.add(video.season_id)

                    async for sv in self._fetch_season(mid, video.season_id, delay_manager):
                        yield sv
                elif not video.season_id:
                    yield video

            if page * page_size >= total_videos:
                break

            page += 1
            await asyncio.sleep(PRODUCER_PAGE_DELAY_SECONDS)

    async def _fetch_season(self, mid: int, season_id: int, delay_manager: DelayManager) -> AsyncGenerator[VideoSchema, None]:
        """获取合集内所有视频，分页处理"""
        page = 1

        while True:
            try:
                data = await self.api.get_season_video_list(mid, season_id, page, 50)
            except Exception:
                break

            archives = data.get('archives', [])
            if not archives:
                break

            for arc in archives:
                try:
                    item = SeasonArchiveItem.model_validate(arc)
                    yield season_item_to_video(item, mid, season_id)
                except Exception:
                    continue

            if len(archives) < 50:
                break

            page += 1
            sleep_time = delay_manager.get_request_delay()
            await asyncio.sleep(sleep_time)
