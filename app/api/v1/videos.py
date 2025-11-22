import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from shared.models.video import Video
from ...database import get_db, get_all_videos, get_video_parts, get_touhou_videos


def _process_video_rows(db: sqlite3.Connection, video_rows: list[sqlite3.Row]) -> list[Video]:
    response_videos = []
    for video_row in video_rows:
        video_data = dict(video_row)

        video_parts = get_video_parts(db, video_data['aid'])
        video_data['parts'] = [dict(part) for part in video_parts]
        tags_str = video_data.get('tags')
        video_data['tags'] = [tag.strip() for tag in tags_str.split(',')] if tags_str else []

        response_videos.append(Video.model_validate(video_data))
    
    return response_videos

router = APIRouter()
@router.get("", response_model=list[Video])
def read_videos(db = Depends(get_db)):
    """提供视频列表的 JSON 数据给前端"""
    try:
        videos = get_all_videos(db)
        return _process_video_rows(db, videos)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching videos.") from e


@router.get("/touhou", response_model=list[Video])
def read_touhou_videos(db = Depends(get_db)):
    """提供东方视频列表的 JSON 数据给前端"""
    try:
        videos = get_touhou_videos(db)
        return _process_video_rows(db, videos)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching touhou videos.") from e