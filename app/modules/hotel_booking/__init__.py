
from fastapi import APIRouter

router = APIRouter(prefix="/hotel_booking", tags=["Hotel Booking"])

@router.get("/")
async def read_hotel_booking():
    return {"module": "hotel_booking"}
