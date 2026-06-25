# Paw World — Backend TODO List

Build checklist for the monolith FastAPI app, ordered so each module is
built after the modules it depends on (Auth/User before things that need a
`user_id`, Cat Profile before Healthcare/Breeding, Posts before
Likes/Comments/Bookmarks, etc.).

---

## Phase 0 — Repo & infra scaffolding

- [ ] Initialize repo, `.gitignore`, `README.md`
- [ ] Write `.env.example` (`DATABASE_URL`, `REDIS_URL`, `MONGO_URL`,
      `ELASTICSEARCH_URL`, `JWT_SECRET`, `POSTGRES_PASSWORD`)
- [ ] Write `Dockerfile`
- [ ] Write `requirements.txt` (fastapi, uvicorn, sqlalchemy[asyncio],
      asyncpg, alembic, pydantic-settings, redis, motor, elasticsearch,
      python-jose, passlib)
- [ ] Write `docker-compose.yml` (postgres, redis, mongo, elasticsearch, api)
- [ ] Write `docker-compose.override.yml` (hot reload, mounted volume)
- [ ] Write `Makefile` (`make up`, `make migrate`, `make logs`, `make test`)
- [ ] Confirm `docker compose up` boots all five containers cleanly

## Phase 1 — Core app shell

- [ ] `app/core/config.py` — single `Settings(BaseSettings)`
- [ ] `app/core/security.py` — JWT decode/verify dependency
      (`get_current_user`), shared across modules
- [ ] `app/db/postgres.py` — async engine + `get_db()` dependency
- [ ] `app/db/redis.py` — singleton redis client factory
- [ ] `app/db/mongo.py` — singleton motor client factory (lazy connect)
- [ ] `app/db/elastic.py` — singleton AsyncElasticsearch client factory (lazy connect)
- [ ] `app/db/base.py` — Declarative `Base`
- [ ] `app/main.py` — bare `FastAPI()` app, healthcheck route (`GET /health`)
- [ ] `alembic.ini` + `alembic/env.py` pointed at `app.db.base.Base.metadata`
- [ ] Confirm `alembic revision --autogenerate` runs with zero tables (sanity check)

## Phase 2 — Modules

For each module: `models.py` (skip if no Postgres tables) → `schemas.py` →
`crud.py`/`service.py` → `routes.py` → wire into `app/main.py` → tests.

### 1. Auth
- [ ] `models.py`: `users_auth`, `refresh_tokens`, `password_reset_tokens`
- [ ] `schemas.py`: register/login/token/forgot-reset request+response models
- [ ] `security.py`: password hashing, access/refresh token creation
- [ ] `crud.py`: create user, get by email, store/revoke refresh token
- [ ] `routes.py`: register, login, logout, refresh-token, forgot/reset-password, `GET /me`
- [ ] Alembic migration `0001_auth`
- [ ] Tests: register, login, bad password, expired/revoked token, refresh flow

### 2. User
- [ ] `models.py`: `users`, `follows`, `blocks`
- [ ] `schemas.py`, `crud.py` (list/get/update/delete user, follow/unfollow, block/unblock)
- [ ] `routes.py`: full set incl. followers/following/cats/blocked
- [ ] Migration `0002_user`
- [ ] Tests: follow/unfollow idempotency, block prevents follow, soft constraints

### 3. Profile
- [ ] `models.py`: `profiles` (1:1 with `users`)
- [ ] `routes.py`: get/update profile, avatar/banner upload
- [ ] Decide + implement media storage for avatar/banner (S3-compatible bucket or local volume)
- [ ] Migration `0003_profile`
- [ ] Tests: profile auto-created on registration, avatar upload validation

### 4. Posts
- [ ] `models.py`: `posts`
- [ ] `cache.py`: `post:{id}` + `user:{id}:recent_posts` via shared Redis client
- [ ] `routes.py`: CRUD + list by user
- [ ] Migration `0004_posts`
- [ ] Tests: cache hit/miss path, ownership check on update/delete

