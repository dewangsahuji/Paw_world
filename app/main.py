
from fastapi import FastAPI

from app.core.config import settings
from app.modules import (
    auth,
    user,
    profile,
    posts,
    likes,
    comments,
    feed,
    stories,
    search,
    hashtags,
    bookmarks,
    cat_profile,
    hotel_booking,
    healthcare,
    marketplace,
    cat_breeding,
    rescue_network,
    reviews_ratings,
    reports_moderation,
    messaging,
    payments,
    notifications,
)

app = FastAPI(title="paw-world", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(profile.router)
app.include_router(posts.router)
app.include_router(likes.router)
app.include_router(comments.router)
app.include_router(feed.router)
app.include_router(stories.router)
app.include_router(search.router)
app.include_router(hashtags.router)
app.include_router(bookmarks.router)
app.include_router(cat_profile.router)
app.include_router(hotel_booking.router)
app.include_router(healthcare.router)
app.include_router(marketplace.router)
app.include_router(cat_breeding.router)
app.include_router(rescue_network.router)
app.include_router(reviews_ratings.router)
app.include_router(reports_moderation.router)
app.include_router(messaging.router)
app.include_router(payments.router)
app.include_router(notifications.router)
