from pydantic import BaseModel, Field
from typing import List


class VideoPart(BaseModel):
    cid: int
    page: int
    part: str
    duration: int
    ctime: int
    class Config:
        from_attributes = True


class Video(BaseModel):
    aid: int
    bvid: str
    mid: int
    title: str
    description: str
    pic: str
    created: int
    touhou_status: int
    parts: List[VideoPart]= Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    class Config:
        from_attributes = True