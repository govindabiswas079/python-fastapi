import os
from pathlib import Path

from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Load default environment
load_dotenv(BASE_DIR / ".env")

# Determine active environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Load environment-specific configuration
ENV_FILE = BASE_DIR / f".env.{ENVIRONMENT}"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)


# Application configuration
class Config:
    APP_NAME = os.getenv("APP_NAME", "FastAPI MongoDB Backend")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "myapp")
    API_PREFIX = os.getenv('API_PREFIX', '/api/v1')
    CORS_ORIGINS: list[str] = []  # noqa: RUF012


settings = Config()