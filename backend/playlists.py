from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from models import PlaylistCreateRequest, ReadPlaylistsRequest, PlaylistDeleteRequest
from selecta.mongo_db import insert_documents, query_collection, delete_documents

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


@playlists_router.post("/read_playlists")
async def read_playlists(request: Request, email: ReadPlaylistsRequest):
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


@playlists_router.post("/update_playlist")
async def update_playlist():
    pass


@playlists_router.post("/delete_playlist")
async def delete_playlist(request: Request, data: PlaylistDeleteRequest):
    try:
        db = request.app.state.db
        collection_name = "Playlists"
        query = {"name": data.name, "email": data.email}

        deleted_id = await delete_documents(db, collection_name, query)

        return {"message": "Playlist deleted", "playlist_id": str(deleted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete playlist: {e}")
