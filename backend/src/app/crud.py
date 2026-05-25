from sqlmodel import Session, select, col

from domain.models import Video, VideoPart, User
from domain.schemas import VideoSchema, VideoPartSchema, UserSchema


def get_videos(session: Session, is_touhou: bool = False) -> list[VideoSchema]:
    """获取视频列表"""
    stmt = select(Video, User.name).join(User, Video.mid == User.mid, isouter=True)

    if is_touhou:
        stmt = stmt.where(col(Video.touhou_status).in_([1, 3]))

    stmt = stmt.order_by(col(Video.published_at).desc())

    results = session.exec(stmt).all()
    if not results:
        return []

    aids = [row[0].aid for row in results]

    parts_stmt = select(VideoPart).where(col(VideoPart.aid).in_(aids))
    all_parts = session.exec(parts_stmt).all()

    parts_map: dict[int, list] = {}
    for part in all_parts:
        parts_map.setdefault(part.aid, []).append(part)

    videos = []
    for video_model, uploader_name in results:
        raw_parts = parts_map.get(video_model.aid, [])
        part_schemas = [
            VideoPartSchema(cid=p.cid, index=p.idx, title=p.title, duration=p.duration)
            for p in raw_parts
        ]
        videos.append(video_model.to_schema(uploader_name=uploader_name or "", parts=part_schemas))

    return videos


def get_user_by_mid(session: Session, mid: int) -> UserSchema | None:
    """通过 mid 获取用户"""
    user = session.get(User, mid)
    if user is None:
        return None
    return UserSchema(mid=user.mid, name=user.name)
