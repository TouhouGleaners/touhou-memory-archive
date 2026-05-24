from pydantic import BaseModel


class UserSchema(BaseModel):
    mid: int
    name: str
