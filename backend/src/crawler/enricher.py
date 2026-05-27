"""补全阶段：并发获取视频详情和标签，产出 EnrichedVideo。"""

import asyncio
import logging

from crawler.api.bili_api import BiliAPI
from crawler.api.models import VideoDetailData, VideoTag, Page
from crawler.models import PartialVideo, EnrichedVideo
from domain.schemas import VideoSchema, VideoPartSchema

logger = logging.getLogger(__name__)


class Enricher:
    def __init__(self, api: BiliAPI):
        self.api = api

    async def _fetch_detail(self, bvid: str) -> VideoDetailData:
        """获取视频详情，失败时抛异常"""
        raw = await self.api.get_video_detail(bvid)
        return VideoDetailData.model_validate(raw)

    async def _fetch_tags(self, bvid: str) -> list[VideoTag]:
        """获取视频标签，逐条容错"""
        data = await self.api.get_video_tags(bvid)
        if not isinstance(data, list):
            return []
        tags = []
        for t in data:
            try:
                tags.append(VideoTag.model_validate(t))
            except ValueError:
                logger.warning(f"跳过格式异常的标签: {t}")
        return tags

    async def enrich(
        self,
        partial: PartialVideo,
        semaphore: asyncio.Semaphore,
    ) -> EnrichedVideo:
        """并发获取 detail + tags，拼装为 EnrichedVideo。"""
        async with semaphore:
            raw_tags, detail = await asyncio.gather(
                self._fetch_tags(partial.bvid),
                self._fetch_detail(partial.bvid),
            )

        # 用 detail 构建 VideoSchema（字段映射）
        video = VideoSchema(
            aid=detail.aid,
            bvid=detail.bvid,
            mid=partial.mid,
            uploader_name=detail.owner.name,
            title=detail.title,
            description=detail.desc,
            cover_url=detail.pic,
            published_at=detail.pubdate,
            created_at=detail.ctime,
            duration=detail.duration,
            category_id=detail.tid,
            category_name=detail.tname,
            copyright=detail.copyright,
            state=detail.state,
            season_id=partial.season_id,
            view_count=detail.stat.view,
            danmaku_count=detail.stat.danmaku,
            reply_count=detail.stat.reply,
            favorite_count=detail.stat.favorite,
            coin_count=detail.stat.coin,
            share_count=detail.stat.share,
            like_count=detail.stat.like,
            parts=[
                VideoPartSchema(
                    cid=p.cid,
                    index=p.page,
                    title=p.part,
                    duration=p.duration,
                )
                for p in detail.pages
            ],
        )

        return EnrichedVideo(video=video, raw_tags=raw_tags)
