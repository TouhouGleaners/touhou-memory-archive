from dataclasses import dataclass

from crawler.api.models import VideoTag
from domain.schemas import VideoSchema


@dataclass
class PartialVideo:
    """提取阶段的输出：从空间搜索/合集列表拿到的最少信息"""
    aid: int
    bvid: str
    mid: int
    season_id: int | None


@dataclass
class EnrichedVideo:
    """补全阶段的输出：完整数据 + 未处理的原始标签"""
    video: VideoSchema
    raw_tags: list[VideoTag]