### 5. Likes
- [ ] `models.py`: `likes` (ledger)
- [ ] `cache.py`: `post:{id}:like_count`, `post:{id}:liked_by` (Redis)
- [ ] `routes.py`: like/unlike, list likers
- [ ] Background/async job (or write-through) to keep ledger and Redis in sync
- [ ] Migration `0005_likes`
- [ ] Tests: double-like no-ops, count consistency between Postgres and Redis

### 6. Comments
- [ ] `models.py`: `comments` (self-referencing `parent_comment_id`)
- [ ] `routes.py`: create/list/update/delete, reply
- [ ] Recursive CTE (or app-level tree build) for nested replies
- [ ] Migration `0006_comments`
- [ ] Tests: nested reply depth, soft delete hides body but keeps thread shape

### 7. Feed
- [ ] `service.py`: `ZADD`/`ZRANGE` helpers against shared Redis client
- [ ] Fan-out-on-write (or fan-out-on-read) job triggered from Posts module on new post
- [ ] `routes.py`: feed, trending, explore
- [ ] Tests: feed ordering, trending score recalculation

### 8. Stories
- [ ] `service.py`: Redis `EXPIRE`-backed story storage + viewer set
- [ ] Optional `models.py` + migration `0007_stories_log` if keeping permanent log
- [ ] `routes.py`: create/list/get/delete, mark viewed
- [ ] Tests: TTL expiry behavior, viewer dedup

### 9. Search
- [ ] `service.py`: AsyncElasticsearch query builder per entity type
- [ ] Index definitions: `users_idx`, `posts_idx`, `hotels_idx`, `products_idx`,
      `vets_idx`, `rescue_listings_idx`, `breeders_idx`
- [ ] Indexer/sync job (CDC or simple polling) from Postgres → ES per entity
- [ ] `routes.py`: cross-entity search, per-entity search, `filters?type=`
- [ ] Tests: facet filtering, typo tolerance, filters endpoint returns live values

### 10. Hashtags
- [ ] `models.py`: `hashtags`, `post_hashtags`
- [ ] `cache.py`: `hashtags:trending` ZSET
- [ ] Hashtag parsing on post create (Posts module → Hashtags module call)
- [ ] `routes.py`: get tag, get tag's posts
- [ ] Migration `0008_hashtags`
- [ ] Tests: parsing edge cases (case sensitivity, duplicates, unicode)

### 11. Bookmarks
- [ ] `models.py`: `bookmarks`
- [ ] `routes.py`: save/unsave, list saved
- [ ] Migration `0009_bookmarks`
- [ ] Tests: unique constraint on `(user_id, post_id)`

### 12. Cat Profile
- [ ] `models.py`: `cats`, `cat_photos`
- [ ] `routes.py`: CRUD, list by user, photo upload/delete
- [ ] Migration `0010_cat_profile`
- [ ] Tests: ownership checks, photo limit per cat (if any)

### 13. Hotel & Booking
- [ ] `models.py`: `hotels`, `hotel_availability`, `bookings`
- [ ] Add `EXCLUDE USING gist` constraint on `(hotel_id, daterange)` to prevent double-booking
- [ ] `routes.py`: hotel CRUD, availability, booking CRUD, cancel, status update
- [ ] Migration `0011_hotel_booking`
- [ ] Tests: overlapping booking rejected, cancel restores availability

### 14. Healthcare
- [ ] `models.py`: `appointments`, `health_records`, `vaccinations`, `vets`
- [ ] `routes.py`: appointments CRUD/status, health-records, vaccinations, vets list/get
- [ ] Migration `0012_healthcare`
- [ ] Tests: appointment status transitions, vet specialty filter

### 15. Marketplace
- [ ] `models.py`: `products`, `orders`, `order_items`
- [ ] `cache.py`: `cart:{user_id}` Redis hash with TTL
- [ ] `routes.py`: product CRUD, cart CRUD, order create/list/status
- [ ] Stock decrement logic on order confirm (transactional)
- [ ] Migration `0013_marketplace`
- [ ] Tests: cart → order promotion, stock can't go negative, price snapshot on order_items

### 16. Cat Breeding
- [ ] `models.py`: `breeding_profiles`, `breeding_matches`
- [ ] `routes.py`: profile CRUD, match-request, list matches, status update
- [ ] Migration `0014_cat_breeding`
- [ ] Tests: match status transitions, can't match a profile with itself

