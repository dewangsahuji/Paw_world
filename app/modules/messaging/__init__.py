
from fastapi import APIRouter

router = APIRouter(prefix="/messaging", tags=["Messaging"])

@router.get("/")
async def read_messaging():
    return {"module": "messaging"}
