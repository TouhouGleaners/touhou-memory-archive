"""B站 API 响应模型：/x/space/wbi/arc/search"""
from pydantic import BaseModel, Field


class SpaceVideoItem(BaseModel):
    """data.list.vlist[]"""
    aid: int
    bvid: str
    mid: int
    title: str
    created: int
    description: str = ""
    pic: str = ""
    season_id: int = 0


class SpaceList(BaseModel):
    vlist: list[SpaceVideoItem] = Field(default_factory=list)


class SpacePageInfo(BaseModel):
    count: int
    pn: int
    ps: int


class UserSpaceData(BaseModel):
    list: SpaceList
    page: SpacePageInfo | None = None
