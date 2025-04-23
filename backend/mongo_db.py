import os
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    client = AsyncIOMotorClient(MONGO_URI)
    app.state.mongo_client = client
    app.state.db = client[DB_NAME]
    logging.info("✅ Connected to MongoDB")

    yield

    # Shutdown
    client.close()
    logging.info("🛑 MongoDB connection closed")
