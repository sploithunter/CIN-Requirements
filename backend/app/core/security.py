from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()


class TokenData(BaseModel):
    user_id: UUID
    exp: datetime


def create_access_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != token_type:
            return None
        user_id = UUID(payload.get("sub"))
        exp = datetime.fromtimestamp(payload.get("exp"))
        return TokenData(user_id=user_id, exp=exp)
    except (JWTError, ValueError):
        return None
