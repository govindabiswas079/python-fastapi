from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import todoCollection
from app.models.todo_model import TodoModel
from app.schemas.todoschema import all_todo

router = APIRouter()


@router.get("/todos", status_code=status.HTTP_200_OK)
async def get_all_todos(
    currentPage: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1),
):
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch todos: {str(e)}",
        )


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(new_todo: TodoModel):

    try:
        todo_data = new_todo.model_dump()

        result = await todoCollection.insert_one(todo_data)
        fetched_created = await todoCollection.find_one({"_id": result.inserted_id})

        fetched_created["_id"] = str(fetched_created["_id"])

        return {
            "status_code": status.HTTP_201_CREATED,
            "message": "Todo created successfully",
            "todo_id": str(result.inserted_id),
            "data": fetched_created
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create todo: {str(e)}",
        )
