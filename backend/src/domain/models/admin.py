import time
from typing import Literal

from sqlmodel import SQLModel, Field

AdminRole = Literal["admin", "superadmin"]
ROLE_HIERARCHY: dict[str, int] = {"admin": 1, "superadmin": 2}


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: AdminRole = Field(default="admin")
    is_active: bool = Field(default=True)
    created_at: int = Field(default_factory=lambda: int(time.time()))
