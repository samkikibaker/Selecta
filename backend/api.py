from fastapi import FastAPI
from mongo_db import lifespan
from auth import auth_router
from songs import songs_router

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(songs_router)
