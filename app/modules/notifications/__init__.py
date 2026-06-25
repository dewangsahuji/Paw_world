
from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/")
async def read_notifications():
    return {"module": "notifications"}
