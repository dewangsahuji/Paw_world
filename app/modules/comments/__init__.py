
from fastapi import APIRouter

router = APIRouter(prefix="/comments", tags=["Comments"])

@router.get("/")
async def read_comments():
    return {"module": "comments"}
