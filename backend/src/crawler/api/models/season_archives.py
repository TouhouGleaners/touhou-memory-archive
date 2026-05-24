from pydantic import BaseModel


class SeasonArchiveItem(BaseModel):
    """对应 seasons_archives_list → data.archives[] 中的单个元素"""
    aid: int
    bvid: str
    ctime: int
    pubdate: int = 0
    duration: int = 0
    pic: str = ""
    title: str = ""


class SeasonMeta(BaseModel):
    """对应 seasons_archives_list → data.meta"""
    season_id: int
    name: str = ""
    mid: int = 0
    total: int = 0


class SeasonPageInfo(BaseModel):
    """对应 seasons_archives_list → data.page"""
    page_num: int
    page_size: int
    total: int


class SeasonArchivesData(BaseModel):
    """对应 seasons_archives_list → data"""
    archives: list[SeasonArchiveItem] = []
    meta: SeasonMeta | None = None
    page: SeasonPageInfo | None = None
