# Error Handling

FastAPI provides robust error handling capabilities using HTTP exceptions and custom exception handlers.

## HTTPException

The simplest way to handle errors is by raising an `HTTPException`:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

items = {"foo": "The Foo Wrestlers"}

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item": items[item_id]}
```

When you raise an `HTTPException`, FastAPI automatically returns the appropriate HTTP response with the status code and error detail.

## Custom Headers in Errors

You can also add custom headers to HTTP errors:

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id != "valid":
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": item_id}
```

## Custom Exception Handlers

You can create custom exception handlers for specific exception types:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

app = FastAPI()

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

@app.get("/unicorns/{name}")
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}
```

## Override Default Exception Handlers

FastAPI has some default exception handlers. You can override them:

```python
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )
```

## Using Starlette's HTTPException

FastAPI's `HTTPException` extends Starlette's `HTTPException`. The main difference is that FastAPI's version allows the `detail` field to be any JSON-serializable data, not just strings.

If you need to register exception handlers, you should register them for Starlette's `HTTPException` to catch both:

```python
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)
```
