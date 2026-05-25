from pydantic import BaseModel, Field


class SpaceVideoItem(BaseModel):
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


class AppSpaceMeta(BaseModel):
    id: int | None = None
    title: str = ""


class AppSpaceItem(BaseModel):
    param: str
    bvid: str
    title: str
    ctime: int
    cover: str = ""
    author: str = ""
    duration: int = 0
    play: int = 0
    danmaku: int = 0
    meta: AppSpaceMeta | None = None


class AppSpaceData(BaseModel):
    item: list[AppSpaceItem] = Field(default_factory=list)
    has_next: bool = False
    count: int = 0
