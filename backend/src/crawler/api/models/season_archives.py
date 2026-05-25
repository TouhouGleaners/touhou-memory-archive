from pydantic import BaseModel, Field


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
