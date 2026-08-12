"""Small in-process context registry for the local NOVA application.

This is intentionally an application runtime cache, not durable storage. It lets
the assistant use verified batch results without sending entire datasets through
the browser on every chat request. Production deployments should replace it with
a database or object store keyed by batch ID.
"""

from __future__ import annotations

import json
from threading import RLock
from typing import Any, Mapping


_LOCK = RLock()
_BATCH_CONTEXTS: dict[str, dict[str, Any]] = {}


def store_batch_context(session_id: str, result: Mapping[str, Any]) -> None:
    """Store the latest verified analytical context for one UI session."""
    enriched = list(result.get("enriched_records", []))
    review_examples = [
        {
            "feedback_id": row.get("feedback_id"),
            "comment": row.get("comment"),
            "predicted_theme_id": row.get("predicted_theme_id"),
            "prediction_evidence": row.get("prediction_evidence"),
        }
        for row in enriched
        if row.get("prediction_needs_review")
    ][:10]
    representative_records = [
        {
            "feedback_id": row.get("feedback_id"),
            "source": row.get("source"),
            "score": row.get("score"),
            "comment": row.get("comment"),
            "predicted_theme_id": row.get("predicted_theme_id"),
            "predicted_sentiment": row.get("predicted_sentiment"),
        }
        for row in enriched
        if not row.get("prediction_needs_review")
    ][:25]

    context = {
        "batch_id": result.get("run_info", {}).get("batch_id"),
        "status": result.get("run_info", {}).get("status"),
        "source_name": result.get("run_info", {}).get("source_name"),
        "data_quality": result.get("data_quality", {}),
        "summary_metrics": result.get("summary_metrics", {}),
        "evidence_insights": result.get("evidence_insights", {}),
        "representative_records": representative_records,
        "review_examples": review_examples,
        "errors": list(result.get("errors", []))[:20],
    }
    with _LOCK:
        _BATCH_CONTEXTS[session_id] = context


def get_batch_context(session_id: str) -> dict[str, Any] | None:
    with _LOCK:
        context = _BATCH_CONTEXTS.get(session_id)
        return dict(context) if context is not None else None


def format_batch_context(session_id: str, *, max_chars: int = 14000) -> str | None:
    """Serialize bounded, verified context for an assistant system message."""
    context = get_batch_context(session_id)
    if context is None:
        return None
    serialized = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    return serialized[:max_chars]


def clear_contexts() -> None:
    """Clear runtime state (primarily for tests)."""
    with _LOCK:
        _BATCH_CONTEXTS.clear()
