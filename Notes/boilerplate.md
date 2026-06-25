# Paw World — Backend Boilerplate (Monolith Scaffold)

Folder/file structure for a single deployable backend. Stack: **FastAPI +
Docker + Alembic**, **modular monolith** architecture — one process, one
container, one repo. All 22 domains live in the same codebase as
`app/modules/<domain>/` packages instead of separate services, but keep the
same internal seams so any module could be peeled back out into its own
service later without a rewrite.

---

## Module key — which backend each module uses

Same data-store choices as before; the only thing that changed is that
they're now all imported into one app instead of spread across 22
containers. Most modules are PostgreSQL-backed. A few don't touch Postgres
at all, so they have no `models.py` (no ORM tables to migrate).

| Module | Backend |
|---|---|
| 1. Auth | Postgres |
| 2. User | Postgres |
| 3. Profile | Postgres |
| 4. Posts | Postgres + Redis (cache) |
| 5. Likes | Postgres (ledger) + Redis (counters) |
| 6. Comments | Postgres |
| 7. Feed | **Redis only — no models.py** |
| 8. Stories | Redis + optional Postgres (log) |
| 9. Search | **Elasticsearch — no models.py** |
| 10. Hashtags | Postgres + Redis |
| 11. Bookmarks | Postgres |
| 12. Cat Profile | Postgres |
| 13. Hotel & Booking | Postgres |
| 14. Healthcare | Postgres |
| 15. Marketplace | Postgres + Redis |
| 16. Cat Breeding | Postgres |
| 17. Rescue Network | Postgres |
| 18. Reviews & Ratings | Postgres |
| 19. Reports & Moderation | Postgres (JSONB metadata) |
| 20. Messaging | **MongoDB — no models.py (plain Pydantic doc shapes)** |
| 21. Payments | Postgres |
| 22. Notifications | MongoDB + Redis + small Postgres table (`devices`) |

---

## Top-level repo tree

```
paw-world/
├── docker-compose.yml
├── docker-compose.override.yml      # local dev overrides (hot reload, mounted volume)
├── .env.example
├── .gitignore
├── README.md
├── Makefile                         # make up / make migrate / make logs
├── Dockerfile                       # single image for the whole app
├── requirements.txt                 # single dependency list for the whole app
├── alembic.ini
├── alembic/
│   ├── env.py                       # imports Base.metadata pulled from ALL modules
│   └── versions/
│       └── 0001_initial.py
│
├── gateway/                         # OPTIONAL now — only useful for TLS
│   └── nginx.conf                   # termination/static files, not service routing
│
└── app/
    ├── __init__.py
    ├── main.py                      # single FastAPI() app, includes all 22 routers
    │
    ├── core/
    │   ├── config.py                # ONE Settings(BaseSettings) for the whole app
    │   └── security.py              # JWT decode/verify dependency, used by every module
    │
    ├── db/                          # shared, singleton clients — created once, imported everywhere
    │   ├── base.py                  # Declarative Base + combined metadata for Alembic
    │   ├── postgres.py               # single async engine + get_db() dependency
    │   ├── redis.py                  # single redis client factory
    │   ├── mongo.py                  # single motor client factory
    │   └── elastic.py                # single AsyncElasticsearch client factory
    │
    ├── modules/
    │   ├── auth/
    │   ├── user/
    │   ├── profile/
    │   ├── posts/
    │   ├── likes/
    │   ├── comments/
    │   ├── feed/
    │   ├── stories/
    │   ├── search/
    │   ├── hashtags/
    │   ├── bookmarks/
    │   ├── cat_profile/
    │   ├── hotel_booking/
    │   ├── healthcare/
    │   ├── marketplace/
    │   ├── cat_breeding/
    │   ├── rescue_network/
    │   ├── reviews_ratings/
    │   ├── reports_moderation/
    │   ├── messaging/
    │   ├── payments/
    │   └── notifications/
    │
    └── tests/
        ├── test_auth.py
        ├── test_user.py
        └── ...                      # one test file per module, same names as before
```

No more `services/` array, no per-service `Dockerfile`/`requirements.txt`,
no `shared/` pip package — what used to be the shared package is now just
`app/core/` and `app/db/`, imported directly since everything is already in
the same process.

