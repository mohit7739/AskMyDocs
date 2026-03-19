# Response Models

You can declare the model used for the response with the `response_model` parameter in your path operation decorators.

## Basic Response Model

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class ItemOut(BaseModel):
    name: str
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/", response_model=ItemOut)
async def create_item(item: Item):
    return item
```

Even though the `Item` model includes `description`, the response will only include the fields defined in `ItemOut`. FastAPI will use `ItemOut` to filter and validate the output data.

## Response Model Benefits

Using `response_model` provides several benefits:

1. **Data Filtering**: Only the fields in the response model are included in the response.
2. **Data Validation**: The output data is validated against the response model.
3. **Documentation**: The response model is used to generate the API documentation.
4. **Security**: Sensitive fields (like passwords) can be excluded from the response by not including them in the response model.

## Return Type Annotations

FastAPI also supports using return type annotations instead of `response_model`:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

app = FastAPI()

@app.get("/items/")
async def read_items() -> list[Item]:
    return [
        Item(name="Portal Gun", price=42.0),
        Item(name="Plumbus", price=32.0),
    ]
```

## Response Model Exclude Unset

You can set `response_model_exclude_unset=True` to exclude fields that were not explicitly set:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float = 10.5

app = FastAPI()

items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
}

@app.get("/items/{item_id}", response_model=Item, response_model_exclude_unset=True)
async def read_item(item_id: str):
    return items[item_id]
```

This is useful when you want to distinguish between "not set" and "set to default value."

## Status Codes

You can declare the HTTP status code used for the response using the `status_code` parameter:

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/items/", status_code=201)
async def create_item(name: str):
    return {"name": name}
```

FastAPI provides convenience constants in `fastapi.status`:

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {"name": name}
```
