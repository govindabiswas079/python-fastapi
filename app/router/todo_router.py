from fastapi import APIRouter, HTTPException, status

from app.core.database import todoCollection
from app.models.todo_model import TodoModel
from app.schemas.todoschema import all_todo

router = APIRouter()


@router.get("/todos", status_code=status.HTTP_200_OK)
async def get_all_todos():
    try:
        data = await todoCollection.find()
        return all_todo(data)

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
