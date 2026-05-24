from crawler.api.models import VideoDetailData, VideoTag, SpaceVideoItem
from crawler.models import Video, VideoPart


def video_detail_to_video(
    detail: VideoDetailData,
    tags: list[VideoTag],
    mid: int | None = None,
    season_id: int | None = None,
) -> Video:
    """将详情接口响应 + 标签合并为领域模型"""
    return Video(
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
        parts=[
            VideoPart(cid=p.cid, index=p.page, title=p.part, duration=p.duration)
            for p in detail.pages
        ],
    )


def space_dict_to_video(data: dict) -> Video:
    """将空间搜索 vlist 中的原始 dict 转换为领域模型"""
    return Video(
        aid=data['aid'],
        bvid=data['bvid'],
        mid=data.get('mid', 0),
        title=data.get('title', ''),
        description=data.get('description', ''),
        cover_url=data.get('pic', ''),
        published_at=data.get('created', 0),
        season_id=data.get('season_id') or None,
    )


def season_dict_to_video(data: dict, mid: int, season_id: int) -> Video:
    """将合集 archives 中的原始 dict 转换为领域模型"""
    return Video(
        aid=data['aid'],
        bvid=data['bvid'],
        mid=mid,
        title=data.get('title', ''),
        cover_url=data.get('pic', ''),
        published_at=data.get('pubdate', 0),
        created_at=data.get('ctime', 0),
        duration=data.get('duration', 0),
        season_id=season_id,
    )


def pages_dict_to_parts(pages: list[dict]) -> list[VideoPart]:
    """将 view 接口返回的 pages dict 列表转换为 VideoPart 列表"""
    return [
        VideoPart(
            cid=p['cid'],
            index=p['page'],
            title=p.get('part', ''),
            duration=p.get('duration', 0),
        )
        for p in pages
    ]


def extract_season_ids(items: list[SpaceVideoItem]) -> set[int]:
    """从空间搜索结果中提取合集 ID（排除 0）"""
    return {item.season_id for item in items if item.season_id != 0}
