
from fastapi import APIRouter

router = APIRouter(prefix="/reports_moderation", tags=["Reports Moderation"])

@router.get("/")
async def read_reports_moderation():
    return {"module": "reports_moderation"}