---

## Module pattern A — Postgres-backed module (most modules)

```
app/modules/auth/
├── __init__.py
├── models.py            # SQLAlchemy ORM models (users_auth, refresh_tokens, ...)
├── schemas.py           # Pydantic request/response models
├── crud.py              # DB access functions (create_user, get_by_email, ...)
├── security.py          # password hashing, token creation (auth-specific logic)
└── routes.py            # APIRouter with this module's endpoints
```

Modules that are polyglot (Posts, Likes, Hashtags, Marketplace,
Notifications) add a thin `cache.py` or `realtime.py` alongside `models.py`
that just imports the shared client from `app/db/redis.py` or
`app/db/mongo.py` — there's no need for each module to build its own client,
since there's only one Redis/Mongo connection for the whole app now.

## Module pattern B — Redis-only module (no models.py)

```
app/modules/feed/
├── __init__.py
├── schemas.py
├── service.py            # ZADD/ZRANGE helpers, uses app.db.redis client
└── routes.py
```

Stories follows this same shape, plus an *optional* `models.py` if you keep
the permanent analytics log in Postgres.

## Module pattern C — MongoDB module (no models.py / no ORM)

```
app/modules/messaging/
├── __init__.py
├── schemas.py            # plain Pydantic models describing document shape
├── service.py            # uses app.db.mongo client (motor)
└── routes.py
```

Notifications is the same shape, plus a small `models.py` + Postgres table
for `devices`, and a `service.py` using the shared Redis client for the
unread counter.

## Module pattern D — Elasticsearch module

```
app/modules/search/
├── __init__.py
├── schemas.py
├── service.py            # uses app.db.elastic client (AsyncElasticsearch)
└── routes.py              # cross-entity + per-entity search endpoints
```

---

## `app/main.py` — single entrypoint, every router included

```python
from fastapi import FastAPI

from app.modules.auth.routes import router as auth_router
from app.modules.user.routes import router as user_router
from app.modules.profile.routes import router as profile_router
from app.modules.posts.routes import router as posts_router
from app.modules.likes.routes import router as likes_router
from app.modules.comments.routes import router as comments_router
from app.modules.feed.routes import router as feed_router
from app.modules.stories.routes import router as stories_router
from app.modules.search.routes import router as search_router
from app.modules.hashtags.routes import router as hashtags_router
from app.modules.bookmarks.routes import router as bookmarks_router
from app.modules.cat_profile.routes import router as cat_profile_router
from app.modules.hotel_booking.routes import router as hotel_booking_router
from app.modules.healthcare.routes import router as healthcare_router
from app.modules.marketplace.routes import router as marketplace_router
from app.modules.cat_breeding.routes import router as cat_breeding_router
from app.modules.rescue_network.routes import router as rescue_router
from app.modules.reviews_ratings.routes import router as reviews_router
from app.modules.reports_moderation.routes import router as reports_router
from app.modules.messaging.routes import router as messaging_router
from app.modules.payments.routes import router as payments_router
from app.modules.notifications.routes import router as notifications_router

app = FastAPI(title="Paw World API")

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(profile_router, prefix="/api/profile", tags=["profile"])
app.include_router(posts_router, prefix="/api/posts", tags=["posts"])
app.include_router(likes_router, prefix="/api/posts", tags=["likes"])
app.include_router(comments_router, prefix="/api/posts", tags=["comments"])
app.include_router(feed_router, prefix="/api/feed", tags=["feed"])
app.include_router(stories_router, prefix="/api/stories", tags=["stories"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(hashtags_router, prefix="/api/hashtags", tags=["hashtags"])
app.include_router(bookmarks_router, prefix="/api", tags=["bookmarks"])
app.include_router(cat_profile_router, prefix="/cats", tags=["cats"])
app.include_router(hotel_booking_router, prefix="", tags=["hotels", "bookings"])
app.include_router(healthcare_router, prefix="", tags=["healthcare"])
app.include_router(marketplace_router, prefix="", tags=["marketplace"])
app.include_router(cat_breeding_router, prefix="/breeding", tags=["breeding"])
app.include_router(rescue_router, prefix="/rescue", tags=["rescue"])
app.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
app.include_router(messaging_router, prefix="", tags=["messaging"])
app.include_router(payments_router, prefix="", tags=["payments"])
app.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
```

