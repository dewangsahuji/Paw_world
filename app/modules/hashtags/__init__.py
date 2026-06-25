
from fastapi import APIRouter

router = APIRouter(prefix="/hashtags", tags=["Hashtags"])

@router.get("/")
async def read_hashtags():
    return {"module": "hashtags"}
