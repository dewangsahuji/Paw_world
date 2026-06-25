
from fastapi import APIRouter

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/")
async def read_user():
    return {"module": "user"}