Routes and request/response shapes are untouched from the API reference —
only *where the code lives* changed, not the URLs.

---

## `Dockerfile` (one image now, not 22)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## `requirements.txt` (one combined list)

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
alembic
pydantic-settings
redis
motor
elasticsearch
python-jose[cryptography]
passlib[bcrypt]
```

---

## `docker-compose.yml` skeleton

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: pawworld
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

  redis:
    image: redis:7
    ports: ["6379:6379"]

  mongo:
    image: mongo:7
    ports: ["27017:27017"]

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports: ["9200:9200"]

  api:
    build: .
    env_file: .env
    depends_on: [postgres, redis, mongo, elasticsearch]
    ports: ["8000:8000"]

volumes:
  pgdata:
```

One app container instead of 22. `make up` brings up the whole stack with a
single `docker compose up`; there's no more "spin up just auth-service and
its dependency" since the process isn't split — it's all-or-nothing now.
Mongo/Elasticsearch clients in `app/db/` should connect lazily (on first use,
not at startup) so the app doesn't crash-loop in dev if you haven't bothered
running those containers yet and aren't touching Messaging/Search/Notifications.

---

## Conventions worth locking in early

- **One Postgres database, one schema, no per-module schema separation.**
  Since every table already has a distinct name (`users_auth`, `users`,
  `profiles`, `posts`, `cats`, ...), there's no collision risk, so there's
  no need for `search_path` tricks anymore — that was only needed to keep
  22 separate Alembic histories from stepping on each other.
- **One Alembic history for the whole app.** `alembic/env.py` imports
  `Base.metadata` from `app/db/base.py`, which in turn imports every
  module's `models.py` so autogenerate sees all tables at once. Migrations
  run with a single `alembic upgrade head` — no `SERVICE=` argument needed.
- **`app/core` and `app/db` replace `shared/`.** JWT verification, the
  settings base class, and DB client factories are now just regular
  in-repo imports (`from app.db.postgres import get_db`) instead of an
  installable local package — there's no cross-repo boundary to maintain
  since it's all one codebase.
- **One `.env` file, one `Settings` class.** Namespacing per module
  (`AUTH_DATABASE_URL`, `POSTS_DATABASE_URL`, ...) is no longer needed since
  there's one `DATABASE_URL` for the one Postgres connection pool the whole
  app shares; keep `REDIS_URL`, `MONGO_URL`, `ELASTICSEARCH_URL`,
  `JWT_SECRET` as before.
- **One port, no gateway routing.** Everything is served on `:8000` by the
  single FastAPI app; `gateway/nginx.conf` is now optional and, if kept, is
  only for TLS termination or serving static files — not for routing `/api/auth`
  vs `/api/posts` to different upstreams, since there's only one upstream.
- **Cross-module calls are just function calls.** Anywhere a service used
  to make an HTTP call to another service (e.g. Likes checking if a Post
  exists), that becomes a direct Python import and function call between
  modules — faster, but worth being deliberate about which modules are
  allowed to import from which, so you don't end up with circular imports
  or a fully tangled ball of modules.

---

## What you gain vs. what you give up

**Gained:** one thing to build, test, and deploy; no network hops between
modules; no per-service Postgres/Alembic juggling; much simpler local dev
(`docker compose up` and you're done); easier to reason about a request
end-to-end since it's all one stack trace.

**Given up:** you can no longer deploy or scale one module independently
(e.g. scaling Feed or Search separately under load); a bug or crash in one
module can take down the whole app instead of just one service; the whole
team ships on the same release cadence.

Keeping the `app/modules/<domain>/` boundary (rather than one flat `app/`
folder) is what keeps this reversible — if any one module's load outgrows
the monolith later, it's a relatively mechanical extraction back into its
own service, since the module already owns its own models/schemas/routes
and doesn't reach into other modules' internals directly.

---

*Note: `docker-compose.yml`'s db containers, the API endpoint reference, and
the database-per-module choices in the Database Design Reference don't need
to change — those concern storage and routes, not deployment topology.
Only this file (the boilerplate/deploy structure) changes.*