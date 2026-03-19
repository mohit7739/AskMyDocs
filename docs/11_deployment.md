# Deployment

FastAPI applications can be deployed in many ways. Here are the most common deployment strategies.

## Running with Uvicorn

Uvicorn is the recommended ASGI server for FastAPI:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

For production, you should run with multiple workers:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Using Gunicorn with Uvicorn Workers

For production deployments, Gunicorn with Uvicorn workers is recommended:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

This uses Gunicorn as the process manager and Uvicorn as the ASGI server, giving you the best of both worlds.

## Docker Deployment

A typical production Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Environment Variables

For production, use environment variables for configuration:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My App"
    debug: bool = False
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()
```

## HTTPS/TLS

For production, always use HTTPS. You can configure this at the reverse proxy level (Nginx, Traefik) or directly with Uvicorn:

```bash
uvicorn main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
```

## Startup and Shutdown Events

FastAPI supports lifespan events for startup and shutdown logic:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load models, connect to DB, etc.
    print("Starting up...")
    yield
    # Shutdown: cleanup resources
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

## Health Checks

Always include a health check endpoint for monitoring:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Logging

Configure proper logging for production:

```python
import logging
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}
```

## Performance Tips

1. **Use async functions** when handling I/O-bound operations
2. **Use connection pooling** for database connections
3. **Enable response caching** for read-heavy endpoints
4. **Use background tasks** for non-critical operations:

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def write_log(message: str):
    with open("log.txt", mode="a") as log:
        log.write(message)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, f"notification sent to {email}")
    return {"message": "Notification sent"}
```

## Background Tasks

FastAPI provides the `BackgroundTasks` class to run tasks after the response is sent:

```python
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

def process_data(data: dict):
    # This runs after the response is sent
    import time
    time.sleep(5)
    print(f"Processed: {data}")

@app.post("/items/")
async def create_item(data: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_data, data)
    return {"status": "accepted"}
```

Background tasks are useful for operations that:
- Don't need to be completed before the response
- Can run independently of the request
- Are I/O-bound (sending emails, writing logs, etc.)
