import bcrypt

from fastapi import APIRouter, HTTPException, Request
from models import UserCreate, UserLogin
from jose import jwt
from datetime import datetime, timedelta, timezone

from selecta.utils import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET

auth_router = APIRouter()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_user_by_email(request: Request, email: str):
    users_collection = request.app.state.db["Users"]
    return await users_collection.find_one({"email": email})


@auth_router.post("/register")
async def register(request: Request, user: UserCreate):
    existing_user = await get_user_by_email(request, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await request.app.state.db["Users"].insert_one({"email": user.email, "password": hashed_password})
    return {"msg": "User registered successfully"}


@auth_router.post("/login")
async def login(request: Request, user: UserLogin):
    db_user = await get_user_by_email(request, user.email)
    if not db_user or not bcrypt.checkpw(user.password.encode("utf-8"), db_user["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
