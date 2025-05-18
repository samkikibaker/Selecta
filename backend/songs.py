import json

from fastapi import APIRouter, HTTPException
from azure.identity.aio import DefaultAzureCredential
from azure.storage.queue.aio import QueueServiceClient
from passlib.context import CryptContext
from dotenv import load_dotenv

from models import QueueJobRequest

load_dotenv()

songs_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@songs_router.post("/queue_analysis_job")
async def queue_analysis_job(job: QueueJobRequest):
    try:
        queue_service_client = QueueServiceClient(
            account_url="https://saselecta.queue.core.windows.net/", credential=DefaultAzureCredential()
        )
        queue_client = queue_service_client.get_queue_client(queue="q-selecta")

        await queue_client.send_message(json.dumps({"email": job.email}))
        return {"message": "Email added to queue successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")
