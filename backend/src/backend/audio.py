"""Audio transcription through a separately configured Azure deployment."""

from __future__ import annotations

import os
import logging
from pathlib import Path
from time import perf_counter
from typing import Any

from src.ai.azure_client import get_azure_client, is_azure_configured
from src.backend.logging_config import log_event


logger = logging.getLogger(__name__)


def get_transcription_deployment() -> str:
    return os.getenv("AZURE_OPENAI_TRANSCRIPTION_DEPLOYMENT", "").strip()


def is_transcription_configured() -> bool:
    return is_azure_configured() and bool(get_transcription_deployment())


def transcribe_audio(file_path: str, *, language: str | None = None) -> dict[str, Any]:
    """Transcribe an audio file with Azure OpenAI; no local FFmpeg is required."""
    deployment = get_transcription_deployment()
    if not is_transcription_configured():
        raise RuntimeError(
            "Audio transcription requires AZURE_OPENAI_TRANSCRIPTION_DEPLOYMENT "
            "in the project .env file."
        )

    path = Path(file_path)
    started = perf_counter()
    kwargs: dict[str, Any] = {"model": deployment}
    if language:
        kwargs["language"] = language.casefold().split("-")[0]
    with path.open("rb") as audio_file:
        response = get_azure_client().audio.transcriptions.create(file=audio_file, **kwargs)

    text = getattr(response, "text", None)
    if not text and isinstance(response, str):
        text = response
    if not text:
        raise RuntimeError("Azure returned an empty transcription.")
    transcript = str(text).strip()
    log_event(
        logger,
        logging.INFO,
        "azure_audio_transcription_completed",
        deployment=deployment,
        file_type=path.suffix.casefold(),
        size_bytes=path.stat().st_size,
        language=kwargs.get("language"),
        transcript_chars=len(transcript),
        duration_ms=round((perf_counter() - started) * 1000),
    )
    return {
        "status": "complete",
        "transcript": transcript,
        "provider": "azure_openai",
        "deployment": deployment,
        "filename": path.name,
    }
