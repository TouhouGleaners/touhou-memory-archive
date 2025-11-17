from pydantic import BaseModel, Field


class VideoPart(BaseModel):
    cid: int
    page: int
    part: str
    duration: int
    ctime: int

class Video(BaseModel):
    aid: int
    bvid: str
    mid: int
    title: str
    description: str
    pic: str
    created: int
    tags: list[str] = Field(default_factory=list)
    parts: list[VideoPart] = Field(default_factory=list)
    touhou_status: int = 0  # 0:未检测 1:自动检测为东方 2:自动检测为非东方 3:人工确认为东方 4:人工确认为非东方