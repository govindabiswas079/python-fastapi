from bson import ObjectId
from fastapi import HTTPException, Query, status
import asyncio
import secrets

from app.core.config import settings

from app.core.database import userCollection
from app.schemas.user_schema import all_users, individual_user


class UserService:

    def __init__(self, collection):
        self.collection = collection

    async def update_profile_picture(self, user_id: ObjectId, upload):
        allowed_types = {
            "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
            "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
            "image/webp": (
                ".webp",
                lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
            ),
        }
        file_type = allowed_types.get(upload.content_type)
        if not file_type:
            raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")

        contents = await upload.read(5 * 1024 * 1024 + 1)
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Profile picture must be 5 MB or smaller")
        if not file_type[1](contents):
            raise HTTPException(status_code=400, detail="File content does not match its image type")

        user = await self.collection.find_one({"_id": user_id, "is_verified": True})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        settings.PROFILE_PICTURE_DIR.mkdir(parents=True, exist_ok=True)
        extension = file_type[0]
        filename = f"{user_id}-{secrets.token_hex(8)}{extension}"
        target = settings.PROFILE_PICTURE_DIR / filename
        temporary = settings.PROFILE_PICTURE_DIR / f".{user_id}-{secrets.token_hex(8)}.tmp"
        await asyncio.to_thread(temporary.write_bytes, contents)
        await asyncio.to_thread(temporary.replace, target)

        profile_picture = f"/media/profile-pictures/{filename}"
        await self.collection.update_one(
            {"_id": user_id}, {"$set": {"profile_picture": profile_picture}}
        )

        old_picture = user.get("profile_picture")
        if old_picture and old_picture.startswith("/media/profile-pictures/") and old_picture != profile_picture:
            old_path = settings.PROFILE_PICTURE_DIR / old_picture.rsplit("/", 1)[-1]
            await asyncio.to_thread(old_path.unlink, missing_ok=True)

        updated_user = await self.collection.find_one({"_id": user_id})
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Profile picture updated successfully",
            "data": individual_user(updated_user),
        }

    async def get_all_users(self, currentPage: int = Query(default=1, ge=1), pageSize: int = Query(default=25, ge=1)) :
        try:
            startIndex = (currentPage - 1) * pageSize

            cursor = await userCollection.aggregate([
                {"$match": {"is_verified": True}},
                {
                    "$lookup": {
                        "from": "todo_data",
                        "localField": "_id",
                        "foreignField": "_creator",
                        "as": "totalTodos",
                    },
                },
                {
                    "$facet": {
                        "metadata": [
                            {
                                "$count": "numberOfData"
                            },
                            {
                                "$addFields": {
                                    "currentPage": int(currentPage),
                                    "pageSize": pageSize,
                                    "totalPages": {
                                        "$toInt": {
                                            "$ceil": {
                                                "$divide": ["$numberOfData", pageSize],
                                            },
                                        }
                                    },
                                    "from": {
                                        "$cond": [
                                            { "$gt": ["$numberOfData", 0] },
                                            { "$add": [startIndex, 1] },
                                            0,
                                        ],
                                    },
                                    "to": {
                                        "$min": [
                                            { "$add": [startIndex, pageSize] },
                                            "$numberOfData",
                                        ],
                                    },
                                }
                            }
                        ],
                        "data": [
                            {
                                "$skip": startIndex,
                            },
                            {
                                "$limit": pageSize,
                            },
                            {
                                "$addFields": {
                                    "totalTodos": {
                                        "$size": "$totalTodos"
                                    },
                                }
                            },
                            {
                                "$project": {
                                    "password": 0
                                }
                            }
                        ],
                    }
                }
            ])

            users = await cursor.to_list(length=None)
            metadata = users[0]['metadata'][0]
            data = users[0]['data']

            return {
                "status_code": status.HTTP_200_OK,
                "message": "Users fetched successfully",
                "data": {
                    "users": all_users(data),
                    **metadata
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"User not found: {e}"
            )

    async def get_user(self, _id: ObjectId):
            try:
                cursor = await userCollection.aggregate([
                    {"$match": {"_id": _id, "is_verified": True}},
                    {
                        "$lookup": {
                            "from": "todo_data",
                            "localField": "_id",
                            "foreignField": "_creator",
                            "as": "totalTodos",
                        },
                    },
                    {
                        "$addFields": {
                            "totalTodos": {
                                "$size": "$totalTodos"
                            },
                        }
                    },
                    {
                        "$project": {
                            "password": 0
                        }
                    }
                ])

                user = await cursor.to_list(length=None)
                data = user[0]

                return {
                    "status_code": status.HTTP_200_OK,
                    "message": "User fetched successfully",
                    "data": {
                        "users": individual_user(data),
                    }
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"User not found: {e}"
                )

user_service = UserService(userCollection)
