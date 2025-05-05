import os

from fastapi import APIRouter, HTTPException, Request
from models import UserCreate, UserLogin
from jose import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM")
TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


async def get_user_by_email(request: Request, email: str):
    users_collection = request.app.state.db["Users"]
    return await users_collection.find_one({"email": email})


@router.post("/register")
async def register(request: Request, user: UserCreate):
    existing_user = await get_user_by_email(request, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(user.password)
    await request.app.state.db["Users"].insert_one({"email": user.email, "password": hashed_password})
    return {"msg": "User registered successfully"}


@router.post("/login")
async def login(request: Request, user: UserLogin):
    db_user = await get_user_by_email(request, user.email)
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
