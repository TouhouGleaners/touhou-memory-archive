from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from domain.schemas.video import VideoSchema


class VideoPart(SQLModel, table=True):
    __tablename__: str = "video_parts"

    cid: int = Field(primary_key=True)
    aid: int = Field(foreign_key="videos.aid", index=True)
    idx: int
    title: str
    duration: int | None = None

    video: Mapped["Video"] = Relationship(back_populates="parts")


class Video(SQLModel, table=True):
    __tablename__: str = "videos"

    aid: int = Field(primary_key=True)
    bvid: str = Field(unique=True, index=True)
    mid: int = Field(foreign_key="users.mid")
    title: str

    description: str | None = None
    cover_url: str | None = None
    duration: int | None = None
    published_at: int | None = None
    created_at: int | None = None

    category_id: int | None = None
    category_name: str | None = None
    copyright: int | None = None
    state: int | None = None

    view_count: int | None = None
    danmaku_count: int | None = None
    reply_count: int | None = None
    favorite_count: int | None = None
    coin_count: int | None = None
    share_count: int | None = None
    like_count: int | None = None

    tags: str | None = None  # 逗号分隔
    touhou_status: int = 0
    season_id: int | None = None

    parts: Mapped[list["VideoPart"]] = Relationship(back_populates="video")

    @classmethod
    def from_schema(cls, schema: "VideoSchema") -> "Video":
        """Pydantic schema → 表模型"""
        return cls(
            aid=schema.aid,
            bvid=schema.bvid,
            mid=schema.mid,
            title=schema.title,
            description=schema.description,
            cover_url=schema.cover_url,
            duration=schema.duration,
            published_at=schema.published_at,
            created_at=schema.created_at,
            category_id=schema.category_id,
            category_name=schema.category_name,
            copyright=schema.copyright,
            state=schema.state,
            view_count=schema.view_count,
            danmaku_count=schema.danmaku_count,
            reply_count=schema.reply_count,
            favorite_count=schema.favorite_count,
            coin_count=schema.coin_count,
            share_count=schema.share_count,
            like_count=schema.like_count,
            tags=",".join(schema.tags) if schema.tags else None,
            touhou_status=schema.touhou_status,
            season_id=schema.season_id,
        )

    def to_schema(self, uploader_name: str = "", parts: list | None = None):
        """表模型 → Pydantic schema"""
        from domain.schemas.video import VideoSchema

        return VideoSchema(
            aid=self.aid,
            bvid=self.bvid,
            mid=self.mid or 0,
            title=self.title,
            description=self.description or "",
            cover_url=self.cover_url or "",
            duration=self.duration or 0,
            published_at=self.published_at or 0,
            created_at=self.created_at or 0,
            uploader_name=uploader_name,
            category_id=self.category_id,
            category_name=self.category_name,
            copyright=self.copyright,
            state=self.state,
            touhou_status=self.touhou_status,
            view_count=self.view_count,
            danmaku_count=self.danmaku_count,
            reply_count=self.reply_count,
            favorite_count=self.favorite_count,
            coin_count=self.coin_count,
            share_count=self.share_count,
            like_count=self.like_count,
            season_id=self.season_id,
            tags=[t.strip() for t in self.tags.split(",")] if self.tags else [],
            parts=parts or [],
        )
