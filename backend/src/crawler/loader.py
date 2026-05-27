"""写入阶段：将 VideoSchema 存入数据库。"""

import logging

from crawler.database import save_video
from domain.schemas import VideoSchema

logger = logging.getLogger(__name__)


def load(video: VideoSchema) -> None:
    """保存视频到数据库。"""
    save_video(video)
    logger.info(f"视频 {video.bvid} 保存成功。")
