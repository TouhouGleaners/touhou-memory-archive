from crawler.api.models import (
    VideoDetailData, VideoTag, Page,
    SpaceVideoItem, SeasonArchiveItem,
)
from shared.schemas import VideoSchema, VideoPartSchema


def video_detail_to_video(
    detail: VideoDetailData,
    tags: list[VideoTag],
    mid: int | None = None,
    season_id: int | None = None,
) -> VideoSchema:
    """将详情接口响应 + 标签合并为领域模型"""
    return VideoSchema(
        aid=detail.aid,
        bvid=detail.bvid,
        mid=mid or detail.owner.mid,
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
        season_id=season_id,
        view_count=detail.stat.view,
        danmaku_count=detail.stat.danmaku,
        reply_count=detail.stat.reply,
        favorite_count=detail.stat.favorite,
        coin_count=detail.stat.coin,
        share_count=detail.stat.share,
        like_count=detail.stat.like,
        tags=[t.tag_name for t in tags if t.tag_type != "bgm"],
        parts=[page_to_part(p) for p in detail.pages],
    )


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


def extract_season_ids(items: list[SpaceVideoItem]) -> set[int]:
    """从空间搜索结果中提取合集 ID（排除 0）"""
    return {item.season_id for item in items if item.season_id != 0}
