from pydantic import BaseModel, Field


# --- /x/web-interface/view ---


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


# --- /x/web-interface/view/detail/tag ---


class VideoTag(BaseModel):
    tag_id: int
    tag_name: str
    tag_type: str = ""
    music_id: str = ""
    jump_url: str = ""


# --- /x/space/wbi/arc/search ---


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


# --- /x/polymer/web-space/seasons_archives_list ---


class SeasonArchiveItem(BaseModel):
    aid: int
    bvid: str
    ctime: int
    pubdate: int = 0
    duration: int = 0
    pic: str = ""
    title: str = ""


class SeasonMeta(BaseModel):
    season_id: int
    name: str = ""
    mid: int = 0
    total: int = 0


class SeasonPageInfo(BaseModel):
    page_num: int
    page_size: int
    total: int


class SeasonArchivesData(BaseModel):
    archives: list[SeasonArchiveItem] = Field(default_factory=list)
    meta: SeasonMeta | None = None
    page: SeasonPageInfo | None = None


# --- APP 接口 (app.biliapi.com/x/v2/space/archive/cursor) ---


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
