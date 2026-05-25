"""B站 API 响应模型：/x/web-interface/view/detail/tag"""
from pydantic import BaseModel


class VideoTag(BaseModel):
    """data[] 中的单个元素"""
    tag_id: int
    tag_name: str
    tag_type: str = ""
    music_id: str = ""
    jump_url: str = ""
