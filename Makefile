.PHONY: up down logs restart-web restart-workers migrate lint test format

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f web worker beat

restart-web:
	docker compose restart web

restart-workers:
	docker compose restart worker beat

migrate:
	docker compose exec web alembic upgrade head

lint:
	ruff check .

test:
	pytest -q

format:
	black app tests
