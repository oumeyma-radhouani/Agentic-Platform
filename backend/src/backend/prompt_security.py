"""Free, deterministic first-line checks for prompt-injection indicators.

This module is deliberately conservative and transparent. It is not a complete
prompt-injection solution; its purpose is to identify common direct attacks and
obfuscation so the application can quarantine or review untrusted text before it
reaches a model.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


DETECTOR_VERSION = "local-rules-v1"

_ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\u2060\uFEFF]")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_BASE64_BLOCK_PATTERN = re.compile(
    r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/])"
)

# NFKC does not fold cross-script lookalikes. This small mapping handles common
# characters used to disguise English control words without pretending to be a
# complete confusable-character implementation.
_COMMON_CONFUSABLES = str.maketrans(
    {
        "а": "a",
        "е": "e",
        "і": "i",
        "о": "o",
        "р": "p",
        "с": "c",
        "х": "x",
        "у": "y",
        "Α": "a",
        "Β": "b",
        "Ε": "e",
        "Ι": "i",
        "Κ": "k",
        "Μ": "m",
        "Ν": "n",
        "Ο": "o",
        "Ρ": "p",
        "Τ": "t",
        "Χ": "x",
    }
)

_CATEGORY_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "INSTRUCTION_OVERRIDE": (
        re.compile(r"\b(?:ignore|disregard|forget)\b.{0,40}\b(?:previous|prior|system|developer)\b.{0,20}\binstructions?\b"),
        re.compile(r"\boverride\b.{0,30}\b(?:system|security|rules?|instructions?)\b"),
        re.compile(r"\b(?:ignore|oublie|oubliez)\b.{0,40}\b(?:instructions?|consignes?)\b.{0,20}\b(?:precedentes?|systeme)\b"),
    ),
    "PROMPT_EXTRACTION": (
        re.compile(r"\b(?:reveal|show|print|repeat|expose)\b.{0,40}\b(?:system prompt|hidden instructions?|developer message)\b"),
        re.compile(r"\b(?:affiche|revele|montre|repete)\b.{0,40}\b(?:prompt systeme|instructions? cachees?|message developpeur)\b"),
    ),
    "ROLE_IMPERSONATION": (
        re.compile(r"(?:^|\n)\s*(?:system|developer|assistant)\s*:\s*"),
        re.compile(r"<\|(?:system|developer|assistant)\|>"),
        re.compile(r"\b(?:you are now|developer mode|system override)\b"),
    ),
    "DATA_EXFILTRATION": (
        re.compile(r"\b(?:reveal|show|print|send|expose|extract)\b.{0,50}\b(?:api[_ -]?keys?|passwords?|secrets?|connection strings?|other sessions?|previous users?)\b"),
        re.compile(r"\b(?:affiche|revele|envoie|extrais)\b.{0,50}\b(?:cles? api|mots? de passe|secrets?|autres sessions?)\b"),
    ),
}

_WEIGHTS = {
    "INSTRUCTION_OVERRIDE": 5,
    "PROMPT_EXTRACTION": 5,
    "ROLE_IMPERSONATION": 2,
    "DATA_EXFILTRATION": 5,
    "OBFUSCATION": 3,
}


@dataclass(frozen=True)
class PromptInjectionAssessment:
    """A payload-safe security decision; matched text is intentionally omitted."""

    allowed: bool
    action: str
    risk: str
    score: int
    reason_codes: tuple[str, ...]
    detector_version: str = DETECTOR_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "risk": self.risk,
            "score": self.score,
            "reason_codes": list(self.reason_codes),
            "detector_version": self.detector_version,
        }


class PromptInjectionDetected(ValueError):
    """Raised when untrusted content must not proceed to model processing."""

    def __init__(self, assessment: PromptInjectionAssessment) -> None:
        self.assessment = assessment
        reasons = ", ".join(assessment.reason_codes) or "UNKNOWN"
        super().__init__(f"Potential prompt injection detected ({reasons}).")


def normalize_for_detection(text: str) -> tuple[str, bool]:
    """Return a comparison-only normalized copy and whether obfuscation was found."""
    nfkc_text = unicodedata.normalize("NFKC", text)
    zero_width_found = bool(_ZERO_WIDTH_PATTERN.search(nfkc_text))
    normalized = _ZERO_WIDTH_PATTERN.sub("", nfkc_text)
    normalized = normalized.translate(_COMMON_CONFUSABLES)
    normalized = normalized.casefold()
    normalized = "".join(
        character
        for character in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(character)
    )
    normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip()
    encoded_block_found = bool(_BASE64_BLOCK_PATTERN.search(normalized))
    return normalized, zero_width_found or encoded_block_found


def assess_prompt_injection(text: str) -> PromptInjectionAssessment:
    """Normalize and score common prompt-injection indicators locally."""
    normalized, obfuscation_found = normalize_for_detection(text)
    reasons = [
        category
        for category, patterns in _CATEGORY_PATTERNS.items()
        if any(pattern.search(normalized) for pattern in patterns)
    ]
    if obfuscation_found:
        reasons.append("OBFUSCATION")

    score = sum(_WEIGHTS[reason] for reason in reasons)
    if score >= 7:
        risk, action = "high", "quarantine"
    elif score >= 3:
        risk, action = "medium", "review"
    else:
        risk, action = "low", "allow"

    return PromptInjectionAssessment(
        allowed=action == "allow",
        action=action,
        risk=risk,
        score=score,
        reason_codes=tuple(reasons),
    )


def require_safe_prompt(text: str) -> PromptInjectionAssessment:
    """Return an assessment or raise without exposing the inspected text."""
    assessment = assess_prompt_injection(text)
    if not assessment.allowed:
        raise PromptInjectionDetected(assessment)
    return assessment
