from fastapi import FastAPI
from mongo_lifespan import lifespan
from auth import auth_router
from songs import songs_router
from playlists import playlists_router

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(songs_router)
app.include_router(playlists_router)
