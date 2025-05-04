from fastapi import APIRouter

from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/upload")
async def upload_songs():
    pass

@router.post("/queue_analysis_job")
async def queue_analysis_job():
    pass