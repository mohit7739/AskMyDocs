# Getting Started with FastAPI

FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints.

## Installation

You can install FastAPI with pip:

```bash
pip install fastapi
```

You will also need an ASGI server. The recommended one is Uvicorn:

```bash
pip install uvicorn[standard]
```

## Quick Start

Create a file called `main.py` with the following content:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Then run the server:

```bash
uvicorn main:app --reload
```

The `--reload` flag makes the server restart after code changes. It should only be used during development.

## Key Features

FastAPI provides several key features out of the box:

- **Fast**: Very high performance, on par with NodeJS and Go, thanks to Starlette and Pydantic.
- **Fast to code**: Increase the speed of developing features by about 200% to 300%.
- **Fewer bugs**: Reduce about 40% of human-induced errors.
- **Intuitive**: Great editor support with completion everywhere, reducing debugging time.
- **Easy**: Designed to be easy to use and learn.
- **Short**: Minimize code duplication.
- **Robust**: Get production-ready code with automatic interactive documentation.
- **Standards-based**: Based on (and fully compatible with) the open standards for APIs: OpenAPI and JSON Schema.

## Interactive API Documentation

FastAPI automatically generates interactive API documentation. When you run your application, you can access:

- **Swagger UI** at `http://127.0.0.1:8000/docs` — provides an interactive interface to test your API endpoints.
- **ReDoc** at `http://127.0.0.1:8000/redoc` — provides an alternative, documentation-focused interface.

Both are generated automatically from your Python type annotations and docstrings.

## Python Type Hints

FastAPI makes extensive use of Python type hints. These type hints allow FastAPI to:

1. Provide editor support (auto-completion, type checking)
2. Validate request data
3. Serialize response data
4. Generate API documentation

For example:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

In this example, `item_id` is declared as `int`, which means FastAPI will automatically validate that the path parameter is an integer and convert it.
