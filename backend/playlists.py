from fastapi import APIRouter

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.post("/generate_playlist")  # i.e. given a song, build a playlist of size n
async def generate_playlist():
    pass


@router.post("/save_playlist")
async def save_playlist():
    pass


@router.post("/delete_playlist")
async def delete_playlist():
    pass


@router.post("/download_playlist")
async def save_playlist():
    pass
