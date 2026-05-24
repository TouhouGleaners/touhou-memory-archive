from sqlmodel import SQLModel, Session, create_engine

from core.config import DB_PATH


DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: yields a Session per request."""
    with Session(engine) as session:
        yield session
