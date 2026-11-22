"""Small HS256 JWT helpers, implemented with the Python standard library."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import settings


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(subject: str, token_type: str, lifetime: timedelta, jti: Optional[str] = None) -> str:
    now = datetime.now(timezone.utc)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "jti": jti or secrets.token_urlsafe(24),
    }
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.JWT_SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_token(token: str, expected_type: str) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        header_part, payload_part, signature_part = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            settings.JWT_SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected_signature, _b64decode(signature_part)):
            raise unauthorized
        header = json.loads(_b64decode(header_part))
        payload = json.loads(_b64decode(payload_part))
        if header.get("alg") != "HS256" or payload.get("type") != expected_type:
            raise unauthorized
        if int(payload.get("exp", 0)) <= int(datetime.now(timezone.utc).timestamp()):
            raise unauthorized
        if not payload.get("sub") or not payload.get("jti"):
            raise unauthorized
        return payload
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise unauthorized from exc


def access_token_lifetime() -> timedelta:
    return timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def refresh_token_lifetime() -> timedelta:
    return timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
