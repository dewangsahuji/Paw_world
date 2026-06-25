# Paw World — Database Design Reference

Maps each of the 22 services in the API reference to a database, using only
PostgreSQL, MongoDB, and Redis as a baseline (your current stack), with
Elasticsearch called out only where it earns its place over PG full-text
search. One database per service is the default for clean REST/microservice
boundaries — shared instances are noted explicitly where polyglot-per-service
would be overkill.

---

## TL;DR table

| # | Service | Database | Why |
|---|---|---|---|
| 1 | Auth | **PostgreSQL** | Relational, ACID, credentials |
| 2 | User | **PostgreSQL** | Relational (follows/blocks = edges) |
| 3 | Profile | **PostgreSQL** | 1:1 with User, structured fields |
| 4 | Posts | **PostgreSQL** + **Redis** (cache) | Relational core, hot reads cached |
| 5 | Likes | **Redis** (counts) + **PostgreSQL** (ledger) | High write volume, need durability too |
| 6 | Comments | **PostgreSQL** | Threaded relational data |
| 7 | Feed | **Redis** | Precomputed timelines, ephemeral/derived |
| 8 | Stories | **Redis** (TTL) + **PostgreSQL** (optional log) | Natural expiry fits Redis TTL |
| 9 | Search | **Elasticsearch** | Multi-entity full-text + faceted filters |
| 10 | Hashtags | **PostgreSQL** + **Redis** (trending) | Relational tag table, hot counts cached |
| 11 | Bookmarks | **PostgreSQL** | Simple relational join table |
| 12 | Cat Profile | **PostgreSQL** | Structured, relational to User |
| 13 | Hotel & Booking | **PostgreSQL** | Transactional, needs ACID for bookings |
| 14 | Healthcare | **PostgreSQL** | Medical records — relational integrity matters |
| 15 | Marketplace | **PostgreSQL** + **Redis** (cart) | Orders = transactional; cart = ephemeral |
| 16 | Cat Breeding | **PostgreSQL** | Structured profiles + matches |
| 17 | Rescue Network | **PostgreSQL** | Relational orgs/listings/applications |
| 18 | Reviews & Ratings | **PostgreSQL** | Relational, aggregatable ratings |
| 19 | Reports & Moderation | **PostgreSQL** + **MongoDB** (flexible payload) | Structured workflow, variable report metadata |
| 20 | Messaging | **MongoDB** | Variable message shape, high write throughput |
| 21 | Payments | **PostgreSQL** | Strict ACID, financial ledger |
| 22 | Notifications | **MongoDB** + **Redis** (unread counts) | Varied notification payloads, fast badge counts |

**Cross-cutting:** Search aggregates data that lives in PostgreSQL elsewhere — Elasticsearch
here is a read-optimized index fed by CDC/sync jobs, not the source of truth.

---

## Reasoning, service by service

### 1. Auth Service → PostgreSQL
Credentials, tokens, password resets. This is the textbook case for strong
consistency and ACID guarantees. Never put auth data in something eventually
consistent. Use PG for `users_auth`, `refresh_tokens`, `password_reset_tokens`.
Consider Redis only as a denylist/blacklist cache for revoked JWTs (fast
lookup on every request) — not as the source of truth.

### 2. User Service → PostgreSQL
Followers/following/blocks are graph edges between two integers — a relational
table with a composite key (`follower_id, followed_id`) handles this cleanly
and lets you do `JOIN`s for "users you follow who also follow X" type queries
later. MongoDB would work too, but you'd be reinventing relational joins in
application code for no benefit since the data is genuinely tabular.

### 3. Profile Service → PostgreSQL
Effectively a 1:1 extension of the `users` table (bio, avatar URL, banner
URL). Keep it in the same PG instance as User Service, possibly literally the
same table if your service boundary allows it — splitting it into its own
database only makes sense if Profile truly scales/deploys independently.

