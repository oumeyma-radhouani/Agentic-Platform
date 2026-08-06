"""Batch orchestration for JSON and JSONL customer feedback sources."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, TextIO
from uuid import uuid4

from src.backend.aggregator import aggregate_results, classify_nps

Analyzer = Callable[[str, int, str], Mapping[str, Any]]
ProgressCallback = Callable[[int, int], None]

class RecordValidationError(ValueError):
    """Raised when one feedback record does not satisfy the input contract."""

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _read_source(source: str | Path | TextIO | Sequence[Mapping[str, Any]]) -> tuple[list[Any], str]:
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes, bytearray)):
        return list(source), "in-memory"

    if hasattr(source, "read"):
        text = source.read()
        if isinstance(text, bytes):
            text = text.decode("utf-8")
        source_name = Path(getattr(source, "name", "uploaded.json")).name
        suffix = Path(source_name).suffix.lower()
    else:
        path = Path(source)
        text = path.read_text(encoding="utf-8-sig")
        source_name = path.name
        suffix = path.suffix.lower()

    if suffix == ".jsonl":
        records: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL on line {line_number}: {exc.msg}.") from exc
        return records, source_name

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}.") from exc

    if isinstance(payload, list):
        return payload, source_name
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"], source_name
    if isinstance(payload, dict):
        return [payload], source_name
    raise ValueError("The JSON source must contain an object, a list, or a 'records' list.")

def validate_record(
    raw_record: Any,
    *,
    record_index: int,
    seen_feedback_ids: set[str],
) -> dict[str, Any]:
    if not isinstance(raw_record, Mapping):
        raise RecordValidationError("The record must be a JSON object.")

    raw_feedback_id = raw_record.get("feedback_id", raw_record.get("id"))
    feedback_id = str(raw_feedback_id).strip() if raw_feedback_id is not None else ""
    if not feedback_id:
        raise RecordValidationError("Missing required field: feedback_id (or id).")
    if feedback_id in seen_feedback_ids:
        raise RecordValidationError(f"Duplicate feedback_id: {feedback_id}.")

    raw_score = raw_record.get("score")
    if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
        raise RecordValidationError("The score must be an integer between 0 and 10.")
    if not float(raw_score).is_integer():
        raise RecordValidationError("The score must be an integer between 0 and 10.")
    score = int(raw_score)
    try:
        classify_nps(score)
    except ValueError as exc:
        raise RecordValidationError(str(exc)) from exc

    raw_comment = raw_record.get("comment")
    if not isinstance(raw_comment, str) or not raw_comment.strip():
        raise RecordValidationError("The comment must be a non-empty string.")

    raw_customer_id = raw_record.get("customer_id", raw_record.get("id", feedback_id))
    customer_id = str(raw_customer_id).strip()
    if not customer_id:
        raise RecordValidationError("The customer_id cannot be empty.")

    seen_feedback_ids.add(feedback_id)
    return {
        "feedback_id": feedback_id,
        "customer_id": customer_id,
        "score": score,
        "comment": raw_comment.strip(),
        "created_at": raw_record.get("created_at"),
        "source": raw_record.get("source"),
        "metadata": raw_record.get("metadata", {}),
        "record_index": record_index,
    }

def _default_analyzer() -> Analyzer:
    from src.ai.extractor import analyze_feedback
    return analyze_feedback

def _analyze_with_retries(
    analyzer: Analyzer,
    record: Mapping[str, Any],
    max_retries: int,
) -> Mapping[str, Any]:
    last_error: Exception | None = None
    for _ in range(max_retries + 1):
        try:
            result = analyzer(record["customer_id"], record["score"], record["comment"])
            if not isinstance(result, Mapping):
                raise TypeError("The analyzer must return a mapping.")
            return result
        except Exception as exc:
            last_error = exc
    assert last_error is not None
    raise last_error

def _to_processed_record(
    record: Mapping[str, Any],
    analysis: Mapping[str, Any],
    processing_time_ms: int,
) -> dict[str, Any]:
    ai_analysis = analysis.get("ai_analysis", analysis)
    if not isinstance(ai_analysis, Mapping):
        raise TypeError("The analyzer's ai_analysis field must be a mapping.")

    assigned_theme = analysis.get("assigned_theme", ai_analysis.get("theme", "Non classifié"))
    assigned_urgency = analysis.get("assigned_urgency", ai_analysis.get("urgency", "Non assigné"))
    rag_verified = analysis.get("rag_verified", ai_analysis.get("rag_verified", False))

    return {
        "feedback_id": record["feedback_id"],
        "customer_id": record["customer_id"],
        "original_score": record["score"],
        "original_comment": record["comment"],
        "nps_category": classify_nps(record["score"]),
        "assigned_urgency": str(assigned_urgency),
        "assigned_theme": str(assigned_theme),
        "rag_verified": bool(rag_verified),
        "sentiment": ai_analysis.get("sentiment"),
        "main_cause": ai_analysis.get("main_cause", assigned_theme),
        "summary": ai_analysis.get("summary"),
        "processing_time_ms": processing_time_ms,
        "status": "success",
    }

def _generate_macro_insights(processed_records: list[dict[str, Any]]) -> dict[str, Any]:
    """Génère des insights décisionnels basés sur l'agrégation des analyses de l'IA."""
    detractor_causes = Counter()
    promoter_causes = Counter()

    for rec in processed_records:
        cause = rec.get("main_cause") or rec.get("assigned_theme") or "Problème non spécifié"
        if rec["nps_category"] == "Detractor":
            detractor_causes[cause] += 1
        elif rec["nps_category"] == "Promoter":
            promoter_causes[cause] += 1

    top_frictions = [{"theme": k, "count": v} for k, v in detractor_causes.most_common(3)]
    top_strengths = [{"theme": k, "count": v} for k, v in promoter_causes.most_common(3)]

    # Génération des recommandations dynamiques
    recos = []
    if top_frictions:
        recos.append(f"Alerte Prioritaire : '{top_frictions[0]['theme']}' est la cause majeure d'insatisfaction identifiée sur ce lot.")
    if len(top_frictions) > 1:
        recos.append(f"Optimisation : Sécuriser l'expérience client autour de '{top_frictions[1]['theme']}' pour réduire le risque d'attrition.")
    if top_strengths:
        recos.append(f"Levier de Fidélisation : Capitaliser sur '{top_strengths[0]['theme']}', identifié comme votre atout majeur par les promoteurs.")
    
    if not recos:
        recos.append("L'analyse ne dégage pas de tendance critique. Maintenir le suivi régulier.")

    return {
        "top_frictions": top_frictions,
        "top_strengths": top_strengths,
        "recommendations": recos,
        "main_subject": top_frictions[0]["theme"] if top_frictions else (top_strengths[0]["theme"] if top_strengths else "Général")
    }

def run_batch(
    source: str | Path | TextIO | Sequence[Mapping[str, Any]],
    *,
    analyzer: Analyzer | None = None,
    progress_callback: ProgressCallback | None = None,
    max_retries: int = 1,
    top_theme_limit: int | None = 5,
) -> dict[str, Any]:
    if max_retries < 0:
        raise ValueError("max_retries cannot be negative.")

    batch_started = _utc_now()
    timer_started = perf_counter()
    batch_id = f"BATCH-{uuid4().hex[:12].upper()}"
    raw_records, source_name = _read_source(source)
    analyze = analyzer or _default_analyzer()
    processed_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_feedback_ids: set[str] = set()
    total = len(raw_records)

    for index, raw_record in enumerate(raw_records, start=1):
        record_started = perf_counter()
        feedback_id = None
        if isinstance(raw_record, Mapping):
            feedback_id = raw_record.get("feedback_id", raw_record.get("id"))
        try:
            record = validate_record(
                raw_record,
                record_index=index,
                seen_feedback_ids=seen_feedback_ids,
            )
            feedback_id = record["feedback_id"]
            analysis = _analyze_with_retries(analyze, record, max_retries)
            elapsed_ms = round((perf_counter() - record_started) * 1000)
            processed_records.append(_to_processed_record(record, analysis, elapsed_ms))
        except Exception as exc:
            errors.append(
                {
                    "record_index": index,
                    "feedback_id": feedback_id,
                    "status": "failed",
                    "error_reason": str(exc),
                }
            )
        finally:
            if progress_callback is not None:
                progress_callback(index, total)

    batch_completed = _utc_now()
    
    # Agrégation classique
    output = aggregate_results(processed_records, top_theme_limit=top_theme_limit)
    
    # --- C'EST CETTE LIGNE QUI MANQUAIT AU FRONTEND ---
    output["strategic_insights"] = _generate_macro_insights(processed_records)
    
    output["errors"] = errors
    output["run_info"] = {
        "batch_id": batch_id,
        "source_name": source_name,
        "started_at": batch_started.isoformat(),
        "completed_at": batch_completed.isoformat(),
        "processing_time_ms": round((perf_counter() - timer_started) * 1000),
        "total_received": total,
        "total_succeeded": len(processed_records),
        "total_failed": len(errors),
    }
    return output