import asyncio
import logging
from typing import AsyncGenerator

from crawler.api.bili_api import BiliAPI
from crawler.api.models import SpaceVideoItem, SeasonArchiveItem, Page
from crawler.config import PRODUCER_PAGE_DELAY_SECONDS
from crawler.converters import space_item_to_video, season_item_to_video, page_to_part
from crawler.models import Video, VideoPart

from .delay_manager import DelayManager


logger = logging.getLogger(__name__)


class BiliClient:
    def __init__(self, api: BiliAPI):
        self.api = api

    async def get_user_all_videos(
        self,
        mid: int,
        delay_manager: DelayManager,
        page_size: int = 50
    ) -> AsyncGenerator[Video, None]:
        """
        业务逻辑：循环分页获取用户所有视频，并自动展开合集
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

    async def _fetch_season(self, mid: int, season_id: int, delay_manager: DelayManager) -> AsyncGenerator[Video, None]:
        """内部递归：获取合集"""
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

    async def get_video_info(self, bvid: str) -> dict:
        return await self.api.get_video_detail(bvid)

    async def get_video_parts(self, bvid: str) -> list[VideoPart]:
        data = await self.api.get_video_parts(bvid)
        if isinstance(data, list):
            return [page_to_part(Page.model_validate(p)) for p in data]
        return []

    async def get_video_tags(self, bvid: str) -> list[str]:
        data = await self.api.get_video_tags(bvid)
        if isinstance(data, list):
            return [t.get('tag_name') for t in data if 'tag_name' in t]
        return []
