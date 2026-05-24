.PHONY: up down logs backend-test backend-lint frontend-install frontend-dev

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backend-test:
	cd backend && pytest

backend-lint:
	cd backend && ruff check src tests

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev
