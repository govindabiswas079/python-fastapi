from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.core.database import userCollection
from app.schemas.user_schema import all_users, individual_user

router = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_all_users(
    currentPage: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1),
):
    query = {"is_verified": True}
    number_of_data = await userCollection.count_documents(query)
    offset = (currentPage - 1) * pageSize
    users = await userCollection.find(query).skip(offset).limit(pageSize).to_list(length=pageSize)
    return {
        "users": all_users(users),
        "numberOfData": number_of_data,
        "currentPage": currentPage,
        "pageSize": pageSize,
        "totalPages": (number_of_data + pageSize - 1) // pageSize,
        "from": offset + 1 if users else 0,
        "to": offset + len(users) if users else 0,
    }


@router.get("/user/{_id}", status_code=status.HTTP_200_OK)
async def get_user(_id: str):
    if not ObjectId.is_valid(_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format")
    user = await userCollection.find_one({"_id": ObjectId(_id), "is_verified": True})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return individual_user(user)
