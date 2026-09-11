PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install backend frontend up down lint test

install:
	bash ./install.sh

backend:
	cd backend && $(PIP) install -r requirements.txt

frontend:
	cd frontend && npm install

up:
	docker compose up -d --build

down:
	docker compose down -v

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

test:
	cd backend && pytest -q
	cd frontend && npm run test -- --run
