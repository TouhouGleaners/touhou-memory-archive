import logging
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from shared.models.video import Video

from ...database import get_db
from ...crud import crud_video


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=list[Video])
def read_videos(db: sqlite3.Connection = Depends(get_db)):
    """获取所有视频列表"""
    try:
        return crud_video.get_videos(db, is_touhou=False)
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        raise HTTPException(status_code=500, detail="Error fetching videos")

@router.get("/touhou", response_model=list[Video])
def read_touhou_videos(db: sqlite3.Connection = Depends(get_db)):
    """只获取东方Project相关的视频"""
    try:
        return crud_video.get_videos(db, is_touhou=True)
    except Exception as e:
        logger.error(f"Error fetching touhou videos: {e}")
        raise HTTPException(status_code=500, detail="Error fetching touhou videos")