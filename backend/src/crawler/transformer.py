"""清洗阶段：纯函数，无副作用。EnrichedVideo → VideoSchema。"""

from crawler.models import EnrichedVideo
from domain.schemas import VideoSchema

# 东方关键词（全小写，匹配时用 in 做子串匹配）
_TOUHOU_KEYWORDS = {
    "东方project", "東方project",
    "touhou", "東方", "车万", "zun",
}


def transform(enriched: EnrichedVideo) -> VideoSchema:
    """清洗 + 业务逻辑，产出最终 VideoSchema。"""
    video = enriched.video

    # 过滤 bgm 标签，只保留 tag_name
    video.tags = [t.tag_name for t in enriched.raw_tags if t.tag_type != "bgm"]

    # 判断是否为东方视频
    video.touhou_status = _is_touhou(video.tags)

    return video


def _is_touhou(tags: list[str]) -> int:
    """根据标签关键词判断是否为东方视频。是:1 否:2"""
    for tag in tags:
        tag_lower = tag.lower()
        for kw in _TOUHOU_KEYWORDS:
            if kw in tag_lower:
                return 1
    return 2
