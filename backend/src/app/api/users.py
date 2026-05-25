import logging

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session

from domain.database import get_session
from domain.schemas import UserSchema

from ..crud import get_user_by_mid


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{mid}", response_model=UserSchema, summary="获取单个 UP 主信息")
def read_user(
    mid: int = Path(..., gt=0, description="用户 mid"),
    session: Session = Depends(get_session)
):
    """通过用户 mid 获取单个 UP 主信息"""
    try:
        user = get_user_by_mid(session, mid)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {mid}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
