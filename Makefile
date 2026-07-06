.PHONY: install dev test lint format typecheck up down

install:
	pip install -r requirements-dev.txt

dev:
	uvicorn src.interfaces.http.app:app --reload

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src

up:
	docker compose up --build

down:
	docker compose down
