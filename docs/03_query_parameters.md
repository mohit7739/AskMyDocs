# Query Parameters

When you declare function parameters that are not part of the path parameters, they are automatically interpreted as query parameters.

## Basic Query Parameters

```python
from fastapi import FastAPI

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
```

The query parameters are:
- `skip`: with a default value of `0`
- `limit`: with a default value of `10`

For example, the URL `http://127.0.0.1:8000/items/?skip=0&limit=10` would use those query parameters.

## Optional Parameters

You can declare optional query parameters by setting their default to `None`:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None):
    if q:
        return {"item_id": item_id, "q": q}
    return {"item_id": item_id}
```

In this case, the function parameter `q` is optional and will be `None` by default.

## Query Parameter Type Conversion

FastAPI supports automatic type conversion for query parameters. For example, boolean parameters:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update({"description": "This is a long description for the item"})
    return item
```

For boolean parameters, FastAPI will accept `1`, `true`, `on`, `yes` (case-insensitive) as `True`, and `0`, `false`, `off`, `no` as `False`.

## Required Query Parameters

If you don't set a default value, the query parameter becomes required:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str, needy: str):
    item = {"item_id": item_id, "needy": needy}
    return item
```

Here, `needy` is a required query parameter. If not provided, FastAPI will return an error.

## Multiple Path and Query Parameters

You can combine path parameters and query parameters freely:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update({"description": "This is a long description"})
    return item
```

FastAPI will automatically distinguish between path parameters and query parameters based on your route definition.
