"""Machine-readable source registry with **licence metadata** — the enforceable single source
of truth for what each data source is and how it may be used.

This is authoritative in code; ``docs/data-sources.md`` is the human-readable mirror. Both
ingestion and the (future) report path import from here so licence rules are enforced
structurally, not by prose.

The operating rule this encodes (see ``.claude/rules/data.md`` and decisions D-licence):
**Use FACTS + our own words + a citation. Never reproduce a source's expression (its tables,
figures, maps, text, or the document itself). Attribution is not permission.**

Fields per source:
- ``licence``               — short licence id (e.g. "CC-BY-4.0", "proprietary-netbeheerder").
- ``customer_report_safe``  — may facts DERIVED from this appear in a *paid* customer report?
- ``reproduction_allowed``  — may we store/serve the *raw* source artifact (PDF/tiles/tables)?
- ``attribution``           — the exact credit string that MUST render wherever it's used (or None).
- ``usage_note``            — the human-readable rule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    licence: str
    customer_report_safe: bool
    reproduction_allowed: bool
    attribution: str | None
    usage_note: str


# Every source name used anywhere in the codebase MUST appear here. Unknown/unassessed sources
# default to customer_report_safe=False (safe-by-default) so the report gate can never be bypassed
# by an unregistered name. Flags mirror docs/data-sources.md.
SOURCES: dict[str, Source] = {
    # --- assessed, in use ---
    "cbs_postcode6": Source(
        name="cbs_postcode6",
        licence="CC-BY-4.0",
        customer_report_safe=True,
        reproduction_allowed=True,
        attribution="© CBS, © Esri Nederland",  # licence CONDITION, not optional
        usage_note="Attribution mandatory on any map/report that shows the polygons.",
    ),
    "capaciteitskaart": Source(
        name="capaciteitskaart",
        licence="ambiguous-netbeheerder",
        customer_report_safe=True,
        # Licence is ambiguous (no explicit open/CC statement) → don't redistribute the raw
        # CSV/tables; extracted facts are fine.
        reproduction_allowed=False,
        attribution="Bron: Netbeheer Nederland, Capaciteitskaart elektriciteitsnet",
        usage_note="Indicative data; always show confidence + as_of. Facts only, not the raw file.",
    ),
    "investeringsplannen_2026": Source(
        name="investeringsplannen_2026",
        licence="proprietary-netbeheerder (no open licence)",
        customer_report_safe=True,  # for extracted FACTS ONLY
        reproduction_allowed=False,
        attribution="Bron: <operator> Investeringsplan 2026",
        usage_note=(
            "Extract facts only. NEVER store, serve, mirror, or reproduce the PDF or its "
            "tables/figures/maps/text. Re-derive facts into our own schema and layout."
        ),
    ),
    "enexis_waitlist": Source(
        name="enexis_waitlist",
        licence="esri-platform-tou",
        customer_report_safe=False,  # BLOCKED from paid reports
        reproduction_allowed=False,
        attribution="Bron: Netbeheer Nederland / Esri Nederland",
        usage_note=(
            "LICENCE-BLOCKED for redistribution until cleared owner-direct via Partners in "
            "Energie. Prototype/read only."
        ),
    ),
    # --- registered but not yet assessed: conservative, report-UNSAFE until each is verified ---
    **{
        name: Source(
            name=name,
            licence="unverified",
            customer_report_safe=False,
            reproduction_allowed=False,
            attribution=None,
            usage_note="Licence not yet assessed — report-unsafe by default until verified.",
        )
        for name in (
            "liander",
            "enexis",
            "stedin",
            "tennet",
            "entsoe",
            "gopacs",
            "liander_waitlist",
            "vivet",
            "capacitypedia",
            "partners-in-energie",
        )
    },
}


def get_source(name: str) -> Source:
    """Return the registered ``Source``. Fails loud on an unregistered name so nothing
    unassessed can silently flow into ingestion or a report."""
    try:
        return SOURCES[name]
    except KeyError:
        raise KeyError(
            f"source {name!r} is not registered in provenance.sources.SOURCES — register it "
            f"(with licence metadata) before using it anywhere"
        ) from None
