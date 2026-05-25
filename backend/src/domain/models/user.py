from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    __tablename__: str = "users"

    mid: int = Field(primary_key=True)
    name: str
