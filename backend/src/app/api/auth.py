import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from domain.database import get_session
from domain.models.admin import Admin
from app.auth import verify_password, create_access_token, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminInfo(BaseModel):
    id: int
    username: str
    role: str


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    admin = session.exec(select(Admin).where(Admin.username == form_data.username)).first()
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    access_token = create_access_token(data={"sub": str(admin.id), "role": admin.role})
    logger.info(f"管理员 {admin.username} 登录成功")
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=AdminInfo)
def get_me(current_admin: Admin = Depends(get_current_admin)):
    return AdminInfo(id=current_admin.id, username=current_admin.username, role=current_admin.role)
