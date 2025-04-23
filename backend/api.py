from fastapi import FastAPI
from mongo_db import lifespan
from auth import router as auth_router

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
