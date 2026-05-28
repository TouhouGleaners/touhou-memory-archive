import time
from typing import Literal

from sqlmodel import SQLModel, Field


class Admin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: Literal["admin", "superadmin"] = Field(default="admin")
    is_active: bool = Field(default=True)
    created_at: int = Field(default_factory=lambda: int(time.time()))