### 17. Rescue Network
- [ ] `models.py`: `rescue_organizations`, `rescue_listings`, `rescue_applications`, `rescue_donations`
- [ ] `routes.py`: orgs CRUD, listings CRUD, applications CRUD/status, donations
- [ ] Migration `0015_rescue_network`
- [ ] Tests: listing status flips to `pending`/`adopted` correctly, org verification gate (if required)

### 18. Reviews & Ratings
- [ ] `models.py`: `reviews` (polymorphic `target_type`/`target_id`)
- [ ] Rating aggregation job/query (update `hotels.rating_avg` etc., or compute on read)
- [ ] `routes.py`: create/list/update/delete, filter by target
- [ ] Migration `0016_reviews_ratings`
- [ ] Tests: one review per user per target (if enforced), rating range 1–5

### 19. Reports & Moderation
- [ ] `models.py`: `reports` (with JSONB `metadata`)
- [ ] `routes.py`: create report, list, update status
- [ ] Migration `0017_reports_moderation`
- [ ] Tests: polymorphic target validation, status workflow

### 20. Messaging
- [ ] `schemas.py`: `conversations`, `messages` document shapes (Pydantic, no ORM)
- [ ] `service.py`: motor queries against shared Mongo client
- [ ] Mongo index: `{conversation_id: 1, sent_at: -1}`
- [ ] `routes.py`: list/create conversations, list/send messages, mark read
- [ ] Tests: pagination on message history, read_by dedup

### 21. Payments
- [ ] `models.py`: `payments`, `refunds`, `payment_methods`
- [ ] Integrate payment provider SDK (Stripe or similar) — checkout + webhook handling
- [ ] `routes.py`: checkout, get payment, refund, payment-methods CRUD
- [ ] Migration `0018_payments`
- [ ] Tests: webhook idempotency, refund can't exceed payment amount, no raw card data stored

### 22. Notifications
- [ ] `schemas.py`: `notifications` document shape (Mongo)
- [ ] `models.py`: `devices` (Postgres), `notification_preferences` (Postgres or Mongo — pick one)
- [ ] `cache.py`: `notif:{user_id}:unread_count` Redis counter
- [ ] Mongo index: `{user_id: 1, created_at: -1}`
- [ ] `routes.py`: list, mark read, preferences get/update, device register/delete
- [ ] Event hooks from other modules (new follower, booking confirmed, order shipped, new message) → create notification
- [ ] Migration `0019_notifications_devices`
- [ ] Tests: unread count sync on read, per-type preference suppression

## Phase 3 — Cross-cutting

- [ ] Wire every module's router into `app/main.py` with correct prefixes/tags
- [ ] Confirm full `alembic upgrade head` runs clean from empty DB
- [ ] Global exception handlers (404/422/500 shapes consistent across all modules)
- [ ] Request logging / correlation ID middleware
- [ ] Rate limiting on auth endpoints (login, forgot-password)
- [ ] CORS config
- [ ] Seed script for local dev (sample users, cats, posts, products)

## Phase 4 — Testing & CI

- [ ] `pytest` config + test DB fixture (separate test Postgres schema or testcontainers)
- [ ] Run full test suite locally via `make test`
- [ ] CI pipeline: lint (ruff/flake8) → type-check (mypy, optional) → tests → build image
- [ ] Smoke test: spin up full `docker compose`, hit `/health`, run a basic auth → post → like flow end-to-end

## Phase 5 — Deployment

- [ ] Production `.env` (secrets manager, not committed)
- [ ] Decide hosting target (single VM, ECS/Fargate, Railway/Render, etc.)
- [ ] Migration step in deploy pipeline (`alembic upgrade head` before app restart)
- [ ] Backups for Postgres + Mongo
- [ ] Basic monitoring/alerting (uptime, error rate, DB connection pool saturation)

## Phase 6 — Polish

- [ ] OpenAPI docs reviewed (`/docs`) — tags, descriptions, example payloads
- [ ] README updated with setup/run instructions
- [ ] Revisit "Where you could simplify" trade-offs from the DB design doc once
      real usage data exists (e.g. drop Mongo for JSONB if Messaging/Notifications
      never need true document flexibility)