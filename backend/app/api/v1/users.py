import logging
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Path

from ....shared.models.user import User
from ...database import get_db
from ...crud import crud_user


logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{mid}", response_model=User, summary="获取单个 UP 主信息")
def read_user(
    mid: int = Path(..., gt=0, description="用户 mid"),
    db: sqlite3.Connection = Depends(get_db)
):
    """通过用户 mid 获取单个 UP 主信息"""
    try:
        user_data = crud_user.get_user_by_mid(db, mid)
        if user_data is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {mid}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")