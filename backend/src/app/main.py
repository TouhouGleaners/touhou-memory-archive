import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv

# 加载 backend/.env
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .api import videos, users, auth
from .auth import hash_password
from domain.database import engine, init_db
from domain.models.admin import Admin

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Touhou Memory Archive API",
    description="API for accessing Touhou Memory video archive data.",
    version="1.0.0",
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.on_event("startup")
def seed_admin():
    """Admin 表为空时，用 .env 中的凭据创建初始 superadmin。"""
    init_db()

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        logger.warning("ADMIN_USERNAME 或 ADMIN_PASSWORD 未设置，跳过初始管理员创建")
        return

    with Session(engine) as session:
        existing = session.exec(select(Admin)).first()
        if existing:
            return
        admin = Admin(
            username=admin_username,
            hashed_password=hash_password(admin_password),
            role="superadmin",
            created_at=int(time.time()),
        )
        session.add(admin)
        session.commit()
        logger.info(f"已创建初始 superadmin: {admin_username}")


@app.get("/")
def read_root():
    return {"message": "Welcome to Touhou Memory Archive API"}