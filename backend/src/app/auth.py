import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from domain.database import get_session
from domain.models.admin import Admin, AdminRole

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.environ["SECRET_KEY"], algorithm=ALGORITHM)


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=[ALGORITHM])
        admin_id: str | None = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
        admin_id_int = int(admin_id)
    except (JWTError, ValueError):
        raise credentials_exception

    admin = session.get(Admin, admin_id_int)
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin


def require_role(required_role: AdminRole):
    """依赖注入工厂：要求当前管理员的角色 >= required_role。"""

    async def _check(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        if current_admin.role < required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )
        return current_admin

    return _check
