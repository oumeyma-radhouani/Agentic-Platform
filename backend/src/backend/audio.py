"""Audio transcription through a separately configured Azure deployment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.ai.azure_client import get_azure_client, is_azure_configured


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
    return {
        "status": "complete",
        "transcript": str(text).strip(),
        "provider": "azure_openai",
        "deployment": deployment,
        "filename": path.name,
    }
