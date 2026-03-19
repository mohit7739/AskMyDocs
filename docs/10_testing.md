# Testing

FastAPI provides excellent testing support using the `TestClient` class from Starlette, which is built on top of `httpx`.

## TestClient

You can use `TestClient` to test your FastAPI application without starting the server:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

## Testing with pytest

FastAPI works great with pytest. Here is a complete example:

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# test_main.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_item():
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42}

def test_read_item_bad_type():
    response = client.get("/items/foo")
    assert response.status_code == 422
```

## Testing with Dependencies Override

You can override dependencies during testing:

```python
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

async def get_db():
    return {"connected": True}

@app.get("/items/")
async def read_items(db=Depends(get_db)):
    return {"db": db}

# In tests
def test_read_items():
    async def override_get_db():
        return {"connected": False, "test": True}

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    response = client.get("/items/")
    assert response.json() == {"db": {"connected": False, "test": True}}
    app.dependency_overrides.clear()
```

## Async Tests

For testing async functions, use `pytest-asyncio` with `httpx.AsyncClient`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
```

## Running Tests

Run your tests with pytest:

```bash
pip install pytest httpx
pytest tests/ -v
```

## Test Organization

It is recommended to organize your tests in a `tests/` directory:

```
project/
├── app/
│   ├── main.py
│   └── routers/
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_items.py
```

Each test file should start with `test_` and each test function should also start with `test_`.
