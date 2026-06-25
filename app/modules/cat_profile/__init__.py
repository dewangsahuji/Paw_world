
from fastapi import APIRouter

router = APIRouter(prefix="/cat_profile", tags=["Cat Profile"])

@router.get("/")
async def read_cat_profile():
    return {"module": "cat_profile"}
