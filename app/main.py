from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_database, connect_database
from app.router import todo_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()
    print("MongoDB connected successfully")
    yield
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
