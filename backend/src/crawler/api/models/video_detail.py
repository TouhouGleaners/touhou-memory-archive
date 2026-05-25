from pydantic import BaseModel, Field


class Page(BaseModel):
    cid: int
    page: int
    part: str
    duration: int


class Owner(BaseModel):
    mid: int
    name: str


class VideoStat(BaseModel):
    view: int = 0
    danmaku: int = 0
    reply: int = 0
    favorite: int = 0
    coin: int = 0
    share: int = 0
    like: int = 0


class VideoDetailData(BaseModel):
    aid: int
    bvid: str
    title: str
    desc: str
    pubdate: int
    ctime: int
    pic: str
    duration: int
    tid: int | None = None
    tname: str | None = None
    copyright: int | None = None
    state: int | None = None
    owner: Owner
    stat: VideoStat
    pages: list[Page] = Field(default_factory=list)
