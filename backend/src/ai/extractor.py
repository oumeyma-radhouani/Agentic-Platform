"""Customer-feedback analysis using Azure OpenAI."""

from __future__ import annotations

import json

from backend.src.ai.azure_client import create_chat_completion


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
    """Analyze one customer-feedback record with Azure OpenAI."""
    response_content = create_chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "Analyze customer feedback. Return only a JSON object with "
                    "the keys sentiment, main_cause, theme, urgency, and summary. "
                    "Do not invent details."
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

    return {
        "customer_id": client_id,
        "score": score,
        "nps_category": classify_nps(score),
        "ai_analysis": json.loads(response_content),
    }
