
from fastapi import APIRouter

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/")
async def read_profile():
    return {"module": "profile"}
