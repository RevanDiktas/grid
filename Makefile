# GridScout task runner — one command per common task (see CLAUDE.md "Commands").
SHELL := /bin/bash
UV := uv
COMPOSE := docker-compose
SOURCE ?=

# The repo lives on exFAT (no POSIX perms, case-insensitive), which cannot host a Python
# venv reliably. Keep the venv on the APFS disk-image (mounted by `make db-up`), same as the
# database — a real POSIX filesystem that physically lives on the Expansion drive.
export UV_PROJECT_ENVIRONMENT := /Volumes/gridscout-data/venv
export UV_LINK_MODE := copy

# Docker/Colima live on the same image; talk to Colima's socket with a clean config
# (avoids the stale docker-credential-desktop helper on the internal disk).
export DOCKER_HOST := unix:///Volumes/gridscout-data/colima/docker.sock
export DOCKER_CONFIG := /Volumes/gridscout-data/docker-config

.DEFAULT_GOAL := help
.PHONY: help setup db-up db-down migrate ingest serve report test check lint typecheck fmt

help:
	@echo "GridScout targets:"
	@echo "  make setup                 - db up (APFS image + colima + postgis), deps, migrate"
	@echo "  make db-up                 - create/mount APFS image, start colima, start postgis"
	@echo "  make db-down               - stop the postgis container"
	@echo "  make migrate               - apply db/migrations"
	@echo "  make ingest SOURCE=<name>  - run one ingestion job (e.g. capaciteitskaart)"
	@echo "  make test                  - pytest"
	@echo "  make check                 - ruff + mypy (RUN BEFORE EVERY COMMIT)"

setup: db-up
	$(UV) sync
	$(MAKE) migrate
	@echo "setup complete."

db-up:
	bash scripts/db-up.sh

db-down:
	-$(COMPOSE) down

migrate:
	$(UV) run python -m db.migrate

ingest:
	@test -n "$(SOURCE)" || { echo "usage: make ingest SOURCE=<name>"; exit 2; }
	$(UV) run python -m ingestion.run $(SOURCE)

serve:
	@echo "serve: api + web not built yet (out of scope this session)"; exit 1

report:
	@echo "report: generator not built yet (out of scope this session)"; exit 1

test:
	$(UV) run pytest -q

check: lint typecheck

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy -p ingestion -p db -p provenance

fmt:
	$(UV) run ruff format .
