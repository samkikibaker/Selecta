from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
from dotenv import load_dotenv

from models import PlaylistCreateRequest, GetPlaylistsRequest
from selecta.mongo_db import insert_documents, query_collection

load_dotenv()

playlists_router = APIRouter()


@playlists_router.post("/create_playlist")
async def create_playlist(request: Request, playlist: PlaylistCreateRequest):
    try:
        db = request.app.state.db
        collection_name = "Playlists"

        playlist_doc: Dict[str, Any] = playlist.model_dump()
        inserted_id = await insert_documents(db, collection_name, playlist_doc)

        return {"message": "Playlist created", "playlist_id": str(inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create playlist: {e}")


@playlists_router.post("/get_playlists")
async def read_playlists(request: Request, email: GetPlaylistsRequest):
    try:
        db = request.app.state.db
        collection_name = "Playlists"
        query = {"email": email.email}
        playlists = await query_collection(db, collection_name, query)

        # Convert ObjectId to string
        for playlist in playlists:
            if "_id" in playlist:
                playlist["_id"] = str(playlist["_id"])

        return {"message": f"{len(playlists)} playlists found for {email}", "playlists": playlists}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find playlists: {e}")


@playlists_router.post("/modify_playlist")
async def update_playlist():
    pass


@playlists_router.post("/delete_playlist")
async def delete_playlist():
    pass
