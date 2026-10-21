PYTHON ?= python

.PHONY: setup dev lint test e2e build audit
setup:
	$(PYTHON) -m venv backend/.venv
	backend/.venv/bin/pip install --require-hashes -r backend/requirements-dev.lock
	cd frontend && npm ci

dev:
	docker compose up --build

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy app
	cd frontend && npm run lint && npm run format:check

test:
	cd backend && .venv/bin/pytest
	cd frontend && npm test

e2e:
	cd frontend && npm run e2e

build:
	docker compose build

audit:
	cd backend && .venv/bin/pip-audit -r requirements.lock
	cd frontend && npm audit --audit-level=high
