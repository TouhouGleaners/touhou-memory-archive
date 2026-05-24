import re
import logging
import asyncio

from crawler.api.models import Page
from crawler.converters import pages_to_parts
from crawler.core.database import save_video
from crawler.core.video_fetcher import BiliClient
from shared.schemas import VideoSchema


logger = logging.getLogger(__name__)


class VideoService:
    """封装所有视频处理相关的业务逻辑"""
    def __init__(self, client: BiliClient):
        self.client = client
        self.session = session
        self.tag_pattern = re.compile(r'^\$发现《.+?》\^$')
        self.touhou_keywords = {
            "东方Project", "东方project", "东方PROJECT",
            "東方Project", "東方project", "東方PROJECT",
            "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
        }

    def _is_touhou(self, tags: list[str]) -> int:
        """自动检测是否为东方视频 是:1 否:2"""
        return 1 if any(keyword in tag for tag in tags for keyword in self.touhou_keywords) else 2

    async def process_video(self, video: VideoSchema, semaphore: asyncio.Semaphore):
        """处理单个视频的完整业务流程"""
        try:
            async with semaphore:
                tags_task = self.client.get_video_tags(video.bvid)
            async with semaphore:
                info_task = self.client.get_video_info(video.bvid)

            results = await asyncio.gather(tags_task, info_task, return_exceptions=True)

            video_tags_result = []
            if not isinstance(results[0], Exception):
                video_tags_result = results[0]
            else:
                logger.warning(f"获取视频 {video.bvid} 的标签失败: {results[0]}")

            if not isinstance(results[1], Exception):
                view_info = results[1]
                if 'desc' in view_info:
                    video.description = view_info['desc']

                if 'pages' in view_info:
                    try:
                        pages = [Page.model_validate(p) for p in view_info['pages']]
                        video.parts = pages_to_parts(pages)
                    except Exception as e:
                         logger.warning(f"解析视频 {video.bvid} 分P模型失败: {e}")
                         video.parts = []
            else:
                logger.warning(f"获取视频 {video.bvid} 的分P信息失败: {results[1]}")

            video.tags = [tag for tag in video_tags_result if not self.tag_pattern.match(tag)]
            video.touhou_status = self._is_touhou(video.tags)

            save_video(video)

            logger.info(f"视频 {video.bvid} 处理并保存成功。")

        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 的业务逻辑时失败: {str(e)}")
            raise
