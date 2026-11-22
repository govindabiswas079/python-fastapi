from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_user
from app.models.todo_model import TodoModel
from app.service.todo_service import TodoService

router = APIRouter(prefix="/todo", tags=["Todo"], dependencies=[Depends(get_current_user)])


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(new_todo: TodoModel):
    return await TodoService.create_todo(new_todo)


@router.get("/todos", status_code=status.HTTP_200_OK)
async def get_all_todos(currentPage: int = Query(default=1, ge=1), pageSize: int = Query(default=25, ge=1)):
    return await TodoService.get_all_todos(currentPage, pageSize)

@router.get("/todo/{_id}", status_code=status.HTTP_200_OK)
async def get_todo(_id: str):
    return await TodoService.get_todo(_id)


@router.put("/todo/{_id}", status_code=200)
async def update_todo(_id: str, updated_todo: TodoModel):
    return await TodoService.update_todo(_id, updated_todo)


@router.patch("/todo/completed/{_id}", status_code=200)
async def complete_and_in_complete_todo(_id: str):
    return await TodoService.complete_and_in_complete_todo(_id)


@router.patch("/todo/disable/{_id}", status_code=status.HTTP_200_OK)
async def disable_and_enable_todo(_id: str):
    return await TodoService.disable_and_enable_todo(_id)

@router.delete("/todo/{_id}", status_code=status.HTTP_200_OK)
async def delete_todo(_id: str):
    return await TodoService.delete_todo(_id)
