from datetime import datetime

from pydantic import BaseModel


class TodoModel(BaseModel):
    _creator: str
    title: str
    description: str
    is_completed: bool = False
    is_deleted: bool = False
    createdAt: int = int(datetime.timestamp(datetime.now()))
    updatedAt: int = int(datetime.timestamp(datetime.now()))