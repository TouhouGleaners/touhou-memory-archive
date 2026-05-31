import logging
import time
from enum import IntEnum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.auth import require_role, hash_password
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


# --- 用户管理 (superadmin) ---

class AdminUserOut(BaseModel):
    id: int
    username: str
    role: AdminRole
    is_active: bool
    created_at: int


class AdminUserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    role: AdminRole = AdminRole.ADMIN


class AdminUserUpdate(BaseModel):
    role: AdminRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    session: Session = Depends(get_session),
    _current: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
):
    return session.exec(select(Admin).order_by(Admin.id)).all()


@router.post("/users", response_model=AdminUserOut, status_code=201)
def create_user(
    body: AdminUserCreate,
    session: Session = Depends(get_session),
    current: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
):
    existing = session.exec(select(Admin).where(Admin.username == body.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"用户名 {body.username} 已存在")

    admin = Admin(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
        created_at=int(time.time()),
    )
    session.add(admin)
    session.commit()
    session.refresh(admin)
    logger.info(f"管理员 {current.username} 创建了用户 {admin.username} (role={admin.role})")
    return admin


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    session: Session = Depends(get_session),
    current: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
):
    admin = session.get(Admin, user_id)
    if not admin:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    if admin.id == current.id:
        raise HTTPException(status_code=400, detail="不能修改自己的账号")

    # 检查是否会移除系统中最后一个激活的 superadmin
    will_lose_superadmin = (
        admin.role == AdminRole.SUPERADMIN
        and admin.is_active
        and (
            (body.role is not None and body.role != AdminRole.SUPERADMIN)
            or (body.is_active is not None and not body.is_active)
        )
    )
    if will_lose_superadmin:
        other_superadmins = session.exec(
            select(Admin).where(
                Admin.id != admin.id,
                Admin.role == AdminRole.SUPERADMIN,
                Admin.is_active == True,
            )
        ).first()
        if not other_superadmins:
            raise HTTPException(status_code=409, detail="不能降级/禁用最后一个激活的超级管理员")

    if body.role is not None:
        admin.role = body.role
    if body.is_active is not None:
        admin.is_active = body.is_active
    if body.password is not None:
        admin.hashed_password = hash_password(body.password)

    session.add(admin)
    session.commit()
    session.refresh(admin)
    logger.info(f"管理员 {current.username} 修改了用户 {admin.username}")
    return admin


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
):
    admin = session.get(Admin, user_id)
    if not admin:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    if admin.id == current.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    if admin.role == AdminRole.SUPERADMIN and admin.is_active:
        other_superadmins = session.exec(
            select(Admin).where(
                Admin.id != admin.id,
                Admin.role == AdminRole.SUPERADMIN,
                Admin.is_active == True,
            )
        ).first()
        if not other_superadmins:
            raise HTTPException(status_code=409, detail="不能删除最后一个激活的超级管理员")

    session.delete(admin)
    session.commit()
    logger.info(f"管理员 {current.username} 删除了用户 {admin.username}")
