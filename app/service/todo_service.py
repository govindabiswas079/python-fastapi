import json

from bson import ObjectId
from fastapi import HTTPException, Query, status
from pymongo import ReturnDocument

from app.core.database import todoCollection
from app.models.todo_model import TodoModel
from app.schemas.todo_schema import all_todo, individual_data


class TodoService:
    @staticmethod
    async def create_todo(new_todo: TodoModel, creator_id: str):
        try:
            todo_data = dict(new_todo)
            todo_data["_creator"] = ObjectId(creator_id)

            result = await todoCollection.insert_one(todo_data)

            # Query MongoDB
            cursor = await todoCollection.aggregate([
                {"$match":{"_id": result.inserted_id}},
                # Lookup _creator
                {
                    "$lookup": {
                        "from": 'user_data',
                        "localField": '_creator',
                        "foreignField": '_id',
                        "pipeline": [
                            {
                                "$project": {
                                    "password": 0
                                }
                            }
                        ],
                        "as": '_creator'
                    },
                },
                {
                    "$unwind": {
                        "path": "$_creator",
                        "preserveNullAndEmptyArrays": True
                    },
                },
                {
                    "$set": {
                        "_creator": {
                            "$ifNull": ["$_creator", None]
                        }
                    }
                },
            ])

            data = await cursor.to_list(length=None)
            todo = data[0]

            return {
                "status_code": status.HTTP_201_CREATED,
                "message": "Todo created successfully",
                "data": individual_data(todo),
            }

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create todo: {e!s}",
            )

    @staticmethod
    async def get_all_todos(_creator_id: str, _creator_ids: str, currentPage: int = Query(default=1, ge=1), pageSize: int = Query(default=25, ge=1)):
        try:
            startIndex = (currentPage - 1) * pageSize

            matchQuery = {}

            if _creator_ids:
                if len(_creator_ids) == 1:
                    try:
                        _creator_ids = json.loads(_creator_ids[0])
                    except json.JSONDecodeError:
                        pass
                matchQuery["_creator"] = {
                    "$in": [ObjectId(creator_id) for creator_id in _creator_ids]
                }

            if _creator_id:
                matchQuery["_creator"] = ObjectId(_creator_id)

            cursor = await todoCollection.aggregate([
                {
                    "$match": matchQuery
                },
                # Lookup _creator
                {
                    "$lookup": {
                        "from": 'user_data',
                        "localField": '_creator',
                        "foreignField": '_id',
                        "pipeline": [
                            {
                                "$project": {
                                    "password": 0
                                }
                            }
                        ],
                        "as": '_creator'
                    },
                },
                {
                    "$unwind": {
                        "path": "$_creator",
                        "preserveNullAndEmptyArrays": True
                    },
                },
                {
                    "$set": {
                        "_creator": {
                            "$ifNull": ["$_creator", None]
                        }
                    }
                },
                # Pagination
                {
                    "$facet": {
                        "metadata": [
                            {
                                "$count": "numberOfData",
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
                                },
                            },
                        ],
                        "data": [
                            {
                                "$skip": startIndex,
                            },
                            {
                                "$limit": pageSize,
                            },
                        ],
                    },
                },
            ])
            todos = await cursor.to_list(length=None)
            result = todos[0] if todos else {}
            data = result.get("data", [])
            metadata = (result.get("metadata") or [{}])[0]


            return {
                "status_code": status.HTTP_200_OK,
                "message": "Todos fetched successfully",
                "data": {
                    "todos": all_todo(data),
                    "numberOfData": metadata.get("numberOfData", 0),
                    "currentPage": metadata.get("currentPage", 0),
                    "pageSize": metadata.get("pageSize", 0),
                    "totalPages": metadata.get("totalPages", 0),
                    "from": metadata.get("from", 0),
                    "to": metadata.get("to", 0),
                }
            }

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch todos: {e!s}",
            )

    @staticmethod
    async def get_todo(_id: str):
        try:
            # Validate MongoDB ObjectId format
            if not ObjectId.is_valid(_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Todo ID format",
                )

            # Query MongoDB
            cursor = await todoCollection.aggregate([
                {"$match":{"_id": ObjectId(_id)}},
                # Lookup _creator
                {
                    "$lookup": {
                        "from": 'user_data',
                        "localField": '_creator',
                        "foreignField": '_id',
                        "pipeline": [
                            {
                                "$project": {
                                    "password": 0
                                }
                            }
                        ],
                        "as": '_creator'
                    },
                },
                {
                    "$unwind": {
                        "path": "$_creator",
                        "preserveNullAndEmptyArrays": True
                    },
                },
                {
                    "$set": {
                        "_creator": {
                            "$ifNull": ["$_creator", None]
                        }
                    }
                },
            ])

            data = await cursor.to_list(length=None)
            todo = data[0]

            # Check if document exists
            if not todo:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
                )

            return {
                "success": True,
                "message": "Todo fetched successfully",
                "data": individual_data(todo),
            }

        except HTTPException:
            raise

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch todo: {e!s}",
            )

    @staticmethod
    async def update_todo(_id: str, updated_todo: TodoModel, creator_id: str):

        try:
            print(f"creator_id: {creator_id}")
            todo_data = dict(updated_todo)

            # Validate MongoDB ObjectId format
            if not ObjectId.is_valid(_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Todo ID format",
                )

            ifExit = await todoCollection.find_one({"_id": ObjectId(_id)})

            # Check if document exists
            if not ifExit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Todo not exit",
                )

            isSame = creator_id == str(ifExit["_creator"])
            if not isSame:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You don't have access to update"
                )

            await todoCollection.update_one({"_id": ObjectId(_id)}, {"$set": todo_data})
            fetch_updated_todo = await todoCollection.find_one({"_id": ObjectId(_id)})

            return {
                "success": True,
                "message": "Todo updated successfully",
                "data": individual_data(fetch_updated_todo),
            }

        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update todo: {e!s}",
            )

    @staticmethod
    async def complete_and_in_complete_todo(_id: str, creator_id: str):
        try:
            # Validate MongoDB ObjectId format
            if not ObjectId.is_valid(_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Todo ID format"
                )

            # fetch exiting todo
            ifExit = await todoCollection.find_one({"_id": ObjectId(_id)})

            # Check if document exists
            if not ifExit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Todo not exit",
                )

            isSame = creator_id == str(ifExit["_creator"])
            if not isSame:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You don't have access to update"
                )

            updated_todo_response = await todoCollection.find_one_and_update(
                {"_id": ObjectId(_id)},
                {"$set": {"is_completed": not ifExit.get("is_completed", False)}},
                return_document=ReturnDocument.AFTER,
            )

            return {
                "success": True,
                "message": "Todo updated successfully",
                "data": individual_data(updated_todo_response),
            }

        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update todo: {e!s}",
            )

    @staticmethod
    async def disable_and_enable_todo(_id: str, creator_id: str):
        try:
            # Validate MongoDB ObjectId format
            if not ObjectId.is_valid(_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Todo ID format"
                )

            # fetch exiting todo
            ifExit = await todoCollection.find_one({"_id": ObjectId(_id)})

            # Check if document exists
            if not ifExit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Todo not exit",
                )
            isSame = creator_id == str(ifExit["_creator"])
            if not isSame:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You don't have access to update"
                )

            updated_todo_response = await todoCollection.find_one_and_update(
                {"_id": ObjectId(_id)},
                {"$set": {"is_deleted": not ifExit.get("is_deleted", False)}},
                return_document=ReturnDocument.AFTER,
            )

            return {
                "success": True,
                "message": "Todo updated successfully",
                "data": individual_data(updated_todo_response),
            }

        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update todo: {e!s}",
            )

    @staticmethod
    async def delete_todo(_id: str, creator_id: str):
        try:
            if not ObjectId.is_valid(_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Todo ID format"
                )

            ifExit = await todoCollection.find_one({"_id": ObjectId(_id)})

            if not ifExit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Todo not exit",
                )
            isSame = creator_id == str(ifExit["_creator"])
            if not isSame:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You don't have access to delete"
                )

            await todoCollection.delete_one({"_id": ObjectId(_id)})

            return {
                "success": True,
                "message": "Todo deleted successfully",
            }

        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete todo: {e!s}",
            )
