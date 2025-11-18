from pydantic import BaseModel, Field, model_validator
from typing import Any


class VideoPart(BaseModel):
    cid: int
    page: int
    part: str
    duration: int
    ctime: int

class Video(BaseModel):
    aid: int
    bvid: str
    mid: int
    title: str
    description: str | None = Field(default=None)
    pic: str
    created: int
    season_id: int | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)
    parts: list[VideoPart] = Field(default_factory=list)
    touhou_status: int = 0  # 0:未检测 1:自动检测为东方 2:自动检测为非东方 3:人工确认为东方 4:人工确认为非东方
    
    @model_validator(mode='before')
    @classmethod
    def unify_timestamp_field(cls, data: Any) -> Any:
        """
        在验证前预处理数据：
        如果数据中有 'pubdate' 字段，就将其值赋给 'created' 字段。
        """
        if isinstance(data, dict):
            if 'pubdate' in data and 'created' not in data:
                data['created'] = data.pop('pubdate')
        return data