from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

_BACKEND_DIR = Path(__file__).parent.parent.parent
DB_PATH = _BACKEND_DIR / "bili_videos.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: yields a Session per request."""
    with Session(engine) as session:
        yield session
