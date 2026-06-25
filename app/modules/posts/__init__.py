
from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.get("/")
async def read_posts():
    return {"module": "posts"}
