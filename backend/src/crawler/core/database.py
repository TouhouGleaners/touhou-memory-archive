from sqlmodel import Session, select

from shared.models import Video, VideoPart
from shared.models.user import User
from shared.schemas import VideoSchema


def get_all_user_mids(session: Session) -> list[int]:
    results = session.exec(select(User.mid))
    return list(results.all())


def save_video(session: Session, schema: VideoSchema) -> None:
    """Upsert 视频及其分P"""
    video_model = Video.from_schema(schema)

    existing = session.get(Video, video_model.aid)
    if existing:
        for key, value in video_model.model_dump(exclude={"parts"}).items():
            setattr(existing, key, value)
    else:
        session.add(video_model)

    # 替换分P
    old_parts = session.exec(
        select(VideoPart).where(VideoPart.aid == schema.aid)
    ).all()
    for p in old_parts:
        session.delete(p)

    for part in schema.parts:
        session.add(VideoPart(
            cid=part.cid,
            aid=schema.aid,
            idx=part.index,
            title=part.title,
            duration=part.duration,
        ))

    session.commit()