### 4. Posts Service → PostgreSQL (+ Redis cache)
Posts are structured (author, caption, media URLs, timestamps) and relational
to Users, Comments, Likes. Use PG as source of truth. Cache hot posts (viral
posts, a user's most recent N posts) in Redis to take read pressure off PG —
this is the standard cache-aside pattern, not a replacement database.

### 5. Likes Service → Redis (counters) + PostgreSQL (ledger)
Likes are extremely high write volume relative to their data size, and you
usually only need the count plus "did this user like this post" — both are
great Redis use cases (`INCR` for counts, a `SET` per post for membership
checks). But if you need to know *who* liked something or want durability
across a Redis restart, keep a PostgreSQL table as the durable ledger and let
Redis serve as the fast-path cache/counter, synced async or written-through.

### 6. Comments Service → PostgreSQL
Threaded replies are a classic adjacency-list or path-based relational
pattern (`parent_comment_id` self-reference). PG handles recursive CTEs for
thread reconstruction well. Avoid MongoDB here unless you specifically want
to embed reply trees as nested documents — that gets awkward once threads get
deep or comments need independent edit/delete.

### 7. Feed Service → Redis
The feed itself isn't really "data" — it's a precomputed, denormalized view
(a sorted set of post IDs per user, score = timestamp or rank). This is the
canonical Redis use case: `ZADD`/`ZRANGE` on a per-user feed key, fan-out on
write or fan-out on read depending on your follower-count distribution. The
underlying posts still live in PostgreSQL; Feed Service just stores
"which post IDs, in what order, for which user."

### 8. Stories Service → Redis (+ optional PostgreSQL log)
Stories expire after 24h by definition — that's a TTL, which Redis gives you
natively (`EXPIRE`) instead of needing a cron job to delete rows. Store story
metadata + media reference in Redis with TTL. If you need permanent analytics
("how many stories did this user post all-time") keep a lightweight append-only
log in PostgreSQL that Redis writes through to.

### 9. Search Service → Elasticsearch
This is the one place Elasticsearch is worth learning, and the API reference
itself signals why: it's not just `users` search, it's faceted, multi-field
filtering across **five different entity types** (hotels, products, vets,
rescue listings, breeders) with price ranges, ratings, amenities, age ranges,
size, etc. — plus a typo-tolerant free-text `q=` param and a cross-entity
search bar. PostgreSQL full-text search (`tsvector`) can technically do
single-field text search, but you'd be hand-rolling faceting, relevance
scoring, and multi-index aggregation that Elasticsearch gives you out of the
box. Treat ES as a **read replica/index**, not your source of truth — write to
PostgreSQL (or each service's own DB) first, then sync into ES via change-data-capture
or an outbox pattern. `GET /api/search/filters?type=` (valid facet values) is
also a natural ES aggregation query.

### 10. Hashtags Service → PostgreSQL (+ Redis for trending)
Hashtag-to-post mapping is a simple relational join table. "Trending hashtags"
is a different problem — that's a leaderboard, which is Redis sorted sets
again (`ZINCRBY` on each use, `ZREVRANGE` to get top N). Keep the canonical
tag table in PG, keep the live trending counter in Redis.

### 11. Bookmarks Service → PostgreSQL
A user-to-post saved join table. Nothing here needs anything beyond a simple
relational table with a unique constraint on `(user_id, post_id)`.

### 12. Cat Profile Service → PostgreSQL
Structured fields (name, breed, birthdate, owner), relational to User and to
Photos. Keep medical data out of here per your own note — it already lives in
Healthcare Service.

### 13. Hotel & Booking Service → PostgreSQL
Bookings need transactional guarantees — you don't want two people double-booking
the same hotel slot due to a race condition, and you'll want
`check_in`/`check_out` overlap queries, which relational date-range constraints
handle well (`EXCLUDE USING gist` in PG is purpose-built for this). This is a
case where ACID really matters: cancellations, status changes, and
availability all need to be consistent.

### 14. Healthcare Service → PostgreSQL
Medical/vaccination records benefit from strict referential integrity (every
record must point to a real cat, every appointment to a real vet) and from
being queryable/auditable. This is sensitive data where "eventually
consistent" is not an acceptable trade-off.

### 15. Marketplace Service → PostgreSQL (+ Redis for cart)
Orders and inventory need ACID — stock decrements, order status transitions,
and payment linkage all need consistency. The shopping cart, however, is
ephemeral, per-session state that doesn't need full durability guarantees —
Redis (hash per user/cart, TTL for abandoned carts) is the standard pattern
here, with the cart only being "promoted" into a durable PostgreSQL `orders`
row at checkout.

### 16. Cat Breeding Service → PostgreSQL
Structured breeding profiles and a match-request/match workflow with status
transitions — relational data with clear referential integrity needs
(profile → match → status). Nothing here is document-shaped or
high-throughput enough to need anything else.

### 17. Rescue Network Service → PostgreSQL
Organizations, listings, applications, and donations are all structured,
relational, and benefit from joins (e.g., "all pending applications for org
X's listings"). Keep this in the same relational mold as Hotel/Marketplace.

### 18. Reviews & Ratings Service → PostgreSQL
`target_type`/`target_id` is a polymorphic association — PG handles this fine
with a `(target_type, target_id)` composite index. You'll also want to
aggregate average ratings per target, which is a straightforward `GROUP BY`
in PG (optionally materialized/cached in Redis if read volume is heavy).

### 19. Reports & Moderation Service → PostgreSQL (+ MongoDB optional)
The workflow itself (report → status: pending/reviewed/actioned) is
structured and benefits from relational status tracking and auditability —
PostgreSQL. The *content* of a report can vary a lot depending on what's
being reported (a post, a comment, a user, a product) — if you want to
attach flexible, type-specific metadata to each report without a wide table
full of nullable columns, a MongoDB side-document (keyed by report ID) is a
reasonable place for that variable payload. Don't over-engineer this one
early — a single PG table with a JSONB `metadata` column may be all you need
before reaching for a second database.

### 20. Messaging Service → MongoDB
Messages are an actual case where document storage is more natural than
relational: a conversation is a list of messages with potentially varying
shape (text, media, replies, read receipts), very high write throughput, and
you almost always query "give me messages for conversation X, in order" —
not relational joins across other entities. MongoDB's document model fits
this 1:1, and its horizontal write scaling fits chat-style workloads better
than PG would at scale. This was correctly flagged as v2 — worth designing
the schema (`conversation_id`, `sender_id`, `body`, `sent_at`, `read_by[]`)
before you build, since chat data models are easy to get wrong on a first pass.

### 21. Payments Service → PostgreSQL
No debate here — financial data needs ACID transactions, period. Refunds,
payment status, and stored payment methods (tokenized, never raw card data)
all belong in PostgreSQL. If you ever introduce an event-sourced ledger for
auditability, that's still typically backed by PG, not Mongo or Redis.

### 22. Notifications Service → MongoDB (+ Redis for counts)
Notification payloads vary a lot by type (new follower vs. booking confirmed
vs. order shipped vs. new message) — each type has different fields, which
is a natural fit for MongoDB's flexible schema instead of a PG table with
many nullable columns or a generic JSONB blob. The **unread badge count**,
though, is a classic Redis counter (`INCR`/`DECR` per user) since you'll
hit that on every app open and don't want to run a `COUNT(*)` query for it.
Device tokens for push (`/notifications/devices`) are simple enough to live
relationally in PostgreSQL if you'd rather not stand up Mongo just for this
service — see "Where you could simplify" below.

---

## Table & document definitions, by service

Field-level schema for every table/collection implied by the endpoints.
Types are written as PostgreSQL types unless marked Mongo/Redis. `PK` =
primary key, `FK` = foreign key. Timestamps (`created_at`, `updated_at`) are
included wherever a resource is mutable; omitted on pure join/log tables
where they're not useful.

### 1. Auth Service (PostgreSQL)

**`users_auth`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL (bcrypt/argon2) |
| is_verified | BOOLEAN | default false |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`refresh_tokens`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users_auth.id |
| token_hash | VARCHAR(255) | NOT NULL, indexed |
| expires_at | TIMESTAMPTZ | |
| revoked | BOOLEAN | default false |
| created_at | TIMESTAMPTZ | |

**`password_reset_tokens`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users_auth.id |
| token_hash | VARCHAR(255) | NOT NULL, indexed |
| expires_at | TIMESTAMPTZ | |
| used_at | TIMESTAMPTZ | nullable |

---

### 2. User Service (PostgreSQL)

**`users`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| username | VARCHAR(50) | UNIQUE, NOT NULL |
| display_name | VARCHAR(100) | |
| email | VARCHAR(255) | UNIQUE, FK-equivalent to users_auth.email |
| is_active | BOOLEAN | default true |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`follows`**
| Field | Type | Notes |
|---|---|---|
| follower_id | UUID | FK → users.id, composite PK |
| followed_id | UUID | FK → users.id, composite PK |
| created_at | TIMESTAMPTZ | |

**`blocks`**
| Field | Type | Notes |
|---|---|---|
| blocker_id | UUID | FK → users.id, composite PK |
| blocked_id | UUID | FK → users.id, composite PK |
| created_at | TIMESTAMPTZ | |

---

### 3. Profile Service (PostgreSQL)

**`profiles`**
| Field | Type | Notes |
|---|---|---|
| user_id | UUID | PK, FK → users.id |
| bio | TEXT | nullable |
| avatar_url | VARCHAR(500) | nullable |
| banner_url | VARCHAR(500) | nullable |
| location | VARCHAR(255) | nullable |
| updated_at | TIMESTAMPTZ | |

---

### 4. Posts Service (PostgreSQL, hot reads cached in Redis)

**`posts`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| caption | TEXT | nullable |
| media_urls | TEXT[] | array of media URLs |
| created_at | TIMESTAMPTZ | indexed (feed ordering) |
| updated_at | TIMESTAMPTZ | |

**Redis cache keys**
| Key pattern | Type | Notes |
|---|---|---|
| `post:{post_id}` | STRING (JSON) | cached serialized post, TTL |
| `user:{user_id}:recent_posts` | LIST | recent post IDs |

---

### 5. Likes Service (Redis counters + PostgreSQL ledger)

**`likes`** (PostgreSQL — durable ledger)
| Field | Type | Notes |
|---|---|---|
| post_id | UUID | FK → posts.id, composite PK |
| user_id | UUID | FK → users.id, composite PK |
| created_at | TIMESTAMPTZ | |

**Redis keys**
| Key pattern | Type | Notes |
|---|---|---|
| `post:{post_id}:like_count` | STRING (int) | `INCR`/`DECR` |
| `post:{post_id}:liked_by` | SET | user_ids, for membership check |

---

### 6. Comments Service (PostgreSQL)

**`comments`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| post_id | UUID | FK → posts.id |
| user_id | UUID | FK → users.id |
| parent_comment_id | UUID | FK → comments.id, nullable (self-ref for replies) |
| body | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |
| deleted_at | TIMESTAMPTZ | nullable (soft delete) |

---

### 7. Feed Service (Redis)

**Redis keys**
| Key pattern | Type | Notes |
|---|---|---|
| `feed:{user_id}` | ZSET | member = post_id, score = timestamp/rank |
| `feed:trending` | ZSET | member = post_id, score = engagement score |
| `feed:explore:{user_id}` | ZSET | personalized explore ranking |

---

### 8. Stories Service (Redis with TTL, optional PostgreSQL log)

**Redis keys**
| Key pattern | Type | Notes |
|---|---|---|
| `story:{story_id}` | STRING (JSON) | `{user_id, media_url, created_at}`, `EXPIRE` 24h |
| `user:{user_id}:stories` | SET | active story_ids, TTL matches |
| `story:{story_id}:viewers` | SET | viewer user_ids |

**`stories_log`** (PostgreSQL, optional, append-only)
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| media_url | VARCHAR(500) | |
| posted_at | TIMESTAMPTZ | |

---

### 9. Search Service (Elasticsearch — indexes fed from PostgreSQL)

**Index: `users_idx`** — username, display_name, area, bio (analyzed text)
**Index: `posts_idx`** — caption (analyzed), hashtags, user_id, created_at
**Index: `hotels_idx`** — name, area, pet_type, price, rating, amenities[] (keyword), check_in/out availability
**Index: `products_idx`** — name, category, pet_type, price, in_stock (boolean)
**Index: `vets_idx`** — name, area, specialty, pet_type
**Index: `rescue_listings_idx`** — name, area, pet_type, breed, age, gender, size
**Index: `breeders_idx`** — name, area, pet_type, breed

Each index mirrors the source-of-truth table's filterable fields, denormalized
flat (no joins in ES) for fast faceted queries and aggregations.

---

### 10. Hashtags Service (PostgreSQL + Redis trending)

**`hashtags`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| tag | VARCHAR(100) | UNIQUE, NOT NULL, indexed |
| created_at | TIMESTAMPTZ | |

**`post_hashtags`**
| Field | Type | Notes |
|---|---|---|
| post_id | UUID | FK → posts.id, composite PK |
| hashtag_id | UUID | FK → hashtags.id, composite PK |

**Redis keys**
| Key pattern | Type | Notes |
|---|---|---|
| `hashtags:trending` | ZSET | member = tag, score = use count |

---

### 11. Bookmarks Service (PostgreSQL)

**`bookmarks`**
| Field | Type | Notes |
|---|---|---|
| user_id | UUID | FK → users.id, composite PK |
| post_id | UUID | FK → posts.id, composite PK |
| created_at | TIMESTAMPTZ | |

---

### 12. Cat Profile Service (PostgreSQL)

**`cats`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id (owner) |
| name | VARCHAR(100) | NOT NULL |
| breed | VARCHAR(100) | nullable |
| birthdate | DATE | nullable |
| gender | VARCHAR(20) | nullable |
| bio | TEXT | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`cat_photos`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| cat_id | UUID | FK → cats.id |
| photo_url | VARCHAR(500) | NOT NULL |
| uploaded_at | TIMESTAMPTZ | |

---

### 13. Hotel & Booking Service (PostgreSQL)

**`hotels`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| owner_id | UUID | FK → users.id |
| name | VARCHAR(255) | NOT NULL |
| area | VARCHAR(255) | indexed |
| pet_type | VARCHAR(50) | default 'cat' |
| price_per_night | NUMERIC(10,2) | |
| rating_avg | NUMERIC(3,2) | denormalized, updated from reviews |
| amenities | TEXT[] | array |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`hotel_availability`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| hotel_id | UUID | FK → hotels.id |
| date | DATE | |
| available_slots | INTEGER | |

**`bookings`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| hotel_id | UUID | FK → hotels.id |
| user_id | UUID | FK → users.id |
| cat_id | UUID | FK → cats.id |
| check_in | DATE | |
| check_out | DATE | EXCLUDE USING gist on (hotel_id, daterange) to prevent overlap |
| status | VARCHAR(20) | enum: pending/confirmed/cancelled/completed |
| total_price | NUMERIC(10,2) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

### 14. Healthcare Service (PostgreSQL)

**`appointments`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| cat_id | UUID | FK → cats.id |
| vet_id | UUID | FK → vets.id |
| scheduled_at | TIMESTAMPTZ | |
| status | VARCHAR(20) | enum: pending/confirmed/completed/cancelled |
| created_at | TIMESTAMPTZ | |

**`health_records`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| cat_id | UUID | FK → cats.id |
| vet_id | UUID | FK → vets.id, nullable |
| diagnosis | TEXT | nullable |
| notes | TEXT | nullable |
| recorded_at | TIMESTAMPTZ | |

**`vaccinations`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| cat_id | UUID | FK → cats.id |
| vaccine_name | VARCHAR(255) | |
| administered_at | DATE | |
| next_due_at | DATE | nullable |

**`vets`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| area | VARCHAR(255) | indexed |
| specialty | VARCHAR(100) | |
| pet_type | VARCHAR(50) | default 'cat' |
| created_at | TIMESTAMPTZ | |

---

### 15. Marketplace Service (PostgreSQL, cart in Redis)

**`products`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| seller_id | UUID | FK → users.id |
| name | VARCHAR(255) | NOT NULL |
| category | VARCHAR(100) | indexed |
| pet_type | VARCHAR(50) | default 'cat' |
| price | NUMERIC(10,2) | |
| in_stock | BOOLEAN | default true |
| stock_qty | INTEGER | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`orders`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| status | VARCHAR(20) | enum: pending/paid/shipped/delivered/cancelled |
| total_price | NUMERIC(10,2) | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`order_items`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| order_id | UUID | FK → orders.id |
| product_id | UUID | FK → products.id |
| quantity | INTEGER | |
| unit_price | NUMERIC(10,2) | snapshot at purchase time |

**Redis cart keys**
| Key pattern | Type | Notes |
|---|---|---|
| `cart:{user_id}` | HASH | field = product_id, value = quantity, TTL for abandoned carts |

---

### 16. Cat Breeding Service (PostgreSQL)

**`breeding_profiles`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| cat_id | UUID | FK → cats.id |
| user_id | UUID | FK → users.id |
| area | VARCHAR(255) | indexed |
| pet_type | VARCHAR(50) | default 'cat' |
| breed | VARCHAR(100) | indexed |
| description | TEXT | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`breeding_matches`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| requester_profile_id | UUID | FK → breeding_profiles.id |
| target_profile_id | UUID | FK → breeding_profiles.id |
| status | VARCHAR(20) | enum: pending/accepted/declined |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

### 17. Rescue Network Service (PostgreSQL)

**`rescue_organizations`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| area | VARCHAR(255) | indexed |
| description | TEXT | nullable |
| contact_email | VARCHAR(255) | |
| verified | BOOLEAN | default false |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`rescue_listings`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → rescue_organizations.id |
| name | VARCHAR(100) | NOT NULL |
| pet_type | VARCHAR(50) | default 'cat' |
| breed | VARCHAR(100) | nullable, indexed |
| age_months | INTEGER | nullable |
| gender | VARCHAR(20) | nullable |
| size | VARCHAR(20) | nullable |
| area | VARCHAR(255) | indexed |
| description | TEXT | nullable |
| status | VARCHAR(20) | enum: available/pending/adopted |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`rescue_applications`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| listing_id | UUID | FK → rescue_listings.id |
| applicant_id | UUID | FK → users.id |
| status | VARCHAR(20) | enum: pending/approved/rejected |
| application_text | TEXT | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`rescue_donations`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| org_id | UUID | FK → rescue_organizations.id |
| donor_id | UUID | FK → users.id |
| amount | NUMERIC(10,2) | |
| created_at | TIMESTAMPTZ | |

---

### 18. Reviews & Ratings Service (PostgreSQL)

**`reviews`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| reviewer_id | UUID | FK → users.id |
| target_type | VARCHAR(20) | enum: hotel/vet/product/seller/breeder |
| target_id | UUID | polymorphic, no FK constraint (composite index with target_type) |
| rating | SMALLINT | 1-5, CHECK constraint |
| body | TEXT | nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

### 19. Reports & Moderation Service (PostgreSQL, optional JSONB/Mongo for metadata)

**`reports`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| reporter_id | UUID | FK → users.id |
| target_type | VARCHAR(20) | enum: post/comment/user/product/listing |
| target_id | UUID | polymorphic |
| reason | VARCHAR(100) | |
| status | VARCHAR(20) | enum: pending/reviewed/actioned/dismissed |
| metadata | JSONB | flexible type-specific payload (or move to Mongo if heavily used) |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

### 20. Messaging Service (MongoDB)

**Collection: `conversations`**
```json
{
  "_id": "ObjectId",
  "participant_ids": ["uuid", "uuid"],
  "created_at": "ISODate",
  "last_message_at": "ISODate"
}
```

**Collection: `messages`**
```json
{
  "_id": "ObjectId",
  "conversation_id": "ObjectId",
  "sender_id": "uuid",
  "body": "string",
  "media_url": "string | null",
  "sent_at": "ISODate",
  "read_by": ["uuid"]
}
```
Index: `{conversation_id: 1, sent_at: -1}` for paginated message history.

---

### 21. Payments Service (PostgreSQL)

**`payments`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| order_id | UUID | FK → orders.id, nullable (could pay for booking instead) |
| booking_id | UUID | FK → bookings.id, nullable |
| amount | NUMERIC(10,2) | |
| currency | VARCHAR(3) | ISO 4217 |
| status | VARCHAR(20) | enum: pending/succeeded/failed/refunded |
| provider_ref | VARCHAR(255) | external processor transaction ID |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

**`refunds`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| payment_id | UUID | FK → payments.id |
| amount | NUMERIC(10,2) | |
| reason | TEXT | nullable |
| created_at | TIMESTAMPTZ | |

**`payment_methods`**
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| provider_token | VARCHAR(255) | tokenized reference, never raw card data |
| brand | VARCHAR(20) | nullable, e.g. visa/mastercard |
| last4 | VARCHAR(4) | nullable |
| is_default | BOOLEAN | default false |
| created_at | TIMESTAMPTZ | |

---

### 22. Notifications Service (MongoDB + Redis counts)

**Collection: `notifications`**
```json
{
  "_id": "ObjectId",
  "user_id": "uuid",
  "type": "new_follower | booking_confirmed | order_shipped | new_message | ...",
  "payload": { "...varies by type" },
  "read": false,
  "created_at": "ISODate"
}
```
Index: `{user_id: 1, created_at: -1}`.

**`notification_preferences`** (PostgreSQL or Mongo, either works — relational
shape suggested if you'd rather not stand up Mongo just for this)
| Field | Type | Notes |
|---|---|---|
| user_id | UUID | PK, FK → users.id |
| email_enabled | BOOLEAN | default true |
| push_enabled | BOOLEAN | default true |
| per_type_settings | JSONB | e.g. `{"new_follower": true, "new_message": false}` |

**`devices`** (PostgreSQL)
| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| push_token | VARCHAR(500) | NOT NULL |
| platform | VARCHAR(20) | ios/android/web |
| registered_at | TIMESTAMPTZ | |

**Redis keys**
| Key pattern | Type | Notes |
|---|---|---|
| `notif:{user_id}:unread_count` | STRING (int) | `INCR`/`DECR`/reset on read |

---

## Where you could simplify (fewer moving parts)

Running 3-4 different database technologies across 22 microservices is a lot
of operational surface area for one team. Some honest trade-offs:

- **You could run almost everything in PostgreSQL alone** and only add Redis
  for caching/counters/feeds and Elasticsearch for the Search Service. Mongo's
  flexible-schema benefit (Messaging, Notifications, Reports) can be
  approximated with PG's `JSONB` columns, which give you flexible document-like
  storage *with* the option to add relational constraints and `JOIN`s later
  if you need them. Many teams ship chat/notifications on PG+JSONB without
  ever introducing Mongo.
- **One PostgreSQL instance, many schemas** is usually a better starting point
  than one PostgreSQL *database per service* — you get service-boundary
  isolation (one schema per service) without 15 separate Postgres clusters to
  patch, back up, and monitor. Split a schema into its own physical database
  only once that service's load actually demands independent scaling.
- **Redis is doing real work in 6 of these services** (Likes, Feed, Stories,
  Hashtags-trending, Cart, Notification counts) — that's the genuine
  high-value use of what you already know, more so than spreading into Mongo.
- **Elasticsearch is justified by one thing**: faceted multi-entity search
  with five different filter sets sharing common params (`area`, `pet_type`).
  If you trimmed Search Service down to plain keyword lookups, PG full-text
  search (`tsvector` + `GIN` index) would suffice and you could skip learning
  ES altogether for v1.

### A pragmatic v1 stack
1. **PostgreSQL** (schema-per-service) for everything structured/relational —
   that's 16 of the 22 services as-is.
2. **Redis** for caching, counters, feeds, carts, sessions, trending, and
   ephemeral TTL data (Stories) — layered on top of PG, not replacing it.
3. **MongoDB** introduced only when you actually hit the pain of variable-shape
   documents at scale (Messaging is the strongest case; Notifications/Reports
   can wait).
4. **Elasticsearch** introduced only when Search Service's faceted filtering
   needs outgrow what `tsvector` + `GIN` indexes in PG can comfortably do.

This lets you ship on the two databases you already know well, add Redis
everywhere it has a clear win, and treat Mongo/Elasticsearch as deliberate,
deferred additions rather than default choices per service.