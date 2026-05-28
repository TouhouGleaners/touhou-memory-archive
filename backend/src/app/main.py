import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .api import videos, users, auth, admin
from .auth import hash_password
from .config import SECRET_KEY  # noqa: F401 — 确保启动时校验
from domain.database import engine, init_db
from domain.models.admin import Admin, AdminRole

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
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.on_event("startup")
def on_startup():
    init_db()

    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_username or not admin_password:
        logger.warning("ADMIN_USERNAME 或 ADMIN_PASSWORD 未设置，跳过初始管理员创建")
        return

    with Session(engine) as session:
        existing = session.exec(select(Admin).where(Admin.username == admin_username)).first()
        if existing:
            logger.info(f"管理员 {admin_username} 已存在，跳过创建")
            return
        admin = Admin(
            username=admin_username,
            hashed_password=hash_password(admin_password),
            role=AdminRole.SUPERADMIN,
        )
        session.add(admin)
        try:
            session.commit()
            logger.info(f"已创建初始 superadmin: {admin_username}")
        except IntegrityError:
            session.rollback()
            logger.warning(f"创建管理员 {admin_username} 时发生唯一约束冲突，可能已被其他实例创建")


@app.get("/")
def read_root():
    return {"message": "Welcome to Touhou Memory Archive API"}
