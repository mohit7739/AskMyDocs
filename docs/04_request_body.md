# Request Body

When you need to send data from a client to your API, you send it as a **request body**. A request body is data sent by the client to your API. A response body is the data your API sends to the client.

## Pydantic Models

To declare a request body, you use Pydantic models:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

The request body is declared as a parameter with its type being the Pydantic model. FastAPI will:

1. Read the body of the request as JSON
2. Validate the data against the model
3. Convert the data to the declared types
4. Give you the resulting model instance

## Using the Model

Inside the function, you can access all the attributes of the model object directly:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
```

## Request Body + Path Parameters

You can use path parameters and request body at the same time. FastAPI will recognize that function parameters matching path parameters should be taken from the path, and parameters declared as Pydantic models should be taken from the request body:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}
```

## Request Body + Path + Query Parameters

You can also combine request body, path parameters, and query parameters:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

app = FastAPI()

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result
```

FastAPI recognizes each parameter by:
- If the parameter is declared in the path, it will be used as a path parameter.
- If the parameter is of a singular type (like `int`, `float`, `str`, `bool`, etc.), it will be interpreted as a query parameter.
- If the parameter is declared to be of the type of a Pydantic model, it will be interpreted as a request body.

## Field Validation

You can add validation to your Pydantic model fields using `Field`:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str
    description: str | None = Field(default=None, max_length=300)
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None

app = FastAPI()

@app.post("/items/")
async def create_item(item: Item):
    return item
```

The `Field` function works similarly to `Query` and `Path`, and allows you to add validation and metadata for model attributes.
