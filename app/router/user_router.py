from bson import ObjectId
from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_user
from app.service.user_service import user_service

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_users(currentPage: int = Query(default=1, ge=1), pageSize: int = Query(default=25, ge=1)):
    return await user_service.get_all_users(currentPage, pageSize)


@router.get("/{_id}", status_code=status.HTTP_200_OK)
async def  get_user(_id: str):
    return await user_service.get_user(ObjectId(_id))
