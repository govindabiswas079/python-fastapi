from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from app.core.config import settings

ALGORITHM = "HS256"


def create_token(
    user: dict,
    token_type: str,
    lifetime: timedelta,
    jti: str,
) -> str:
    now = datetime.now(timezone.utc)  # noqa: UP017
    payload = {
        "sub": str(user["_id"]),
        "user_id": str(user["_id"]),
        "email": user["email"],
        "phone": user["phone"],
        "type": token_type,
        "iat": now,
        "exp": now + lifetime,
        "jti": jti,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "user_id", "email", "phone", "type", "iat", "exp", "jti"]},
        )
        if (
            payload.get("type") != expected_type
            or payload.get("user_id") != payload.get("sub")
            or not payload.get("email")
            or not payload.get("phone")
        ):
            raise unauthorized
        return payload
    except InvalidTokenError as exc:
        raise unauthorized from exc


def access_token_lifetime() -> timedelta:
    return timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
