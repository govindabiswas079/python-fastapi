from bson import ObjectId
from fastapi import HTTPException, Query, status

from app.core.database import userCollection
from app.schemas.user_schema import all_users, individual_user


class UserService:

    def __init__(self, collection):
        self.collection = collection

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