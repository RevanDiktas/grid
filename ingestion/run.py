"""Dispatch entry point: ``python -m ingestion.run <source>`` (via ``make ingest SOURCE=...``)."""

from __future__ import annotations

import sys
from collections.abc import Callable

from ingestion import capaciteitskaart

# Registered ingestion jobs. Each new source adds one entry (build-ingestion-job skill).
JOBS: dict[str, Callable[[], None]] = {
    capaciteitskaart.SOURCE: capaciteitskaart.main,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in JOBS:
        known = ", ".join(sorted(JOBS)) or "(none)"
        print(f"usage: python -m ingestion.run <source>\n  known sources: {known}", file=sys.stderr)
        return 2
    JOBS[argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
