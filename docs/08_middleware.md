# Middleware

A "middleware" is a function that works with every **request** before it is processed by any specific path operation, and also with every **response** before returning it.

## Creating Middleware

You create a middleware with the `@app.middleware("http")` decorator:

```python
import time
from fastapi import FastAPI, Request

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

The middleware function receives:
- The `request` object
- A function `call_next` that receives the request as a parameter, passes it to the corresponding path operation, and returns the response

You can modify the request before passing it to `call_next`, and also modify the response before returning it.

## Built-in Middleware

FastAPI (through Starlette) provides several built-in middleware classes:

### CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Trusted Host Middleware
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"],
)
```

### HTTPS Redirect Middleware
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

### GZip Middleware
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Middleware Order

Middleware is applied in the reverse order of how they are added. The last middleware added is the first to handle the request:

```python
from fastapi import FastAPI

app = FastAPI()

# This runs SECOND for requests (FIRST for responses)
app.add_middleware(MiddlewareA)

# This runs FIRST for requests (SECOND for responses)
app.add_middleware(MiddlewareB)
```

## Advanced Middleware with BaseHTTPMiddleware

For more complex middleware, you can create a class extending `BaseHTTPMiddleware`:

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class CustomMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, some_attribute: str):
        super().__init__(app)
        self.some_attribute = some_attribute

    async def dispatch(self, request: Request, call_next):
        # Process request
        response = await call_next(request)
        # Process response
        response.headers["X-Custom-Header"] = self.some_attribute
        return response

app = FastAPI()
app.add_middleware(CustomMiddleware, some_attribute="example")
```
