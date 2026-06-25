
.PHONY: up down migrate logs

up:
	docker-compose up -d --build

down:
	docker-compose down

migrate:
	docker-compose run --rm app alembic upgrade head

logs:
	docker-compose logs -f
