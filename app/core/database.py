from pymongo import AsyncMongoClient

from app.core.config import settings

MongoDBClient = AsyncMongoClient(
    settings.MONGODB_URL,
    maxPoolSize=100,
    minPoolSize=10,
    serverSelectionTimeoutMS=5000,
)

MongoDataBase = MongoDBClient[settings.DATABASE_NAME]

todoCollection = MongoDataBase["todo_data"]
userCollection = MongoDataBase["user_data"]
sessionCollection = MongoDataBase["auth_sessions"]
pendingRegistrationCollection = MongoDataBase["pending_registrations"]

async def connect_database(): 
    await MongoDBClient.admin.command('ping')

async def close_database():
    await MongoDBClient.close()
