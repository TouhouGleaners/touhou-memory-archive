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
    tags: List[str] = Field(default_factory=list)
    parts: List[VideoPart]= Field(default_factory=list)
    class Config:
        from_attributes = True


class User(BaseModel):
    mid: int
    name: str
    class Config:
        from_attributes = True