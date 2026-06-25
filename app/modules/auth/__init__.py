
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/")
async def read_auth():
    return {"module": "auth"}
