from fastapi import Query


class UserService:

    @staticmethod
    async def get_all_users(currentPage: int = Query(default=1, ge=1), pageSize: int = Query(default=25, ge=1)) :
        return

    @staticmethod
    async def get_user(_id: str):
        return