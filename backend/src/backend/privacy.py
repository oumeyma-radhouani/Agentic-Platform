"""Deterministic masking for common sensitive identifiers in model inputs."""

from __future__ import annotations

import re


_PATTERNS = (
    (
        "email",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[EMAIL]",
    ),
    (
        "payment_card",
        re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
        "[PAYMENT_CARD]",
    ),
    (
        "phone",
        re.compile(r"(?<!\w)(?:\+?\d[\s().-]?){7,15}(?!\w)"),
        "[PHONE]",
    ),
    (
        "ip_address",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[IP_ADDRESS]",
    ),
)


def redact_model_input(text: str) -> tuple[str, list[str]]:
    """Mask common identifiers and return the entity types that were found.

    This is a conservative first privacy layer, not a complete PII detector.
    Names, addresses, and domain-specific identifiers still require policy and
    review appropriate to the deployment.
    """
    redacted = text
    found: list[str] = []
    for entity_type, pattern, replacement in _PATTERNS:
        redacted, count = pattern.subn(replacement, redacted)
        if count:
            found.append(entity_type)
    return redacted, found
