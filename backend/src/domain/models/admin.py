import time
from enum import IntEnum

from sqlmodel import SQLModel, Field


class AdminRole(IntEnum):
    ADMIN = 1
    SUPERADMIN = 2


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: AdminRole = Field(default=AdminRole.ADMIN)
    is_active: bool = Field(default=True)
    created_at: int = Field(default_factory=lambda: int(time.time()))
