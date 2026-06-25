
from fastapi import APIRouter

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

@router.get("/")
async def read_marketplace():
    return {"module": "marketplace"}
