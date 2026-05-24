from pydantic import BaseModel


class VideoTag(BaseModel):
    """对应 /x/web-interface/view/detail/tag → data[] 中的单个元素"""
    tag_id: int
    tag_name: str
    tag_type: str = ""      # old_channel / topic / bgm
    music_id: str = ""
    jump_url: str = ""
