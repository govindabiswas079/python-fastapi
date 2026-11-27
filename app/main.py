from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import close_database, connect_database, create_indexes
from app.core.ephemeral_store import ephemeral_store
from app.router.auth_router import router as auth_router
from app.router.todo_router import router as todo_router
from app.router.user_router import router as user_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()
    await create_indexes()
    await ephemeral_store.connect()
    print("MongoDB connected successfully")
    yield
    await ephemeral_store.close()
    await close_database()


app = FastAPI(
    title=settings.APP_NAME,
    description="REST API using FastAPI and MongoDB",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount(
    "/media/profile-pictures",
    StaticFiles(directory=str(settings.PROFILE_PICTURE_DIR), check_dir=False),
    name="profile-pictures",
)

app.include_router(
    auth_router,
    prefix=settings.API_PREFIX
)
app.include_router(
    user_router,
    prefix=settings.API_PREFIX
)
app.include_router(
    todo_router,
    prefix=settings.API_PREFIX
)


@app.get("/")
async def root():
    return {
        "message": "Backend API is running",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    return {
        "message": "Backend API is running",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "status": "healthy",
    }
