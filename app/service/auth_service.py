import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pymongo.errors import DuplicateKeyError

from app.core.database import userCollection
from app.core.ephemeral_store import (
    ephemeral_store,
    otp_lifetime_seconds,
    refresh_lifetime_seconds,
)
from app.core.security import (
    access_token_lifetime,
    create_token,
    decode_token,
)
from app.models.user_model import UserModel
from app.schemas.user_schema import individual_user

password_hash = PasswordHash.recommended()

# Dummy OTP for development
DUMMY_OTP = "123456"


class AuthService:

    def __init__(self, collection):
        self.collection = collection

    async def _issue_tokens(self, user):
        session_id = secrets.token_urlsafe(32)
        await ephemeral_store.set_session(
            session_id, str(user["_id"]), refresh_lifetime_seconds()
        )
        return {
            "access_token": create_token(
                user, "access", access_token_lifetime(), session_id
            ),
            "refresh_token": create_token(
                user, "refresh",
                timedelta(seconds=refresh_lifetime_seconds()),
                session_id,
            ),
            "token_type": "bearer",
            "expires_in": int(access_token_lifetime().total_seconds()),
        }

    # ==================== REGISTER ====================

    async def register(self, new_user: UserModel):
        try:
            duplicate_query = {
                "$or": [{"email": new_user.email}, {"phone": new_user.phone}]
            }
            existing_user = await self.collection.find_one(duplicate_query)
            if existing_user or await ephemeral_store.has_pending(
                new_user.email, new_user.phone
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email or phone number already registered",
                )

            user_data = new_user.model_dump(mode="json")

            # Remove plain-text password
            password = user_data.pop("password")

            # Hash password
            user_data["password"] = password_hash.hash(password)

            # Keep unverified details outside the registered user collection.
            user_data["registerOTP"] = DUMMY_OTP
            if not await ephemeral_store.create_pending(
                new_user.email,
                new_user.phone,
                user_data,
                otp_lifetime_seconds(),
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email or phone number already has a pending registration",
                )

            return {
                "status_code": status.HTTP_201_CREATED,
                "message": "OTP sent. Verify it to complete registration.",
                "otp": DUMMY_OTP,  # Development only
            }

        except HTTPException:
            raise

        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or phone number already registered",
            )

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {e!s}",
            )

    # ==================== VERIFY REGISTER OTP ====================

    async def verify_register_otp(self, email: str, otp: str):
        try:
            user = await ephemeral_store.get_pending(email)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if user.get("registerOTP") != otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP",
                )

            current_timestamp = int(
                datetime.now(timezone.utc).timestamp()  # noqa: UP017
            )

            user.pop("registerOTP", None)
            user["is_verified"] = True
            user["updatedAt"] = current_timestamp
            result = await self.collection.insert_one(user)
            updated_user = await self.collection.find_one({"_id": result.inserted_id})
            await ephemeral_store.delete_pending(email, user["phone"])

            return {
                "status_code": status.HTTP_200_OK,
                "message": "Account verified successfully",
                "data": individual_user(updated_user),
                **await self._issue_tokens(updated_user),
            }

        except HTTPException:
            raise

        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email or phone number already registered",
            )

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OTP verification failed: {e!s}",
            )

    # ==================== LOGIN ====================

    async def login(self, identifier: str, password: str):
        try:
            user = await self.collection.find_one(
                {
                    "$or": [
                        {"email": identifier},
                        {"phone": identifier},
                    ]
                }
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email/phone or password",
                )

            if not password_hash.verify(
                password,
                user["password"],
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email/phone or password",
                )

            if not user.get("is_verified", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your account first",
                )

            return {
                "status_code": status.HTTP_200_OK,
                "message": "Login successful",
                "data": individual_user(user),
                **await self._issue_tokens(user),
            }

        except HTTPException:
            raise

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {e!s}",
            )

    async def refresh(self, refresh_token: str):
        payload = decode_token(refresh_token, "refresh")
        session_user_id = await ephemeral_store.get_session(payload["jti"])
        try:
            user_id = ObjectId(payload["sub"])
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token") from exc
        if session_user_id != str(user_id):
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        user = await self.collection.find_one({"_id": user_id, "is_verified": True})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        # Rotate the session so a refresh token can be used only once.
        consumed_user_id = await ephemeral_store.consume_session(payload["jti"])
        if consumed_user_id != str(user_id):
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Token refreshed successfully",
            **await self._issue_tokens(user),
        }

    # ==================== FORGOT PASSWORD ====================

    async def forgot_password(self, identifier: str):
        try:
            user = await self.collection.find_one(
                {
                    "$or": [
                        {"email": identifier},
                        {"phone": identifier},
                    ]
                }
            )

            if not user:
                return {
                    "status_code": status.HTTP_200_OK,
                    "message": "If the account exists, OTP has been sent.",
                }

            await self.collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "forgotPasswordOTP": DUMMY_OTP,
                        "forgotPasswordOTPVerified": False,
                    }
                },
            )

            return {
                "status_code": status.HTTP_200_OK,
                "message": "OTP sent successfully",
                "otp": DUMMY_OTP,  # Development only
            }

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Forgot password failed: {e!s}",
            )

    # ==================== VERIFY FORGOT PASSWORD OTP ====================

    async def verify_forgot_password_otp(
        self,
        identifier: str,
        otp: str,
    ):
        try:
            user = await self.collection.find_one(
                {
                    "$or": [
                        {"email": identifier},
                        {"phone": identifier},
                    ]
                }
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if user.get("forgotPasswordOTP") != otp:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid OTP",
                )

            await self.collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "forgotPasswordOTPVerified": True,
                    }
                },
            )

            return {
                "status_code": status.HTTP_200_OK,
                "message": "OTP verified successfully",
            }

        except HTTPException:
            raise

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OTP verification failed: {e!s}",
            )

    # ==================== RESET PASSWORD ====================

    async def reset_password(
        self,
        identifier: str,
        new_password: str,
    ):
        try:
            user = await self.collection.find_one(
                {
                    "$or": [
                        {"email": identifier},
                        {"phone": identifier},
                    ]
                }
            )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if not user.get("forgotPasswordOTPVerified", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please verify OTP first",
                )

            hashed_password = password_hash.hash(new_password)

            current_timestamp = int(
                datetime.now(timezone.utc).timestamp()  # noqa: UP017
            )

            await self.collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "password": hashed_password,
                        "updatedAt": current_timestamp,
                    },
                    "$unset": {
                        "forgotPasswordOTP": "",
                        "forgotPasswordOTPVerified": "",
                    },
                },
            )

            return {
                "status_code": status.HTTP_200_OK,
                "message": "Password reset successfully",
            }

        except HTTPException:
            raise

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Password reset failed: {e!s}",
            )


auth_service = AuthService(userCollection)
