"""Versioned schemas for canonical feedback data and AI enrichment."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


FEEDBACK_SCHEMA_NAME = "nova.feedback"
FEEDBACK_SCHEMA_VERSION = "1.0.0"
ENRICHMENT_SCHEMA_VERSION = "1.0.0"

CANONICAL_FEEDBACK_FIELDS = (
    "feedback_id",
    "customer_id",
    "source",
    "score",
    "comment",
    "language",
)

ThemeId = Literal[
    "SUPPORT_RESPONSE_TIME",
    "SUPPORT_QUALITY",
    "TECHNICAL_RELIABILITY",
    "BILLING_PRICING",
    "USABILITY",
    "PRODUCT_FEATURES",
    "SALES_ACCOUNT_MANAGEMENT",
    "ONBOARDING_MIGRATION",
    "POSITIVE_EXPERIENCE",
    "OTHER",
]
Sentiment = Literal["positive", "neutral", "negative", "mixed"]
Urgency = Literal["low", "medium", "high", "critical"]


class FeedbackRecord(BaseModel):
    """Canonical, source-owned feedback record used throughout the pipeline."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    feedback_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    score: int = Field(strict=True, ge=0, le=10)
    comment: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=20)

    @field_validator("score", mode="before")
    @classmethod
    def reject_boolean_score(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("score must be an integer between 0 and 10")
        return value

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        normalized = value.replace("_", "-").upper()
        parts = normalized.split("-")
        if not parts[0].isalpha() or not 2 <= len(parts[0]) <= 3:
            raise ValueError("language must start with a 2- or 3-letter code")
        if any(not part.isalnum() for part in parts[1:]):
            raise ValueError("language contains an invalid locale component")
        return normalized


class FeedbackEnrichment(BaseModel):
    """Controlled model prediction; never treated as source-owned truth."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    theme_id: ThemeId
    sentiment: Sentiment
    urgency: Urgency
    summary: str = Field(min_length=1, max_length=300)
    evidence: str = Field(min_length=1, max_length=300)


def feedback_json_schema() -> dict[str, Any]:
    """Return the machine-readable schema published in batch manifests."""
    return FeedbackRecord.model_json_schema()
