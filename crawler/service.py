import re
import logging
import asyncio
import aiohttp

from .database import Database
from .fetcher import fetch_tags, fetch_parts
from .video import Video

logger = logging.getLogger(__name__)


class VideoService:
    """
    封装所有视频处理相关的业务逻辑。
    这是一个无状态的服务，其依赖项在创建时被注入。
    """
    def __init__(self, session: aiohttp.ClientSession, db: Database):
        self.session = session
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
            # 并发获取tags和分P信息
            tags_task = fetch_tags([video], self.session, semaphore)
            parts_task = fetch_parts([video], self.session, semaphore)
            tags_dict, parts_dict = await asyncio.gather(tags_task, parts_task)

            # 丰富 Video 对象
            video_tags = tags_dict.get(video.bvid, [])
            video.tags = [tag for tag in video_tags if not self.tag_pattern.match(tag)]
            video.parts = parts_dict.get(video.bvid, [])
            video.touhou_status = self._is_touhou(video.tags)

            # 保存信息
            with self.db.transaction():
                self.db.save_video_info(video)

            logger.info(f"视频 {video.bvid} 处理并保存成功。")

        except Exception as e:
            logger.error(f"处理视频 {video.bvid} 的业务逻辑时失败: {str(e)}")
            raise