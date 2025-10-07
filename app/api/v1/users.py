from fastapi import APIRouter, Depends, HTTPException, Path

from ...models import User
from ...database import get_db, get_user_by_mid


router = APIRouter()
@router.get("/{mid}", response_model=User, summary="获取单个 UP 主信息")
def read_user(
    mid: int = Path(..., gt=0, description="用户 mid"),
    db = Depends(get_db)
):
    """通过用户 mid 获取单个 UP 主信息"""
    user = get_user_by_mid(db, mid=mid)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return dict(user)
