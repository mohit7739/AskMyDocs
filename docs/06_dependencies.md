# Dependency Injection

FastAPI has a very powerful but intuitive **Dependency Injection** system. It is designed to be very simple to use, while supporting very complex use cases.

## What is Dependency Injection?

"Dependency Injection" means that there is a way for your code (your path operation functions) to declare things that it requires to work (its "dependencies"), and then the framework (FastAPI) takes care of providing those dependencies.

This is very useful when you need to:

- Share logic between different path operations
- Share database connections
- Enforce security, authentication, role requirements
- And many other use cases

## Creating a Dependency

A dependency can be any callable (function or class):

```python
from fastapi import Depends, FastAPI

app = FastAPI()

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: dict = Depends(common_parameters)):
    return commons

@app.get("/users/")
async def read_users(commons: dict = Depends(common_parameters)):
    return commons
```

The key feature is that you use `Depends()` in the function parameter's default value. FastAPI will call `common_parameters` with the matching parameters from the request and pass the result to your path operation function.

## Classes as Dependencies

You can also use classes as dependencies:

```python
from fastapi import Depends, FastAPI

app = FastAPI()

class CommonQueryParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: int = 100):
        self.q = q
        self.skip = skip
        self.limit = limit

@app.get("/items/")
async def read_items(commons: CommonQueryParams = Depends(CommonQueryParams)):
    return {"q": commons.q, "skip": commons.skip, "limit": commons.limit}
```

## Sub-dependencies

Dependencies can have their own dependencies. FastAPI will resolve them all:

```python
from fastapi import Cookie, Depends, FastAPI

app = FastAPI()

def query_extractor(q: str | None = None):
    return q

def query_or_cookie_extractor(
    q: str = Depends(query_extractor),
    last_query: str | None = Cookie(default=None),
):
    if not q:
        return last_query
    return q

@app.get("/items/")
async def read_query(query_or_default: str = Depends(query_or_cookie_extractor)):
    return {"q_or_cookie": query_or_default}
```

## Dependencies in Path Operation Decorators

In some cases, you don't need the return value of a dependency, but you still need it to be executed. You can add dependencies to the path operation decorator:

```python
from fastapi import Depends, FastAPI, Header, HTTPException

app = FastAPI()

async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: str = Header()):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key

@app.get("/items/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items():
    return [{"item": "Foo"}, {"item": "Bar"}]
```

## Global Dependencies

You can add dependencies to the whole application:

```python
from fastapi import Depends, FastAPI, Header, HTTPException

async def verify_token(x_token: str = Header()):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

app = FastAPI(dependencies=[Depends(verify_token)])
```

## Dependencies with Yield

FastAPI supports dependencies with `yield`. This is useful for resources that need cleanup, like database sessions:

```python
from fastapi import Depends, FastAPI

async def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get("/items/")
async def read_items(db = Depends(get_db)):
    items = db.query(Item).all()
    return items
```

The code after `yield` runs after the response has been sent, making this perfect for cleanup operations.
