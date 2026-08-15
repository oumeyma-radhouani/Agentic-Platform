"""Validate, enrich, and package customer-feedback batches for analysis."""

from __future__ import annotations

import json
import logging
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, TextIO
from uuid import uuid4

from pydantic import ValidationError

from src.backend.aggregator import aggregate_results, calculate_summary_metrics, classify_nps
from src.backend.schema import (
    CANONICAL_FEEDBACK_FIELDS,
    ENRICHMENT_SCHEMA_VERSION,
    FEEDBACK_SCHEMA_NAME,
    FEEDBACK_SCHEMA_VERSION,
    FeedbackEnrichment,
    FeedbackRecord,
    feedback_json_schema,
)
from src.backend.privacy import redact_model_input
from src.backend.logging_config import log_event
from src.backend.prompt_security import DETECTOR_VERSION, assess_prompt_injection

Analyzer = Callable[[str, int, str], Mapping[str, Any]]
ProgressCallback = Callable[[int, int], None]
logger = logging.getLogger(__name__)


class RecordValidationError(ValueError):
    """Raised when one feedback record does not satisfy the source contract."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _read_source(
    source: str | Path | TextIO | Sequence[Mapping[str, Any]],
) -> tuple[list[Any], str]:
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


def _format_validation_error(exc: ValidationError) -> str:
    messages = []
    for error in exc.errors(include_url=False):
        field = ".".join(str(part) for part in error["loc"]) or "record"
        messages.append(f"{field}: {error['msg']}")
    return "; ".join(messages)


def validate_record(
    raw_record: Any,
    *,
    record_index: int,
    seen_feedback_ids: set[str],
) -> dict[str, Any]:
    """Validate and normalize a raw object into the canonical v1 schema."""
    if not isinstance(raw_record, Mapping):
        raise RecordValidationError("record: must be a JSON object")

    try:
        validated = FeedbackRecord.model_validate(raw_record)
    except ValidationError as exc:
        raise RecordValidationError(_format_validation_error(exc)) from exc

    if validated.feedback_id in seen_feedback_ids:
        raise RecordValidationError(f"feedback_id: duplicate value {validated.feedback_id}")

    seen_feedback_ids.add(validated.feedback_id)
    return {**validated.model_dump(), "record_index": record_index}


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


def _to_enriched_record(
    record: Mapping[str, Any],
    analysis: Mapping[str, Any],
    processing_time_ms: int,
    redacted_entity_types: Sequence[str],
) -> dict[str, Any]:
    """Flatten source fields and explicitly prefixed prediction fields."""
    raw_prediction = analysis.get("prediction")
    if not isinstance(raw_prediction, Mapping):
        raise TypeError("The analyzer must return a 'prediction' object.")
    prediction = FeedbackEnrichment.model_validate(raw_prediction)

    metadata = analysis.get("model_metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}

    return {
        **{field: record[field] for field in CANONICAL_FEEDBACK_FIELDS},
        "nps_category": classify_nps(record["score"]),
        "predicted_theme_id": prediction.theme_id,
        "predicted_sentiment": prediction.sentiment,
        "predicted_urgency": prediction.urgency,
        "prediction_summary": prediction.summary,
        "prediction_evidence": prediction.evidence,
        "prediction_needs_review": bool(analysis.get("prediction_needs_review", False)),
        "model_input_redacted": bool(redacted_entity_types),
        "redacted_entity_types": list(redacted_entity_types),
        "model_provider": str(metadata.get("provider", "custom")),
        "model_name": str(metadata.get("model_name", "custom-analyzer")),
        "prompt_version": str(metadata.get("prompt_version", "unknown")),
        "enrichment_schema_version": str(
            metadata.get("enrichment_schema_version", ENRICHMENT_SCHEMA_VERSION)
        ),
        "processing_time_ms": processing_time_ms,
    }


def _count_missing_fields(raw_records: Sequence[Any]) -> dict[str, int]:
    counts = Counter()
    for raw in raw_records:
        if not isinstance(raw, Mapping):
            counts.update(CANONICAL_FEEDBACK_FIELDS)
            continue
        for field in CANONICAL_FEEDBACK_FIELDS:
            value = raw.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                counts[field] += 1
    return {field: counts[field] for field in CANONICAL_FEEDBACK_FIELDS}


def _build_data_quality_report(
    raw_records: Sequence[Any],
    normalized_records: Sequence[Mapping[str, Any]],
    enriched_records: Sequence[Mapping[str, Any]],
    errors: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    validation_errors = [error for error in errors if error["stage"] == "validation"]
    enrichment_errors = [error for error in errors if error["stage"] == "enrichment"]
    security_reviews = [error for error in errors if error["stage"] == "security"]
    review_required = sum(
        bool(record.get("prediction_needs_review")) for record in enriched_records
    )
    redacted_model_inputs = sum(
        bool(record.get("model_input_redacted")) for record in enriched_records
    )
    comment_counts = Counter(record["comment"].casefold() for record in normalized_records)
    duplicate_comment_rows = sum(count - 1 for count in comment_counts.values() if count > 1)
    total = len(raw_records)
    valid = len(normalized_records)

    unexpected_fields = Counter()
    for raw in raw_records:
        if isinstance(raw, Mapping):
            unexpected_fields.update(set(raw) - set(CANONICAL_FEEDBACK_FIELDS))

    warnings = []
    if validation_errors:
        warnings.append(
            {
                "code": "REJECTED_RECORDS",
                "severity": "error",
                "message": f"{len(validation_errors)} record(s) failed schema validation.",
            }
        )
    if enrichment_errors:
        warnings.append(
            {
                "code": "ENRICHMENT_FAILURES",
                "severity": "warning",
                "message": f"{len(enrichment_errors)} valid record(s) could not be enriched.",
            }
        )
    if security_reviews:
        warnings.append(
            {
                "code": "PROMPT_INJECTION_REVIEW",
                "severity": "warning",
                "message": (
                    f"{len(security_reviews)} valid record(s) were preserved but not "
                    "sent for enrichment because local security checks flagged them."
                ),
            }
        )
    if review_required:
        warnings.append(
            {
                "code": "PREDICTIONS_REQUIRE_REVIEW",
                "severity": "warning",
                "message": (
                    f"{review_required} prediction(s) were excluded from analytical "
                    "findings because their evidence could not be verified."
                ),
            }
        )
    if duplicate_comment_rows:
        warnings.append(
            {
                "code": "DUPLICATE_COMMENTS",
                "severity": "warning",
                "message": f"{duplicate_comment_rows} row(s) repeat an existing comment.",
            }
        )
    if 0 < valid < 30:
        warnings.append(
            {
                "code": "SMALL_SAMPLE",
                "severity": "info",
                "message": "Fewer than 30 valid records; subgroup findings are descriptive only.",
            }
        )

    return {
        "schema_name": FEEDBACK_SCHEMA_NAME,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "total_received": total,
        "total_valid": valid,
        "total_rejected": len(validation_errors),
        "validity_rate_pct": 0 if total == 0 else round(valid / total * 100, 2),
        "enrichment_succeeded": len(enriched_records),
        "enrichment_failed": len(enrichment_errors),
        "enrichment_skipped_security": len(security_reviews),
        "predictions_ready": len(enriched_records) - review_required,
        "predictions_review_required": review_required,
        "total_review_required": review_required + len(security_reviews),
        "model_inputs_redacted": redacted_model_inputs,
        "unique_comment_count": len(comment_counts),
        "duplicate_comment_rows": duplicate_comment_rows,
        "missing_field_counts": _count_missing_fields(raw_records),
        "unexpected_field_counts": dict(sorted(unexpected_fields.items())),
        "source_distribution": dict(Counter(record["source"] for record in normalized_records)),
        "language_distribution": dict(
            Counter(record["language"] for record in normalized_records)
        ),
        "score_distribution": {
            str(score): sum(record["score"] == score for record in normalized_records)
            for score in range(11)
        },
        "warnings": warnings,
    }


def _group_nps(records: Sequence[Mapping[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        groups.setdefault(str(record[field]), []).append(record)

    output = []
    for value, group in groups.items():
        metrics = calculate_summary_metrics(group)
        total = len(group)
        output.append(
            {
                field: value,
                "responses": total,
                "nps_score": metrics["nps_score"],
                "detractors": metrics["total_detractors"],
                "detractor_rate_pct": round(metrics["total_detractors"] / total * 100, 2),
            }
        )
    return sorted(output, key=lambda item: (-item["responses"], str(item[field]).casefold()))


def _generate_evidence_insights(
    normalized_records: Sequence[Mapping[str, Any]],
    enriched_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Generate descriptive findings with denominators and record-level evidence."""
    trusted_records = [
        record for record in enriched_records if not record.get("prediction_needs_review")
    ]
    themes = Counter(record["predicted_theme_id"] for record in trusted_records)
    theme_breakdown = [
        {
            "theme_id": theme,
            "count": count,
            "share_pct": round(count / len(trusted_records) * 100, 2),
        }
        for theme, count in themes.most_common()
    ] if trusted_records else []

    findings = []
    if theme_breakdown:
        top_theme = theme_breakdown[0]
        evidence_ids = [
            record["feedback_id"]
            for record in trusted_records
            if record["predicted_theme_id"] == top_theme["theme_id"]
        ]
        findings.append(
            {
                "finding_id": "TOP_PREDICTED_THEME",
                "title": "Most frequent predicted theme",
                "statement": (
                    f"{top_theme['theme_id']} appears in {top_theme['count']} of "
                    f"{len(trusted_records)} review-ready predictions."
                ),
                "metric": "predicted_theme_share_pct",
                "value": top_theme["share_pct"],
                "denominator": len(trusted_records),
                "record_ids": evidence_ids,
                "caveats": ["Themes are model predictions and require validation."],
            }
        )

    source_breakdown = _group_nps(normalized_records, "source")
    if source_breakdown:
        eligible = [group for group in source_breakdown if group["responses"] >= 5]
        if eligible:
            highest = max(eligible, key=lambda item: item["detractor_rate_pct"])
            record_ids = [
                record["feedback_id"]
                for record in normalized_records
                if record["source"] == highest["source"] and classify_nps(record["score"]) == "detractor"
            ]
            findings.append(
                {
                    "finding_id": "SOURCE_DETRACTOR_RATE",
                    "title": "Highest observed detractor rate by source",
                    "statement": (
                        f"{highest['source']} has {highest['detractors']} detractors "
                        f"among {highest['responses']} valid responses."
                    ),
                    "metric": "detractor_rate_pct",
                    "value": highest["detractor_rate_pct"],
                    "denominator": highest["responses"],
                    "record_ids": record_ids,
                    "caveats": [
                        "Descriptive association only; source does not imply causation.",
                        "Groups with fewer than five responses are excluded.",
                    ],
                }
            )

    return {
        "source_breakdown": source_breakdown,
        "language_breakdown": _group_nps(normalized_records, "language"),
        "predicted_theme_breakdown": theme_breakdown,
        "prediction_population": {
            "enriched": len(enriched_records),
            "included": len(trusted_records),
            "excluded_for_review": len(enriched_records) - len(trusted_records),
        },
        "findings": findings,
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
    try:
        raw_records, source_name = _read_source(source)
    except Exception as exc:
        log_event(
            logger,
            logging.ERROR,
            "batch_source_read_failed",
            batch_id=batch_id,
            reason_type=type(exc).__name__,
        )
        raise

    log_event(
        logger,
        logging.INFO,
        "batch_processing_started",
        batch_id=batch_id,
        source_name=source_name,
        total_received=len(raw_records),
        max_retries=max_retries,
    )
    analyze = analyzer or _default_analyzer()
    normalized_records: list[dict[str, Any]] = []
    enriched_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    security_review_queue: list[dict[str, Any]] = []
    seen_feedback_ids: set[str] = set()
    total = len(raw_records)

    for index, raw_record in enumerate(raw_records, start=1):
        record_started = perf_counter()
        feedback_id = raw_record.get("feedback_id") if isinstance(raw_record, Mapping) else None
        try:
            record = validate_record(
                raw_record,
                record_index=index,
                seen_feedback_ids=seen_feedback_ids,
            )
            feedback_id = record["feedback_id"]
            normalized_records.append(
                {field: record[field] for field in CANONICAL_FEEDBACK_FIELDS}
            )
        except Exception as exc:
            errors.append(
                {
                    "record_index": index,
                    "feedback_id": feedback_id,
                    "stage": "validation",
                    "status": "failed",
                    "error_reason": str(exc),
                }
            )
            log_event(
                logger,
                logging.DEBUG,
                "batch_record_validation_failed",
                batch_id=batch_id,
                record_index=index,
                reason_type=type(exc).__name__,
            )
            if progress_callback is not None:
                progress_callback(index, total)
            continue

        security_assessment = assess_prompt_injection(record["comment"])
        if not security_assessment.allowed:
            assessment_data = security_assessment.to_dict()
            errors.append(
                {
                    "record_index": index,
                    "feedback_id": feedback_id,
                    "stage": "security",
                    "status": "review_required",
                    "error_reason": "Potential prompt injection detected by local rules.",
                    "security_assessment": assessment_data,
                }
            )
            security_review_queue.append(
                {
                    "feedback_id": record["feedback_id"],
                    "customer_id": record["customer_id"],
                    "score": record["score"],
                    "comment": record["comment"],
                    "predicted_theme_id": None,
                    "predicted_sentiment": None,
                    "predicted_urgency": None,
                    "prediction_evidence": None,
                    "review_reason": "Local prompt-injection indicators require review.",
                    "review_type": "security",
                    "security_assessment": assessment_data,
                    "model_name": None,
                    "prompt_version": None,
                }
            )
            log_event(
                logger,
                logging.WARNING,
                "batch_record_security_review_required",
                batch_id=batch_id,
                record_index=index,
                risk=security_assessment.risk,
                score=security_assessment.score,
                reason_codes=list(security_assessment.reason_codes),
            )
            if progress_callback is not None:
                progress_callback(index, total)
            continue

        try:
            model_comment, redacted_entity_types = redact_model_input(record["comment"])
            model_record = dict(record)
            model_record["comment"] = model_comment
            analysis = _analyze_with_retries(analyze, model_record, max_retries)
            elapsed_ms = round((perf_counter() - record_started) * 1000)
            enriched_records.append(
                _to_enriched_record(
                    record, analysis, elapsed_ms, redacted_entity_types
                )
            )
        except Exception as exc:
            errors.append(
                {
                    "record_index": index,
                    "feedback_id": feedback_id,
                    "stage": "enrichment",
                    "status": "failed",
                    "error_reason": str(exc),
                }
            )
            log_event(
                logger,
                logging.DEBUG,
                "batch_record_enrichment_failed",
                batch_id=batch_id,
                record_index=index,
                reason_type=type(exc).__name__,
            )
        finally:
            if progress_callback is not None:
                progress_callback(index, total)

    trusted_enriched_records = [
        record for record in enriched_records if not record.get("prediction_needs_review")
    ]
    output = aggregate_results(
        trusted_enriched_records,
        metric_records=normalized_records,
        top_theme_limit=top_theme_limit,
    )
    output["normalized_records"] = normalized_records
    output["enriched_records"] = enriched_records
    output["review_queue"] = security_review_queue + [
        {
            "feedback_id": record["feedback_id"],
            "customer_id": record["customer_id"],
            "score": record["score"],
            "comment": record["comment"],
            "predicted_theme_id": record["predicted_theme_id"],
            "predicted_sentiment": record["predicted_sentiment"],
            "predicted_urgency": record["predicted_urgency"],
            "prediction_evidence": record["prediction_evidence"],
            "review_reason": "prediction evidence was not found verbatim in the model input",
            "review_type": "prediction",
            "security_assessment": None,
            "model_name": record["model_name"],
            "prompt_version": record["prompt_version"],
        }
        for record in enriched_records
        if record.get("prediction_needs_review")
    ]
    output["rejected_records"] = [
        error for error in errors if error["stage"] == "validation"
    ]
    output["data_quality"] = _build_data_quality_report(
        raw_records, normalized_records, enriched_records, errors
    )
    flagged_record_count = output["data_quality"]["enrichment_skipped_security"]
    output["security_alert"] = {
        "detected": flagged_record_count > 0,
        "code": "PROMPT_INJECTION_FLAGGED" if flagged_record_count else None,
        "severity": "warning" if flagged_record_count else "none",
        "flagged_record_count": flagged_record_count,
        "action": "quarantined_for_review" if flagged_record_count else "none",
        "detector_version": DETECTOR_VERSION,
        "message": (
            f"Potential prompt-injection indicators were detected in "
            f"{flagged_record_count} record(s). The records were preserved, excluded "
            "from ML enrichment, and added to the review queue."
            if flagged_record_count
            else "No prompt-injection indicators were detected by the local rules."
        ),
    }
    output["evidence_insights"] = _generate_evidence_insights(
        normalized_records, enriched_records
    )
    output["dataset_manifest"] = {
        "schema_name": FEEDBACK_SCHEMA_NAME,
        "schema_version": FEEDBACK_SCHEMA_VERSION,
        "canonical_fields": list(CANONICAL_FEEDBACK_FIELDS),
        "prediction_fields": [
            "predicted_theme_id",
            "predicted_sentiment",
            "predicted_urgency",
            "prediction_summary",
            "prediction_evidence",
            "prediction_needs_review",
            "model_input_redacted",
            "redacted_entity_types",
        ],
        "review_queue_fields": [
            "feedback_id",
            "customer_id",
            "score",
            "comment",
            "predicted_theme_id",
            "predicted_sentiment",
            "predicted_urgency",
            "prediction_evidence",
            "review_reason",
            "review_type",
            "security_assessment",
            "model_name",
            "prompt_version",
        ],
        "security_alert_fields": [
            "detected",
            "code",
            "severity",
            "flagged_record_count",
            "action",
            "detector_version",
            "message",
        ],
        "feedback_json_schema": feedback_json_schema(),
        "nps_definition": {
            "detractor": "score 0-6",
            "passive": "score 7-8",
            "promoter": "score 9-10",
        },
        "security_policy": {
            "prompt_injection_detector": DETECTOR_VERSION,
            "source_records_preserved": True,
            "flagged_records_sent_for_enrichment": False,
            "flagged_records_destination": "review_queue",
        },
    }
    output["errors"] = errors
    validation_failures = sum(error["stage"] == "validation" for error in errors)
    enrichment_failures = sum(error["stage"] == "enrichment" for error in errors)
    security_review_required = sum(error["stage"] == "security" for error in errors)
    review_required = len(enriched_records) - len(trusted_enriched_records)
    if not normalized_records:
        run_status = "failed"
    elif validation_failures or enrichment_failures or security_review_required or review_required:
        run_status = "partial"
    else:
        run_status = "complete"

    output["run_info"] = {
        "batch_id": batch_id,
        "status": run_status,
        "source_name": source_name,
        "started_at": batch_started.isoformat(),
        "completed_at": _utc_now().isoformat(),
        "processing_time_ms": round((perf_counter() - timer_started) * 1000),
        "total_received": total,
        "total_valid": len(normalized_records),
        "total_enriched": len(enriched_records),
        "total_failed_validation": validation_failures,
        "total_failed_enrichment": enrichment_failures,
        "total_security_review_required": security_review_required,
        "total_predictions_review_required": review_required,
    }
    completion_level = logging.INFO if run_status == "complete" else logging.WARNING
    log_event(
        logger,
        completion_level,
        "batch_processing_completed",
        batch_id=batch_id,
        source_name=source_name,
        status=run_status,
        total_received=total,
        total_valid=len(normalized_records),
        total_rejected=validation_failures,
        total_enriched=len(enriched_records),
        enrichment_failed=enrichment_failures,
        security_review_required=security_review_required,
        review_required=review_required + security_review_required,
        redacted_model_inputs=output["data_quality"]["model_inputs_redacted"],
        duration_ms=output["run_info"]["processing_time_ms"],
    )
    return output
