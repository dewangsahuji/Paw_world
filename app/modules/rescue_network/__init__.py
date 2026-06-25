
from fastapi import APIRouter

router = APIRouter(prefix="/rescue_network", tags=["Rescue Network"])

@router.get("/")
async def read_rescue_network():
    return {"module": "rescue_network"}
