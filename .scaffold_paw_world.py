from pathlib import Path
from textwrap import dedent

root = Path(r"c:\Users\dewan\Coding\Project\paw-world")
root.mkdir(parents=True, exist_ok=True)

modules = [
    "auth",
    "user",
    "profile",
    "posts",
    "likes",
    "comments",
    "feed",
    "stories",
    "search",
    "hashtags",
    "bookmarks",
    "cat_profile",
    "hotel_booking",
    "healthcare",
    "marketplace",
    "cat_breeding",
    "rescue_network",
    "reviews_ratings",
    "reports_moderation",
    "messaging",
    "payments",
    "notifications",
]

file_contents = {
    "docker-compose.yml": dedent("""
        version: "3.9"
        services:
          app:
            build: .
            command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
            ports:
              - "8000:8000"
            volumes:
              - ./app:/app
            env_file:
              - .env
            depends_on:
              - postgres
              - redis
              - mongo
              - elastic
          postgres:
            image: postgres:15-alpine
            restart: unless-stopped
            environment:
              POSTGRES_USER: app
              POSTGRES_PASSWORD: password
              POSTGRES_DB: pawworld
            ports:
              - "5432:5432"
            volumes:
              - postgres_data:/var/lib/postgresql/data
          redis:
            image: redis:7-alpine
            ports:
              - "6379:6379"
          mongo:
            image: mongo:6.0
            ports:
              - "27017:27017"
          elastic:
            image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
            environment:
              - discovery.type=single-node
              - ES_JAVA_OPTS=-Xms512m -Xmx512m
            ports:
              - "9200:9200"
        volumes:
          postgres_data:
        """),
    "docker-compose.override.yml": dedent("""
        version: "3.9"
        services:
          app:
            command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
            volumes:
              - ./app:/app
            environment:
              - PYTHONUNBUFFERED=1
        """),
    ".env.example": dedent("""
        APP_ENV=development
        APP_DEBUG=true
        DATABASE_URL=postgresql+asyncpg://app:password@postgres:5432/pawworld
        REDIS_URL=redis://redis:6379/0
        MONGO_URL=mongodb://mongo:27017
        ELASTICSEARCH_URL=http://elastic:9200
        SECRET_KEY=changeme
        """),
    "README.md": dedent("""
        # paw-world

        This repository contains a scaffold for a single FastAPI application with shared database clients and a modular service layout.

        ## Structure

        - `app/` - application source code
        - `app/core/` - configuration and security utilities
        - `app/db/` - shared database client factories
        - `app/modules/` - service modules with routers
        - `alembic/` - database migration configuration
        - `gateway/` - optional TLS / reverse proxy configuration

        ## Quickstart

        1. Copy `.env.example` to `.env` and customize values.
        2. Build and start the stack:
           ```bash
           docker-compose up --build
           ```
        3. Open http://localhost:8000

        ## Management

        - `make up` - start containers
        - `make migrate` - run Alembic migrations
        - `make logs` - follow container logs
        """),
    "Makefile": dedent("""
        .PHONY: up down migrate logs

        up:
        	docker-compose up -d --build

        down:
        	docker-compose down

        migrate:
        	docker-compose run --rm app alembic upgrade head

        logs:
        	docker-compose logs -f
        """),
    "Dockerfile": dedent("""
        FROM python:3.12-slim

        WORKDIR /app

        COPY requirements.txt ./
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        EXPOSE 8000

        CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """),
    "requirements.txt": dedent("""
        fastapi>=0.111.0
        uvicorn[standard]>=0.23.0
        SQLAlchemy[asyncio]>=2.0.0
        asyncpg>=0.27.0
        alembic>=1.12.0
        pydantic>=2.8.0
        python-dotenv>=1.0.0
        motor>=4.0.0
        redis>=5.0.0
        elastic-transport>=8.11.0
        python-jose[cryptography]>=3.3.0
        """),
    "alembic.ini": dedent("""
        [alembic]
        script_location = alembic
        sqlalchemy.url = driver://user:pass@localhost/dbname

        [loggers]
        keys = root,sqlalchemy,alembic

        [handlers]
        keys = console

        [formatters]
        keys = generic

        [logger_root]
        level = WARN
        handlers = console
        qualname =

        [logger_sqlalchemy]
        level = WARN
        handlers = console
        qualname = sqlalchemy.engine
        propagate = 0

        [logger_alembic]
        level = INFO
        handlers = console
        qualname = alembic
        propagate = 0

        [handler_console]
        class = StreamHandler
        args = (sys.stdout,)
        level = NOTSET
        formatter = generic

        [formatter_generic]
        format = %(levelname)-5.5s [%(name)s] %(message)s
        datefmt = %Y-%m-%d %H:%M:%S
        """),
    "alembic/env.py": dedent("""
        import os
        import sys
        from logging.config import fileConfig

        from sqlalchemy import engine_from_config
        from sqlalchemy import pool
        from alembic import context

        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

        from app.core.config import settings
        from app.db.base import Base

        config = context.config
        fileConfig(config.config_file_name)
        target_metadata = Base.metadata

        def run_migrations_offline():
            url = settings.database_url
            context.configure(
                url=url,
                target_metadata=target_metadata,
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
            )
            with context.begin_transaction():
                context.run_migrations()

        def run_migrations_online():
            connectable = engine_from_config(
                config.get_section(config.config_ini_section),
                prefix="sqlalchemy.",
                poolclass=pool.NullPool,
            )
            with connectable.connect() as connection:
                context.configure(connection=connection, target_metadata=target_metadata)
                with context.begin_transaction():
                    context.run_migrations()

        if context.is_offline_mode():
            run_migrations_offline()
        else:
            run_migrations_online()
        """),
    "alembic/versions/0001_initial.py": dedent("""
        from alembic import op
        import sqlalchemy as sa

        revision = "0001_initial"
        down_revision = None
        branch_labels = None
        depends_on = None

        def upgrade():
            pass

        def downgrade():
            pass
        """),
    "gateway/nginx.conf": dedent("""
        events {}

        http {
            server {
                listen 443 ssl;
                server_name localhost;

                ssl_certificate /etc/nginx/certs/fullchain.pem;
                ssl_certificate_key /etc/nginx/certs/privkey.pem;

                location / {
                    proxy_pass http://app:8000;
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                    proxy_set_header X-Forwarded-Proto $scheme;
                }
            }
        }
        """),
    "app/__init__.py": "",
    "app/main.py": dedent("""
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
        """),
    "app/core/config.py": dedent("""
        from pydantic import BaseSettings, AnyUrl

        class Settings(BaseSettings):
            app_env: str = "development"
            debug: bool = True
            database_url: str = "postgresql+asyncpg://app:password@postgres:5432/pawworld"
            redis_url: str = "redis://redis:6379/0"
            mongo_url: str = "mongodb://mongo:27017"
            elasticsearch_url: AnyUrl = "http://elastic:9200"
            secret_key: str = "changeme"

            class Config:
                env_file = ".env"
                case_sensitive = True

        settings = Settings()
        """),
    "app/core/security.py": dedent("""
        from fastapi import Depends, HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

        security = HTTPBearer()

        def jwt_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
            token = credentials.credentials
            if not token or token == "dummy":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )
            return {"sub": "user-id"}
        """),
    "app/db/base.py": dedent("""
        from sqlalchemy.orm import declarative_base

        Base = declarative_base()
        """),
    "app/db/postgres.py": dedent("""
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import settings

        engine = create_async_engine(settings.database_url, future=True, echo=settings.debug)
        AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

        async def get_db():
            async with AsyncSessionLocal() as session:
                yield session
        """),
    "app/db/redis.py": dedent("""
        from redis.asyncio import Redis

        from app.core.config import settings

        def get_redis() -> Redis:
            return Redis.from_url(settings.redis_url)
        """),
    "app/db/mongo.py": dedent("""
        from motor.motor_asyncio import AsyncIOMotorClient

        from app.core.config import settings

        def get_mongo_client() -> AsyncIOMotorClient:
            return AsyncIOMotorClient(settings.mongo_url)
        """),
    "app/db/elastic.py": dedent("""
        from elasticsearch import AsyncElasticsearch

        from app.core.config import settings

        def get_elastic_client() -> AsyncElasticsearch:
            return AsyncElasticsearch(hosts=[settings.elasticsearch_url])
        """),
    "app/tests/__init__.py": "",
    "app/tests/test_auth.py": dedent("""
        def test_health_endpoint():
            assert True
        """),
    "app/tests/test_user.py": dedent("""
        def test_dummy_user():
            assert True
        """),
}

for rel_path, content in file_contents.items():
    file_path = root / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

for module_name in modules:
    pkg = root / "app" / "modules" / module_name
    pkg.mkdir(parents=True, exist_ok=True)
    route_name = module_name.replace("_", " ").title()
    content = dedent(f"""
        from fastapi import APIRouter

        router = APIRouter(prefix="/{module_name}", tags=["{route_name}"])

        @router.get("/")
        async def read_{module_name.replace("-", "_")}():
            return {{"module": "{module_name}"}}
        """
    )
    (pkg / "__init__.py").write_text(content, encoding="utf-8")

print("scaffold-complete")
