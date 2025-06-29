import numpy as np

from fastapi import APIRouter, Request, HTTPException

from models import GetEmbeddingsRequest
from selecta.yamnet_model import yamnet_model

yamnet_router = APIRouter()


@yamnet_router.post("/get_embeddings")
async def get_embeddings(request: Request, audio: GetEmbeddingsRequest):
    try:
        # Convert list to NumPy array
        audio_array = np.array(audio.audio, dtype=np.float32)

        # Run through YamNet model to extract embeddings
        outputs_dict = yamnet_model(audio_array)
        yamnet_embeddings = outputs_dict["output_1"].numpy()

        return {
            "message": "Extracted yamnet embeddings",
            "yamnet_embeddings": yamnet_embeddings.tolist(),  # Convert for JSON
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract yamnet embeddings: {e}")
