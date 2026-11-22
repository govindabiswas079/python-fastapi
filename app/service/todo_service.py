from bson import ObjectId
from fastapi import HTTPException, Query, status
from pymongo import ReturnDocument

from app.core.database import todoCollection
from app.models.todo_model import TodoModel
from app.schemas.todo_schema import all_todo, individual_data


class TodoService:
    @staticmethod
    async def create_todo(new_todo: TodoModel):
        try:
            todo_data = dict(new_todo)

            result = await todoCollection.insert_one(todo_data)
            fetched_created = await todoCollection.find_one({"_id": result.inserted_id})

            fetched_created["_id"] = str(fetched_created["_id"])

            return {
                "status_code": status.HTTP_201_CREATED,
                "message": "Todo created successfully",
                "todo_id": str(result.inserted_id),
                "data": fetched_created,
            }

        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create todo: {e!s}",
            )

    @staticmethod
    async def get_all_todos(currentPage: int = Query(default=1, ge=1), pageSize: int = Query(default=25, ge=1)):
        try:
            number_of_data = await todoCollection.count_documents({})
            total_pages = (number_of_data + pageSize - 1) // pageSize
            offset = (currentPage - 1) * pageSize

            print(f"number_of_data: {number_of_data}")
            print(f"total_pages: {total_pages}")
            print(f"offset: {offset}")

            cursor = todoCollection.find({}).skip(offset).limit(pageSize)
            data = await cursor.to_list(length=pageSize)

            # For an empty result (including a page beyond the last page), report
            # zero-based bounds while preserving the requested page number.
            from_item = offset + 1 if data else 0
            to_item = offset + len(data) if data else 0

            return {
                "todos": all_todo(data),
                "numberOfData": number_of_data,
                "currentPage": currentPage,
                "pageSize": pageSize,
                "totalPages": total_pages,
                "from": from_item,
                "to": to_item,
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
            todo = await todoCollection.find_one({"_id": ObjectId(_id)})

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
    async def update_todo(_id: str, updated_todo: TodoModel):

        try:
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
    async def complete_and_in_complete_todo(_id: str):
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
    async def disable_and_enable_todo(_id: str):
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

            updated_todo_response = await todoCollection.find_one_and_update(
                {"_id": ObjectId(_id)},
                {"$set": {"is_deleted": not ifExit.get("is_deleted", False)}},
                return_document=ReturnDocument.AFTER,
            )

            print(f"updated_todo_response: {updated_todo_response}")

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
    async def delete_todo(_id: str):
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