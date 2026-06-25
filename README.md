
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
