from pydantic import BaseModel, Field


class SpaceVideoItem(BaseModel):
    """对应 /x/space/wbi/arc/search → data.list.vlist[] 中的单个元素"""
    aid: int
    bvid: str
    mid: int
    title: str
    created: int
    description: str = ""
    pic: str = ""
    season_id: int = 0      # 不属于合集时为 0


class SpaceList(BaseModel):
    """对应 /x/space/wbi/arc/search → data.list"""
    vlist: list[SpaceVideoItem] = Field(default_factory=list)


class SpacePageInfo(BaseModel):
    """对应 /x/space/wbi/arc/search → data.page"""
    count: int
    pn: int
    ps: int


class UserSpaceData(BaseModel):
    """对应 /x/space/wbi/arc/search → data"""
    list: SpaceList
    page: SpacePageInfo | None = None


# --- APP 接口响应模型 (app.biliapi.com/x/v2/space/archive/cursor) ---


class AppSpaceMeta(BaseModel):
    """APP 接口 item 中的 meta 对象（合集信息）"""
    id: int | None = None       # 合集 ID，不属于合集时不存在
    title: str = ""


class AppSpaceItem(BaseModel):
    """对应 APP 接口 → data.item[] 中的单个元素"""
    param: str              # 视频 aid（字符串）
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
    """对应 APP 接口 → data"""
    item: list[AppSpaceItem] = Field(default_factory=list)
    has_next: bool = False
    count: int = 0
