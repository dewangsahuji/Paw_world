
from fastapi import APIRouter

router = APIRouter(prefix="/healthcare", tags=["Healthcare"])

@router.get("/")
async def read_healthcare():
    return {"module": "healthcare"}
