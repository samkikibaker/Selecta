from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from contextlib import asynccontextmanager

from selecta.logger import generate_logger
from selecta.utils import MONGO_URI, DB

logger = generate_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    client = AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_client = client
    app.state.db = client[DB]
    logger.info("✅ Connected to MongoDB")

    yield

    # Shutdown
    client.close()
    logger.info("🛑 MongoDB connection closed")
