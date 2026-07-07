"""Shared database connection helper (used by the migration runner and ingestion jobs)."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Load .env from the repo root once on import. override=True so this project's DATABASE_URL
# wins over any ambient DATABASE_URL in the shell environment (e.g. another project's Supabase).
load_dotenv(_REPO_ROOT / ".env", override=True)


def database_url() -> str:
    """Return the libpq connection URL from DATABASE_URL, normalised for psycopg."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Create .env from .env.example (see CLAUDE.md)."
        )
    # Accept a SQLAlchemy-style URL too, but hand libpq a plain postgresql:// URL.
    return url.replace("postgresql+psycopg://", "postgresql://")


def connect() -> psycopg.Connection:
    """Open a new psycopg connection to the GridScout database."""
    return psycopg.connect(database_url())
