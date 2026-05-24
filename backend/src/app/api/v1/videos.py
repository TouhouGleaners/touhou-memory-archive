import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from shared.database import get_session
from shared.schemas import VideoSchema

from ...crud import crud_video


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=list[VideoSchema])
def read_videos(session: Session = Depends(get_session)):
    """获取所有视频列表"""
    try:
        return crud_video.get_videos(session, is_touhou=False)
    except Exception as e:
        logger.error(f"Error fetching videos: {e}")
        raise HTTPException(status_code=500, detail="Error fetching videos")

@router.get("/touhou", response_model=list[VideoSchema])
def read_touhou_videos(session: Session = Depends(get_session)):
    """只获取东方Project相关的视频"""
    try:
        return crud_video.get_videos(session, is_touhou=True)
    except Exception as e:
        logger.error(f"Error fetching touhou videos: {e}")
        raise HTTPException(status_code=500, detail="Error fetching touhou videos")
