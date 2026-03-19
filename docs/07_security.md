# Security and Authentication

FastAPI provides several tools to help you deal with **security** and **authentication**. It integrates with OpenAPI and provides built-in security utilities.

## OAuth2 with Password

The most common flow for authentication in APIs is OAuth2 with Password (also known as "Resource Owner Password Credentials"). Here's how to implement it:

```python
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    }
}

def fake_decode_token(token):
    user = fake_users_db.get(token)
    if user:
        return User(**user)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or form_data.password != "secret":
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": user["username"], "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
```

## OAuth2PasswordBearer

`OAuth2PasswordBearer` is a class that FastAPI provides. When you create an instance, you pass the `tokenUrl` parameter, which is the URL that the client should use to send the username and password to get a token.

The `oauth2_scheme` variable is an instance of `OAuth2PasswordBearer` and is also a callable (a dependency). It will look for the `Authorization` header, check if the value starts with `Bearer`, and return the token string.

## JWT Tokens

For production use, you should use JWT (JSON Web Tokens):

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

## API Key Authentication

For simpler cases, you can use API key authentication:

```python
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != "my-secret-api-key":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/secure-data/", dependencies=[Depends(verify_api_key)])
async def get_secure_data():
    return {"data": "This is secured by API key"}
```

## CORS (Cross-Origin Resource Sharing)

FastAPI provides CORS middleware to handle cross-origin requests:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The `allow_origins` parameter specifies which origins are allowed to make requests. Use `["*"]` to allow all origins, but this is not recommended for production.
