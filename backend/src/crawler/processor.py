import logging
import asyncio

from crawler.api.bili_api import BiliAPI
from crawler.api.models import VideoTag, VideoDetailData
from crawler.converters import enrich_video_from_detail
from crawler.database import save_video
from domain.schemas import VideoSchema


logger = logging.getLogger(__name__)


class VideoService:
    """负责单个视频的处理：数据获取、业务逻辑、持久化"""

    TOUHOU_KEYWORDS = {
        "东方Project", "东方project", "东方PROJECT",
        "東方Project", "東方project", "東方PROJECT",
        "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
    }

    def __init__(self, api: BiliAPI):
        self.api = api

    async def _fetch_video_detail(self, bvid: str) -> VideoDetailData:
        """获取视频详情，失败时直接抛异常"""
        raw = await self.api.get_video_detail(bvid)
        return VideoDetailData.model_validate(raw)

    async def _fetch_video_tags(self, bvid: str) -> list[VideoTag]:
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

    @staticmethod
    def _is_touhou(tags: list[str]) -> int:
        """根据标签关键词判断是否为东方视频。是:1 否:2"""
        return 1 if any(kw in tag for tag in tags for kw in VideoService.TOUHOU_KEYWORDS) else 2

    async def process_video(self, video: VideoSchema, semaphore: asyncio.Semaphore):
        """
        处理单个视频的完整业务流程。

        输入的 video 是一个部分填充的 schema（来自空间搜索/合集列表），
        本方法会补充详情、标签、统计数据后保存到数据库。

        流程：
        1. 在 semaphore 限流下并发请求标签接口和详情接口
        2. 用详情数据填充 video 的 description、parts、分类、统计等字段
        3. 用标签数据填充 tags，同时过滤掉 bgm 类型的标签
        4. 根据标签关键词判断 touhou_status
        5. 保存到数据库
        """
        try:
            async with semaphore:
                tags, detail = await asyncio.gather(
                    self._fetch_video_tags(video.bvid),
                    self._fetch_video_detail(video.bvid),
                )

            # 用详情数据补全 video schema（字段映射逻辑在 converters 中）
            enrich_video_from_detail(video, detail, tags)

            # 判断是否为东方视频
            video.touhou_status = self._is_touhou(video.tags)

            save_video(video)

            logger.info(f"视频 {video.bvid} 处理并保存成功。")

        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 的业务逻辑时失败: {str(e)}")
            raise
