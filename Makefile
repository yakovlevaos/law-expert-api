# .env is deliberately NOT included here: make strips everything after a `#`
# and expands `$`, which silently mangles generated secrets. django-environ
# reads the file itself, so only the few shell targets below need a value out
# of it.
.DEFAULT_GOAL := help
MANAGE := uv run python src/manage.py
DUMP_FILE ?= ./volumes/dump_$(shell date +%d%m%y).sql
POSTGRES_USER := $(or $(shell sed -n 's/^POSTGRES_USER=//p' .env 2>/dev/null),postgres)

help:  ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

deps:  ## Install all dependencies, including the dev group
	uv sync

lock:  ## Refresh uv.lock
	uv lock

up:  ## Start the full production stack
	docker compose --profile prod up -d --build

up_db:  ## Start only the development database
	docker compose --profile dev up -d

down:  ## Stop every service
	docker compose --profile prod --profile dev down

dev:  ## Run the development server
	$(MANAGE) runserver

migrate:  ## Create and apply migrations
	$(MANAGE) makemigrations
	$(MANAGE) migrate

test:  ## Run the test suite
	$(MANAGE) test apps

lint:  ## Check formatting, lint rules and types
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check

fmt:  ## Auto-format and auto-fix
	uv run ruff format .
	uv run ruff check --fix .

types:  ## Type-check with ty
	uv run ty check

check_deploy:  ## Run Django's production readiness checklist
	# ALLOWED_HOSTS is mandatory once DEBUG is off, so the target supplies a
	# placeholder rather than requiring it in the development .env.
	DEBUG=false ALLOWED_HOSTS=$${ALLOWED_HOSTS:-example.com} $(MANAGE) check --deploy

dump:  ## Dump the database to $(DUMP_FILE)
	docker exec -i genesis-postgres pg_dump --username $(POSTGRES_USER) genesis > $(DUMP_FILE)

restore:  ## Restore the database from $(DUMP_FILE)
	cat $(DUMP_FILE) | docker exec -i genesis-postgres psql -U $(POSTGRES_USER) --dbname=genesis

.PHONY: help deps lock up up_db down dev migrate test lint fmt types check_deploy dump restore
