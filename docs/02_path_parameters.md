# Path Parameters

You can declare path parameters (or path variables) with the same syntax used by Python format strings.

## Basic Path Parameters

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id):
    return {"item_id": item_id}
```

The value of the path parameter `item_id` will be passed to your function as the argument `item_id`.

## Path Parameters with Types

You can declare the type of a path parameter using standard Python type annotations:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

In this case, `item_id` is declared to be an `int`. This gives you editor support, including error checks, completion, etc.

## Data Validation

If you try to access `http://127.0.0.1:8000/items/foo` (where `foo` is not an integer), you will receive an HTTP error:

```json
{
    "detail": [
        {
            "loc": ["path", "item_id"],
            "msg": "value is not a valid integer",
            "type": "type_error.integer"
        }
    ]
}
```

FastAPI automatically validates that the `item_id` is an integer. If it is not, a clear, useful error is returned.

## Order Matters

When creating path operations, you should be careful about the order. For example:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}

@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}
```

Because path operations are evaluated in order, `/users/me` must be declared before `/users/{user_id}` to ensure it is matched first.

## Predefined Values with Enum

If you have a path parameter that should only accept predefined values, you can use a Python `Enum`:

```python
from enum import Enum
from fastapi import FastAPI

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

app = FastAPI()

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}
```

The available values for the path parameter will be shown in the automatic API documentation.

## Path Parameters Containing Paths

If you need a path parameter that contains a path itself, you can use Starlette's path converter:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
```

The `:path` converter tells Starlette to match the rest of the URL path, including slashes.
