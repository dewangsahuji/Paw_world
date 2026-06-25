
from fastapi import APIRouter

router = APIRouter(prefix="/bookmarks", tags=["Bookmarks"])

@router.get("/")
async def read_bookmarks():
    return {"module": "bookmarks"}
