
from fastapi import APIRouter

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.get("/")
async def read_payments():
    return {"module": "payments"}
