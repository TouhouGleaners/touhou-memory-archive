"""提取阶段：从 B 站 API 获取视频列表，产出 PartialVideo。"""

import logging
from typing import AsyncGenerator

from crawler.api.models import SpaceVideoItem
from crawler.discovery import VideoDiscovery
from crawler.models import PartialVideo
from crawler.rate_limit import DelayManager

logger = logging.getLogger(__name__)


class Extractor:
    def __init__(self, discovery: VideoDiscovery):
        self.discovery = discovery

    async def extract_user_videos(
        self,
        mid: int,
        delay_manager: DelayManager,
    ) -> AsyncGenerator[PartialVideo, None]:
        """获取用户所有视频，yield 最少信息的 PartialVideo。"""
        async for video_schema in self.discovery.get_user_all_videos(mid, delay_manager):
            yield PartialVideo(
                aid=video_schema.aid,
                bvid=video_schema.bvid,
                mid=video_schema.mid,
                season_id=video_schema.season_id,
            )
