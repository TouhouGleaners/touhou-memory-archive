import time
from enum import IntEnum

from sqlmodel import SQLModel, Field


class AdminRole(IntEnum):
    """管理员角色，数值越小权限越高（类似 Unix nice 值）。"""
    SUPERADMIN = 1
    ADMIN = 2

    def sufficient_for(self, required: "AdminRole") -> bool:
        """当前角色是否满足所需权限（数值 <= required 即满足）。"""
        return self <= required


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: AdminRole = Field(default=AdminRole.ADMIN)
    is_active: bool = Field(default=True)
    created_at: int = Field(default_factory=lambda: int(time.time()))  # 使用 int 秒级时间戳，与 Video 模型保持一致
