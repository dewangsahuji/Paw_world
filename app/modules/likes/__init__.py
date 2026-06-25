
from fastapi import APIRouter

router = APIRouter(prefix="/likes", tags=["Likes"])

@router.get("/")
async def read_likes():
    return {"module": "likes"}
