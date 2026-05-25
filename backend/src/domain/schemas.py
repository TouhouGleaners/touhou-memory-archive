from pydantic import BaseModel, Field


class VideoPartSchema(BaseModel):
    cid: int
    index: int          # 分P序号
    title: str          # 分P标题
    duration: int       # 秒


class VideoSchema(BaseModel):
    # 标识
    aid: int
    bvid: str

    # 基本信息
    title: str
    description: str = ""
    cover_url: str = ""
    duration: int = 0

    # 时间
    published_at: int = 0       # 发布时间 (pubdate)
    created_at: int = 0         # 投稿时间 (ctime)

    # 作者
    mid: int = 0
    uploader_name: str = ""

    # 分类
    category_id: int | None = None       # tid
    category_name: str | None = None     # tname
    copyright: int | None = None         # 1原创 2转载

    # 状态
    state: int | None = None             # 视频状态码
    touhou_status: int = 0               # 0:未检测 1:自动东方 2:自动非东方 3:人工东方 4:人工非东方

    # 统计快照
    view_count: int | None = None
    danmaku_count: int | None = None
    reply_count: int | None = None
    favorite_count: int | None = None
    coin_count: int | None = None
    share_count: int | None = None
    like_count: int | None = None

    # 关联
    season_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    parts: list[VideoPartSchema] = Field(default_factory=list)


class UserSchema(BaseModel):
    mid: int
    name: str
