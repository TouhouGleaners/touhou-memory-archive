import logging
from enum import IntEnum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.auth import require_role
from domain.database import get_session
from domain.models.admin import Admin, AdminRole
from domain.models.video import Video

logger = logging.getLogger(__name__)

router = APIRouter()


# 前端对应定义在 frontend/src/utils/index.js 的 touhouStatusOptions，修改时需同步
class TouhouStatus(IntEnum):
    UNKNOWN = 0
    AUTO_TOUHOU = 1
    AUTO_NON_TOUHOU = 2
    MANUAL_TOUHOU = 3
    MANUAL_NON_TOUHOU = 4


class TouhouStatusUpdate(BaseModel):
    touhou_status: TouhouStatus


@router.patch("/videos/{bvid}/touhou-status")
def update_touhou_status(
    bvid: str,
    body: TouhouStatusUpdate,
    session: Session = Depends(get_session),
    current_admin: Admin = Depends(require_role(AdminRole.ADMIN)),
):

    video = session.exec(select(Video).where(Video.bvid == bvid)).first()
    if not video:
        raise HTTPException(status_code=404, detail=f"视频 {bvid} 不存在")

    video.touhou_status = body.touhou_status
    session.add(video)
    session.commit()
    session.refresh(video)

    logger.info(f"管理员 {current_admin.username} 将 {bvid} 的 touhou_status 改为 {body.touhou_status}")
    return {"bvid": bvid, "touhou_status": video.touhou_status}
