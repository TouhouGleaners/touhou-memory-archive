from crawler.api.models import (
    VideoDetailData, VideoTag, Page,
    SpaceVideoItem, SeasonArchiveItem,
)
from shared.schemas import VideoSchema, VideoPartSchema


def enrich_video_from_detail(
    video: VideoSchema,
    detail: VideoDetailData,
    tags: list[VideoTag],
) -> None:
    """用详情接口数据补全已有的 schema（原地修改）"""
    video.description = detail.desc
    video.parts = pages_to_parts(detail.pages)

    video.category_id = detail.tid
    video.category_name = detail.tname
    video.copyright = detail.copyright
    video.state = detail.state

    video.view_count = detail.stat.view
    video.danmaku_count = detail.stat.danmaku
    video.reply_count = detail.stat.reply
    video.favorite_count = detail.stat.favorite
    video.coin_count = detail.stat.coin
    video.share_count = detail.stat.share
    video.like_count = detail.stat.like

    video.tags = [t.tag_name for t in tags if t.tag_type != "bgm"]


def space_item_to_video(item: SpaceVideoItem) -> VideoSchema:
    """将空间搜索 vlist 中的单个条目转换为领域模型"""
    return VideoSchema(
        aid=item.aid,
        bvid=item.bvid,
        mid=item.mid,
        title=item.title,
        description=item.description,
        cover_url=item.pic,
        published_at=item.created,
        season_id=item.season_id or None,
    )


def season_item_to_video(item: SeasonArchiveItem, mid: int, season_id: int) -> VideoSchema:
    """将合集 archives 中的单个条目转换为领域模型"""
    return VideoSchema(
        aid=item.aid,
        bvid=item.bvid,
        mid=mid,
        title=item.title,
        cover_url=item.pic,
        published_at=item.pubdate,
        created_at=item.ctime,
        duration=item.duration,
        season_id=season_id,
    )


def page_to_part(page: Page) -> VideoPartSchema:
    """将详情接口的单个分P转换为领域模型"""
    return VideoPartSchema(
        cid=page.cid,
        index=page.page,
        title=page.part,
        duration=page.duration,
    )


def pages_to_parts(pages: list[Page]) -> list[VideoPartSchema]:
    """将详情接口的分P列表转换为领域模型列表"""
    return [page_to_part(p) for p in pages]
