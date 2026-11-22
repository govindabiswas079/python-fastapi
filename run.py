import os
import sys

import uvicorn
from dotenv import load_dotenv

# Load root default .env
load_dotenv(".env")

# Get environment from command argument
environment = sys.argv[1] if len(sys.argv) > 1 else "development"

# Load environment-specific file
env_file = f".env.{environment}"

if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"Environment: {environment}")
else:
    print(f"{env_file} not found. Using default .env")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))  # noqa: PLW1508
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=DEBUG)
