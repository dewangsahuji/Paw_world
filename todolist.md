# Paw World — Build To-Do List

**Order:** Database/infra setup → Auth Service → everything else, easiest first.
"Easiest" = fewest tables, fewest data stores touched, least business logic
(overlap constraints, multi-DB writes, financial correctness, etc.).

---

## Phase 0 — Repo & Infra Scaffolding
- [ ] Create top-level repo: `docker-compose.yml`, `docker-compose.override.yml`, `.env.example`, `.gitignore`, `README.md`, `Makefile`
- [ ] Create `gateway/nginx.conf` (routes `/api/*` to each service)
- [ ] Create `shared/pawworld_shared` local package
  - [ ] `config.py` — base `Settings` (pydantic-settings)
  - [ ] `security.py` — shared JWT decode/verify dependency
  - [ ] `db/postgres.py` — async SQLAlchemy session factory
  - [ ] `db/redis.py` — redis client factory
  - [ ] `db/mongo.py` — motor client factory
  - [ ] `schemas/base.py` — shared Pydantic base (e.g. `PaginatedResponse`)
- [ ] `make up` / `make migrate` / `make logs SERVICE=...` targets in Makefile

## Phase 1 — Database Setup
- [ ] Spin up **Postgres** container (single instance, schema-per-service)
- [ ] Spin up **Redis** container
- [ ] Spin up **MongoDB** container
- [ ] Spin up **Elasticsearch** container (needed later for Search, but bring it up now so compose is complete)
- [ ] `infra/postgres-init/01-auth.sql` ... one init script per Postgres-backed service, creating its schema
- [ ] `infra/elasticsearch-init/create-indices.sh` (can stay empty/stubbed until Search phase)
- [ ] Decide now: JSONB-on-Postgres vs. real Mongo for Reports & Notifications (see simplification note in db design doc) — pick one path so you don't build both

## Phase 2 — Auth Service (Template A, Postgres)
- [ ] Scaffold `services/auth-service` from Template A
- [ ] Tables: `users_auth`, `refresh_tokens`, `password_reset_tokens` (+ Alembic migration `0001_initial`)
- [ ] Password hashing + token creation in `core/security.py`
- [ ] Endpoints:
  - [ ] `POST /api/auth/register`
  - [ ] `POST /api/auth/login`
  - [ ] `POST /api/auth/logout`
  - [ ] `POST /api/auth/refresh-token`
  - [ ] `POST /api/auth/forgot-password`
  - [ ] `POST /api/auth/reset-password`
  - [ ] `GET /api/auth/me`
- [ ] (Optional) Redis denylist for revoked JWTs
- [ ] Wire `shared/pawworld_shared/security.py` to use this service's JWT secret/claims for every other service to verify

---

## Phase 3 — Bookmarks Service (Postgres) — simplest
- [ ] Table: `bookmarks` (composite PK `user_id, post_id`)
- [ ] Endpoints: `POST /api/posts/{post_id}/save`, `DELETE /api/posts/{post_id}/save`, `GET /api/saved-posts`

## Phase 4 — Profile Service (Postgres)
- [ ] Table: `profiles` (1:1 with `users`)
- [ ] Avatar/banner upload handling (file storage decision: local volume / S3-compatible)
- [ ] Endpoints: `GET/PUT /api/profile`, `POST /api/profile/avatar`, `POST /api/profile/banner`

## Phase 5 — User Service (Postgres) — Follow System merged in
- [ ] Tables: `users`, `follows`, `blocks`
- [ ] Endpoints:
  - [ ] `GET/PUT/DELETE /api/users/{user_id}`, `GET /api/users`
  - [ ] `GET /api/users/{user_id}/followers`, `/following`, `/cats`
  - [ ] `POST/DELETE /api/users/{user_id}/follow`
  - [ ] `POST/DELETE /api/users/{user_id}/block`, `GET /api/users/blocked`

## Phase 6 — Cat Profile Service (Postgres)
- [ ] Tables: `cats`, `cat_photos`
- [ ] Endpoints: full CRUD on `/cats`, `GET /cats/user/{user_id}`, photo upload/delete

## Phase 7 — Likes Service (Postgres ledger + Redis counters)
- [ ] Table: `likes` (durable ledger)
- [ ] Redis keys: `post:{post_id}:like_count`, `post:{post_id}:liked_by`
- [ ] Write-through logic: increment Redis + insert Postgres row together (decide sync vs async)
- [ ] Endpoints: like/unlike a post, `GET /api/posts/{post_id}/likes`

## Phase 8 — Hashtags Service (Postgres + Redis trending)
- [ ] Tables: `hashtags`, `post_hashtags`
- [ ] Redis key: `hashtags:trending` (ZSET, `ZINCRBY` on use)
- [ ] Endpoints: `GET /api/hashtags/{tag}`, `GET /api/hashtags/{tag}/posts`

## Phase 9 — Posts Service (Postgres + Redis cache)
- [ ] Table: `posts`
- [ ] Redis cache: `post:{post_id}` (JSON, TTL), `user:{user_id}:recent_posts` (LIST)
- [ ] Cache-aside read pattern + invalidation on update/delete
- [ ] Endpoints: full CRUD on `/api/posts`, `GET /api/posts/user/{user_id}`

## Phase 10 — Comments Service (Postgres)
- [ ] Table: `comments` (self-referencing `parent_comment_id`, soft delete via `deleted_at`)
- [ ] Recursive CTE for thread reconstruction
- [ ] Endpoints: create/list/update/delete comment, `POST /api/comments/{comment_id}/reply`

