from pydantic import BaseModel


class VideoTag(BaseModel):
    tag_id: int
    tag_name: str
    tag_type: str = ""
    music_id: str = ""
    jump_url: str = ""
