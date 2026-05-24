from sqlmodel import Session

from shared.models.user import User
from shared.schemas.user import UserSchema


def get_user_by_mid(session: Session, mid: int) -> UserSchema | None:
    user = session.get(User, mid)
    if user is None:
        return None
    return UserSchema(mid=user.mid, name=user.name)
