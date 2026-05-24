from sqlmodel import Session, select, delete, col

from shared.database import engine
from shared.models import Video, VideoPart
from shared.models.user import User
from shared.schemas import VideoSchema


def get_all_user_mids() -> list[int]:
    with Session(engine) as session:
        results = session.exec(select(User.mid))
        return list(results.all())


def save_video(schema: VideoSchema) -> None:
    """Upsert 视频及其分P。每次调用创建独立 session。"""
    with Session(engine) as session:
        video_model = Video.from_schema(schema)

        existing = session.get(Video, video_model.aid)
        if existing:
            for key, value in video_model.model_dump(exclude={"parts"}).items():
                setattr(existing, key, value)
        else:
            session.add(video_model)

        # 批量删除旧分P
        session.exec(delete(VideoPart).where(col(VideoPart.aid) == schema.aid))

        for part in schema.parts:
            session.add(VideoPart(
                cid=part.cid,
                aid=schema.aid,
                idx=part.index,
                title=part.title,
                duration=part.duration,
            ))

        session.commit()
