
from fastapi import APIRouter

router = APIRouter(prefix="/feed", tags=["Feed"])

@router.get("/")
async def read_feed():
    return {"module": "feed"}
