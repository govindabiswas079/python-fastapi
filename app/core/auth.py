from typing import Optional

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import userCollection
from app.core.ephemeral_store import ephemeral_store
from app.core.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    payload = decode_token(credentials.credentials, "access")
    try:
        user_id = ObjectId(payload["sub"])
    except Exception as exc:  # noqa: BLE001
        raise unauthorized from exc

    user = await userCollection.find_one({"_id": user_id, "is_verified": True})
    if not user:
        raise unauthorized

    session_user_id = await ephemeral_store.get_session(payload["jti"])
    if session_user_id != str(user_id):
        raise unauthorized
    return user
