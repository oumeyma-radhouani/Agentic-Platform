"""Local document extraction, indexing, and retrieval for grounded chat.

The module name is retained for compatibility with the original project. The
implementation is deliberately transparent: it builds an in-memory lexical
index and never claims that vectors were uploaded to Azure AI Search.
"""

from __future__ import annotations

import math
import re
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from src.backend.logging_config import anonymize_identifier, log_event
from src.backend.prompt_security import PromptInjectionDetected, assess_prompt_injection


_TOKEN_PATTERN = re.compile(r"[\w'-]+", re.UNICODE)
_INDEX_LOCK = RLock()
_DOCUMENTS: dict[str, list[dict[str, Any]]] = {}
logger = logging.getLogger(__name__)


def _extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.casefold()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8-sig"), "plain_text"
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages), "pypdf"
    if suffix == ".docx":
        from docx import Document

        document = Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs), "python-docx"
    raise ValueError("Unsupported document type. Use .txt, .pdf, or .docx.")


def _tokenize(text: str) -> list[str]:
    return [token.casefold() for token in _TOKEN_PATTERN.findall(text)]


def _chunk_text(text: str, *, chunk_words: int = 180, overlap_words: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = chunk_words - overlap_words
    return [
        " ".join(words[start : start + chunk_words])
        for start in range(0, len(words), step)
        if words[start : start + chunk_words]
    ]


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def process_and_vectorize(file_path: str, filename: str, session_id: str) -> dict[str, Any]:
    """Extract and index a document, returning verifiable processing metadata."""
    path = Path(file_path)
    session_ref = anonymize_identifier(session_id)
    text, extractor = _extract_text(path)
    cleaned = " ".join(text.split())
    if not cleaned:
        raise ValueError("The document contains no extractable text.")

    security_assessment = assess_prompt_injection(cleaned)
    if not security_assessment.allowed:
        log_event(
            logger,
            logging.WARNING,
            "document_prompt_injection_detected",
            session_ref=session_ref,
            filename=Path(filename).name,
            risk=security_assessment.risk,
            score=security_assessment.score,
            reason_codes=list(security_assessment.reason_codes),
        )
        raise PromptInjectionDetected(security_assessment)

    document_id = f"DOC-{uuid4().hex[:12].upper()}"
    chunks = _chunk_text(cleaned)
    indexed_at = datetime.now(timezone.utc).isoformat()
    entries = [
        {
            "document_id": document_id,
            "filename": filename,
            "chunk_index": index,
            "text": chunk,
            "term_counts": Counter(_tokenize(chunk)),
        }
        for index, chunk in enumerate(chunks)
    ]
    with _INDEX_LOCK:
        _DOCUMENTS.setdefault(session_id, []).extend(entries)

    log_event(
        logger,
        logging.INFO,
        "document_index_updated",
        session_ref=session_ref,
        document_id=document_id,
        filename=Path(filename).name,
        extractor=extractor,
        word_count=len(cleaned.split()),
        chunk_count=len(entries),
    )

    return {
        "status": "indexed",
        "index_type": "local_lexical_cosine",
        "document_id": document_id,
        "filename": filename,
        "extractor": extractor,
        "character_count": len(cleaned),
        "word_count": len(cleaned.split()),
        "chunk_count": len(entries),
        "indexed_at": indexed_at,
        "security_assessment": security_assessment.to_dict(),
    }


def retrieve_relevant_chunks(session_id: str, query: str, *, limit: int = 4) -> list[dict[str, Any]]:
    """Return ranked document chunks with transparent lexical scores."""
    query_terms = Counter(_tokenize(query))
    with _INDEX_LOCK:
        entries = list(_DOCUMENTS.get(session_id, []))

    ranked = []
    excluded_security_chunks = 0
    for entry in entries:
        if not assess_prompt_injection(entry["text"]).allowed:
            excluded_security_chunks += 1
            continue
        score = _cosine_similarity(query_terms, entry["term_counts"])
        if score > 0:
            ranked.append(
                {
                    "document_id": entry["document_id"],
                    "filename": entry["filename"],
                    "chunk_index": entry["chunk_index"],
                    "score": round(score, 4),
                    "text": entry["text"],
                }
            )
    selected = sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]
    log_event(
        logger,
        logging.DEBUG,
        "document_retrieval_completed",
        session_ref=anonymize_identifier(session_id),
        query_chars=len(query),
        indexed_chunk_count=len(entries),
        matching_chunk_count=len(ranked),
        returned_chunk_count=len(selected),
        excluded_security_chunk_count=excluded_security_chunks,
        limit=limit,
    )
    return selected


def get_document_count(session_id: str) -> int:
    with _INDEX_LOCK:
        return len({entry["document_id"] for entry in _DOCUMENTS.get(session_id, [])})


def clear_document_index() -> None:
    with _INDEX_LOCK:
        _DOCUMENTS.clear()
