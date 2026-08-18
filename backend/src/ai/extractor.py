"""Customer-feedback analysis and decision support using Azure OpenAI."""

from __future__ import annotations

import json

from src.ai.azure_client import create_chat_completion
from src.ai.azure_client import get_deployment_name
from src.backend.schema import ENRICHMENT_SCHEMA_VERSION, FeedbackEnrichment
from src.backend.prompt_security import require_safe_prompt


PROMPT_VERSION = "feedback-enrichment-v2" # Bumped to v2
THEME_IDS = (
    "SUPPORT_RESPONSE_TIME, SUPPORT_QUALITY, TECHNICAL_RELIABILITY, "
    "BILLING_PRICING, USABILITY, PRODUCT_FEATURES, "
    "SALES_ACCOUNT_MANAGEMENT, ONBOARDING_MIGRATION, "
    "POSITIVE_EXPERIENCE, OTHER"
)

# New Target Teams for Action Assignment
TARGET_TEAMS = (
    "ENGINEERING, SUPPORT_L1, SUPPORT_L2, ACCOUNT_MANAGEMENT, "
    "PRODUCT, SALES, NONE"
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


def analyze_feedback(
    client_id: str, 
    score: int, 
    comment: str, 
    operational_metadata: dict | None = None
) -> dict:
    """Create a schema-validated prediction and strategic action plan for one feedback record."""
    require_safe_prompt(comment)
    
    # Inject business context directly into the prompt if available
    business_context = ""
    if operational_metadata:
        business_context = (
            f"Client Segment: {operational_metadata.get('segment', 'Unknown')}\n"
            f"ARR at Risk: {operational_metadata.get('arr_euros', 0)} EUR\n"
            f"Account Manager: {operational_metadata.get('account_manager', 'Unknown')}\n"
        )

    response_content = create_chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "You are a Strategic Executive Copilot for CloudShift, a B2B SaaS platform. "
                    "Your role is to analyze customer feedback and provide direct, actionable decision support. "
                    "Return only a JSON object with exactly these keys: "
                    "theme_id, sentiment, urgency, summary, evidence, target_team, recommended_action. "
                    f"theme_id must be one of: {THEME_IDS}. "
                    "sentiment must be positive, neutral, negative, or mixed. "
                    "urgency must be low, medium, high, or critical. "
                    "evidence must be a short exact quote from the comment. "
                    f"target_team must be one of: {TARGET_TEAMS}. "
                    "recommended_action must be a concise, professional directive (max 2 sentences) to the assigned team outlining the next steps to resolve the issue or capitalize on the feedback. "
                    "Crucial: Factor in the client's segment and ARR (Annual Recurring Revenue) when determining the target_team and urgency."
                ),
            },
            {
                "role": "user",
                "content": f"{business_context}Score: {score}/10\nComment: {comment}",
            },
        ],
        temperature=0.1, # Very slight variance to allow for natural sounding action plans
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