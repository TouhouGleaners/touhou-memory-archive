from pydantic import BaseModel


class User(BaseModel):
    mid: int
    name: str
    
    class Config:
        from_attributes = True