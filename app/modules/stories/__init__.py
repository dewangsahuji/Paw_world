
from fastapi import APIRouter

router = APIRouter(prefix="/stories", tags=["Stories"])

@router.get("/")
async def read_stories():
    return {"module": "stories"}
