"""Deterministic statistics for analyzed customer feedback."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping


def classify_nps(score: int) -> str:
    """Return the standard NPS category for an integer score from 0 to 10."""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError("The score must be an integer between 0 and 10.")
    if not 0 <= score <= 10:
        raise ValueError("The score must be between 0 and 10.")
    if score >= 9:
        return "promoter"
    if score >= 7:
        return "passive"
    return "detractor"


def _display_number(value: float) -> int | float:
    """Keep whole-number metrics tidy while retaining useful decimal precision."""
    rounded = round(value, 2)
    return int(rounded) if rounded.is_integer() else rounded


def calculate_summary_metrics(
    processed_records: Iterable[Mapping[str, Any]],
) -> dict[str, int | float]:
    """Calculate NPS metrics from successfully processed records."""
    records = list(processed_records)
    categories = Counter(
        classify_nps(record["original_score"])
        for record in records
    )
    total = len(records)
    promoters = categories["promoter"]
    passives = categories["passive"]
    detractors = categories["detractor"]
    nps_score = 0 if total == 0 else ((promoters - detractors) / total) * 100

    return {
        "total_processed": total,
        "nps_score": _display_number(nps_score),
        "total_promoters": promoters,
        "total_passives": passives,
        "total_detractors": detractors,
    }


def calculate_top_themes(
    processed_records: Iterable[Mapping[str, Any]],
    *,
    limit: int | None = 5,
) -> list[dict[str, int | str]]:
    """Count assigned themes and order them by frequency, then by name."""
    if limit is not None and limit < 0:
        raise ValueError("The theme limit cannot be negative.")

    themes = Counter(
        str(record["assigned_theme"]).strip()
        for record in processed_records
        if str(record.get("assigned_theme", "")).strip()
    )
    ordered = sorted(themes.items(), key=lambda item: (-item[1], item[0].casefold()))
    if limit is not None:
        ordered = ordered[:limit]
    return [{"theme": theme, "count": count} for theme, count in ordered]


def aggregate_results(
    processed_records: Iterable[Mapping[str, Any]],
    *,
    top_theme_limit: int | None = 5,
) -> dict[str, Any]:
    """Build the stable backend payload consumed by the dashboard."""
    records = [dict(record) for record in processed_records]
    return {
        "summary_metrics": calculate_summary_metrics(records),
        "top_themes": calculate_top_themes(records, limit=top_theme_limit),
        "processed_records": records,
    }
