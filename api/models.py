from pydantic import BaseModel
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
    parts: List[VideoPart]= []
    tags: List[str] = []
    class Config:
        from_attributes = True