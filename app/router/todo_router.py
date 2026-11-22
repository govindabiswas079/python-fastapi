from fastapi import APIRouter

from app.core.database import todoCollection
from app.schemas.todoschema import all_todo

router = APIRouter()

@router.get('/')
async def get_all_todos():
    data = todoCollection.find()
    return all_todo(data)