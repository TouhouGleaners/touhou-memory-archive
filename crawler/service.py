import re
import logging
import asyncio

from .database import Database
from .bili_api_client import BiliApiClient
from .video import Video

logger = logging.getLogger(__name__)


class VideoService:
    """封装所有视频处理相关的业务逻辑"""
    def __init__(self, client: BiliApiClient, db: Database):
        self.client = client
        self.db = db
        self.tag_pattern = re.compile(r'^\$发现《.+?》\^$')
        self.touhou_keywords = {
            "东方Project", "东方project", "东方PROJECT",
            "東方Project", "東方project", "東方PROJECT",
            "Touhou", "東方", "车万", "ZUN", "Zun", "zun"
        }

    def _is_touhou(self, tags: list[str]) -> int:
        """自动检测是否为东方视频 是:1 否:2"""
        return 1 if any(keyword in tag for tag in tags for keyword in self.touhou_keywords) else 2

    async def process_video(self, video: Video, semaphore: asyncio.Semaphore):
        """处理单个视频的完整业务流程"""
        try:
            async with semaphore:
                tags_task = self.client.get_video_tags(video.bvid)
            async with semaphore:
                parts_task = self.client.get_video_parts(video.bvid)

            video_tags, video_parts = await asyncio.gather(tags_task, parts_task)

            # 丰富 Video 对象
            video_tags = [tag for tag in video_tags if not self.tag_pattern.match(tag)]
            video.parts = video_parts
            video.touhou_status = self._is_touhou(video.tags)

            # 保存信息
            with self.db.transaction():
                self.db.save_video_info(video)

            logger.info(f"视频 {video.bvid} 处理并保存成功。")

        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 的业务逻辑时失败: {str(e)}")
            raise