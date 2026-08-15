"""Customer-feedback analysis using Azure OpenAI."""

from __future__ import annotations

import json

from src.ai.azure_client import create_chat_completion
from src.ai.azure_client import get_deployment_name
from src.backend.schema import ENRICHMENT_SCHEMA_VERSION, FeedbackEnrichment
from src.backend.prompt_security import require_safe_prompt


PROMPT_VERSION = "feedback-enrichment-v1"
THEME_IDS = (
    "SUPPORT_RESPONSE_TIME, SUPPORT_QUALITY, TECHNICAL_RELIABILITY, "
    "BILLING_PRICING, USABILITY, PRODUCT_FEATURES, "
    "SALES_ACCOUNT_MANAGEMENT, ONBOARDING_MIGRATION, "
    "POSITIVE_EXPERIENCE, OTHER"
)


def classify_nps(score: int) -> str:
    """Return the localized NPS category for a score from 0 to 10."""
    if not 0 <= score <= 10:
        raise ValueError("The score must be between 0 and 10.")
    if score >= 9:
        return "promoteur"
    if score >= 7:
        return "neutre"
    return "detracteur"


def analyze_feedback(client_id: str, score: int, comment: str) -> dict:
    """Create a schema-validated prediction for one feedback record."""
    require_safe_prompt(comment)
    response_content = create_chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "Classify one customer-feedback comment for a machine-learning "
                    "dataset. Return only a JSON object with exactly these keys: "
                    "theme_id, sentiment, urgency, summary, evidence. "
                    f"theme_id must be one of: {THEME_IDS}. "
                    "sentiment must be positive, neutral, negative, or mixed. "
                    "urgency must be low, medium, high, or critical. "
                    "evidence must be a short exact quote from the comment. "
                    "Do not infer customer attributes, financial impact, or facts "
                    "that are not explicitly present."
                ),
            },
            {
                "role": "user",
                "content": f"Score: {score}/10\nComment: {comment}",
            },
        ],
        temperature=0,
        max_completion_tokens=1024,
        response_format={"type": "json_object"},
    )

    enrichment = FeedbackEnrichment.model_validate(json.loads(response_content))
    evidence_is_quote = enrichment.evidence.casefold() in comment.casefold()

    return {
        "customer_id": client_id,
        "score": score,
        "nps_category": classify_nps(score),
        "prediction": enrichment.model_dump(),
        "prediction_needs_review": not evidence_is_quote,
        "model_metadata": {
            "provider": "azure_openai",
            "model_name": get_deployment_name(),
            "prompt_version": PROMPT_VERSION,
            "enrichment_schema_version": ENRICHMENT_SCHEMA_VERSION,
        },
    }
