from datetime import datetime, timedelta
from jose import JWTError, jwt
from hashlib import sha256
from models.user import User
from fastapi.security import OAuth2PasswordBearer
from schemas import auth as auth_schemas
import os
import secrets
import hashlib
# Secret key and algorithm for JWT encoding/decoding
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Mock database
fake_users_db = {
    "johndoe": User(
        username="johndoe",
        full_name="John Doe",
        email="johndoe@example.com",
        hashed_password=sha256("secret".encode()).hexdigest(),
        disabled=False,
    )
}

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(32)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashed_password == hash_password(plain_password)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_user(user: auth_schemas.UserCreate):
    if user.username in fake_users_db:
        return None
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed_password,
        disabled=False
    )
    fake_users_db[user.username] = db_user
    return db_user