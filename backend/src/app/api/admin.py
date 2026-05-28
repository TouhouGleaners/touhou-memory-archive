import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.auth import require_role
from domain.database import get_session
from domain.models.admin import Admin, AdminRole
from domain.models.video import Video

logger = logging.getLogger(__name__)

router = APIRouter()


class TouhouStatusUpdate(BaseModel):
    touhou_status: int = Field(ge=0, le=4)  # 0:未检测 1:自动东方 2:自动非东方 3:人工东方 4:人工非东方


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
