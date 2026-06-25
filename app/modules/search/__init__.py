
from fastapi import APIRouter

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
async def read_search():
    return {"module": "search"}
