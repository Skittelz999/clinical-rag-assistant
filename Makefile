.PHONY: up start start-detached stop down reset-db logs backend-test backend-lint frontend-install frontend-dev frontend-typecheck frontend-build lint test

up:
	docker compose up --build

start: up

start-detached:
	docker compose up --build -d

stop:
	docker compose down

down:
	docker compose down

reset-db:
	docker compose down -v

logs:
	docker compose logs -f

backend-test:
	cd backend && python -m pytest

backend-lint:
	cd backend && python -m ruff check src tests

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-build:
	cd frontend && npm run build

lint: backend-lint frontend-typecheck

test: backend-test frontend-typecheck