## Phase 11 — Stories Service (Redis TTL, optional Postgres log)
- [ ] Redis keys: `story:{story_id}` (TTL 24h), `user:{user_id}:stories`, `story:{story_id}:viewers`
- [ ] Optional `stories_log` table if you want permanent analytics
- [ ] Endpoints: create/list/get/delete story, `POST /api/stories/{story_id}/view`

## Phase 12 — Feed Service (Redis) — depends on Posts + Follows
- [ ] Redis keys: `feed:{user_id}` (ZSET), `feed:trending`, `feed:explore:{user_id}`
- [ ] Decide fan-out-on-write vs fan-out-on-read based on expected follower distribution
- [ ] Endpoints: `GET /api/feed`, `/api/feed/trending`, `/api/feed/explore`

## Phase 13 — Reviews & Ratings Service (Postgres)
- [ ] Table: `reviews` (polymorphic `target_type` + `target_id`, composite index)
- [ ] Aggregate avg rating per target (`GROUP BY`, optionally cached in Redis)
- [ ] Endpoints: full CRUD on `/reviews` with `target_type`/`target_id` filters

## Phase 14 — Reports & Moderation Service (Postgres, JSONB)
- [ ] Table: `reports` (polymorphic `target_type/target_id`, `metadata JSONB`)
- [ ] Endpoints: `POST /reports`, `GET /reports`, `PUT /reports/{report_id}/status`

## Phase 15 — Healthcare Service (Postgres) — vaccinations + medical records consolidated
- [ ] Tables: `appointments`, `health_records`, `vaccinations`, `vets`
- [ ] Endpoints:
  - [ ] appointments CRUD + status update
  - [ ] `POST /health-records`, `GET /health-records/{cat_id}`
  - [ ] `POST /vaccinations`, `GET /vaccinations/{cat_id}`
  - [ ] `GET /vets`, `GET /vets/{vet_id}`

## Phase 16 — Cat Breeding Service (Postgres)
- [ ] Tables: `breeding_profiles`, `breeding_matches` (status workflow: pending/accepted/declined)
- [ ] Endpoints: profiles CRUD, `POST /breeding/match-request`, `GET /breeding/matches`, status update

## Phase 17 — Rescue Network Service (Postgres) — 4 related entities
- [ ] Tables: `rescue_organizations`, `rescue_listings`, `rescue_applications`, `rescue_donations`
- [ ] Endpoints: orgs CRUD, listings CRUD, applications CRUD + status, donations create/list

## Phase 18 — Hotel & Booking Service (Postgres) — transactional
- [ ] Tables: `hotels`, `hotel_availability`, `bookings`
- [ ] `EXCLUDE USING gist` constraint on `(hotel_id, daterange)` to prevent double-booking
- [ ] Endpoints: hotels CRUD + availability, bookings CRUD + cancel + status update

## Phase 19 — Marketplace Service (Postgres + Redis cart) — inventory + checkout logic
- [ ] Tables: `products`, `orders`, `order_items`
- [ ] Redis key: `cart:{user_id}` (HASH, TTL for abandoned carts)
- [ ] Cart → order "promotion" logic at checkout (stock decrement, snapshot unit price)
- [ ] Endpoints: products CRUD, cart CRUD, orders CRUD + status update

## Phase 20 — Payments Service (Postgres) — financial ACID, ties into Orders/Bookings
- [ ] Tables: `payments`, `refunds`, `payment_methods` (tokenized only, never raw card data)
- [ ] Integrate with a real/sandbox payment processor for `provider_ref`
- [ ] Endpoints: `POST /payments/checkout`, `GET /payments/{id}`, `POST /payments/{id}/refund`, payment-methods CRUD

## Phase 21 — Notifications Service (MongoDB + Redis + Postgres) — 3 stores in one service
- [ ] Collection: `notifications` (variable `payload` by `type`)
- [ ] Table: `notification_preferences` (or Mongo — pick per your Phase 1 decision)
- [ ] Table: `devices` (Postgres, push tokens)
- [ ] Redis key: `notif:{user_id}:unread_count`
- [ ] Hook up triggers from other services (new follower, booking confirmed, order shipped, new message)
- [ ] Endpoints: list/read notifications, preferences get/set, device register/unregister

## Phase 22 — Messaging Service (MongoDB) — flagged as v2, build once core flows are stable
- [ ] Collections: `conversations`, `messages` (index `{conversation_id: 1, sent_at: -1}`)
- [ ] Endpoints: list/create conversations, list/post messages, mark message read

## Phase 23 — Search Service (Elasticsearch) — last, since it indexes everyone else's data
- [ ] Indices: `users_idx`, `posts_idx`, `hotels_idx`, `products_idx`, `vets_idx`, `rescue_listings_idx`, `breeders_idx`
- [ ] Build the CDC/sync (or outbox) job(s) that populate ES from each service's Postgres tables
- [ ] Endpoints:
  - [ ] `GET /api/search` (cross-entity, `type=`)
  - [ ] `GET /api/search/users`, `/posts`, `/hashtags`
  - [ ] `GET /api/search/hotels`, `/products`, `/vets`, `/rescue-listings`, `/breeders`
  - [ ] `GET /api/search/filters?type=` (facet aggregation per resource)

---

## Cross-cutting, do whenever convenient
- [ ] Service ports `800{n}` convention (auth=8001 ... notifications=8022), gateway on 80
- [ ] `.env` namespacing per service (`AUTH_DATABASE_URL`, `POSTS_DATABASE_URL`, shared `JWT_SECRET`)
- [ ] Per-service `tests/` (at minimum: auth, then whichever service you're actively building)
- [ ] Decide image/file storage strategy once (used by Profile avatars/banners, Cat photos, Posts/Stories media)