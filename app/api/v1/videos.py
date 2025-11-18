from fastapi import APIRouter, Depends, HTTPException

from shared.models.video import Video
from ...database import get_db, get_all_videos, get_video_parts


router = APIRouter()
@router.get("", response_model=list[Video])
def read_videos(db = Depends(get_db)):
    """提供视频列表的 JSON 数据给前端"""
    try:
        videos = get_all_videos(db)
        
        response_videos = []
        for video_row in videos:
            video_data = dict(video_row)

            video_parts = get_video_parts(db, video_data['aid'])

            video_data['parts'] = [dict(part) for part in video_parts]
            tags_str = video_data.get('tags')
            video_data['tags'] = [tag.strip() for tag in tags_str.split(',')] if tags_str else []

            response_videos.append(Video.model_validate(video_data))
        
        return response_videos
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching videos.") from e