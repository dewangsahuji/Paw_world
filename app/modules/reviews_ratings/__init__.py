
from fastapi import APIRouter

router = APIRouter(prefix="/reviews_ratings", tags=["Reviews Ratings"])

@router.get("/")
async def read_reviews_ratings():
    return {"module": "reviews_ratings"}
