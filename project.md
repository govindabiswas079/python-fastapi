# FastAPI MongoDB Backend

A FastAPI backend using MongoDB for persistence, with authentication and user routes.

## Requirements

- Python 3.11 or newer. The code uses `datetime.UTC` and modern type hints, so Python 3.9 is not supported.
- MongoDB, running locally or available through a connection URL.
- Homebrew on macOS if you want to install Python with the commands below.

## Install

Run these commands from the project root:

```bash
# Install Python if needed (macOS with Homebrew)
brew install python@3.11

# Create and activate a virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install the project dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create local configuration from the example
cp .env.example .env
```

Edit `.env` and set `MONGODB_URL` to your MongoDB connection string. Set `JWT_SECRET_KEY` to a long, random secret before using the backend beyond local development. Do not commit `.env`; it is ignored by Git.

For a local MongoDB server installed with Homebrew, start it with:

```bash
brew services start mongodb-community
```

If MongoDB is already running or hosted elsewhere, use its URL in `.env` instead.

## Run

With the virtual environment activated and MongoDB reachable:

```bash
uvicorn app.main:app --reload
uvicorn app.main:app --reload --port 8080
uvicorn app.main:app --port 8000 --reload
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```


## Run with .env

With the virtual environment activated and MongoDB reachable:

```bash
python run.py
python run.py development
python run.py testing
python run.py production
```

The API is served at `http://127.0.0.1:8000`. Useful endpoints:

- API documentation: <http://127.0.0.1:8000/docs>
- Root: <http://127.0.0.1:8000/>
- Application health: <http://127.0.0.1:8000/health>
- MongoDB health: <http://127.0.0.1:8000/health/database>

Stop the server with `Ctrl+C`.

To create an administrator account, run this in another terminal from the project root, with the environment configured:

```bash
source venv/bin/activate
python -m scripts.create_admin
```

## Clean up

To stop the local MongoDB service installed through Homebrew:

```bash
brew services stop mongodb-community
```

To remove the Python virtual environment and generated Python cache files (this does not delete MongoDB data or source files):

```bash
deactivate  # skip if the virtual environment is not active
rm -rf venv
find . -type d -name __pycache__ -prune -exec rm -rf {} +
find . -type f -name '*.py[co]' -delete
```

To start again, repeat the [install](#install) steps. To remove the local `.env` file as well, delete it manually; it contains your local configuration.

## Project layout

```text
app/
├── core/           # Settings, MongoDB connection, and security helpers
├── dependencies/   # FastAPI dependencies such as authentication
├── models/         # MongoDB document helpers
├── schemas/        # Request and response schemas
├── repositories/   # Database access
├── services/       # Application logic
├── routes/         # API endpoints
└── utils/          # Shared response helpers
scripts/            # Administrative scripts
```
