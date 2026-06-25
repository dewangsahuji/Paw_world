
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

def get_mongo_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(settings.mongo_url)
