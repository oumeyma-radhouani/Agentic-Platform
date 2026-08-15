"""Shared Azure OpenAI configuration and chat-completion helpers."""

from __future__ import annotations

import os
import logging
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

from dotenv import load_dotenv
from openai import AzureOpenAI

from src.backend.logging_config import log_event

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

DEFAULT_ENDPOINT = "https://novaso.openai.azure.com/"
DEFAULT_DEPLOYMENT = "gpt-4.1-mini"
DEFAULT_API_VERSION = "2024-12-01-preview"
logger = logging.getLogger(__name__)


def get_deployment_name() -> str:
    """Return the configured Azure deployment name."""
    return os.getenv("AZURE_OPENAI_DEPLOYMENT", DEFAULT_DEPLOYMENT).strip()


def is_azure_configured() -> bool:
    """Return whether the minimum Azure OpenAI configuration is present."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    return bool(api_key and api_key != "<your-api-key>")


@lru_cache(maxsize=1)
def get_azure_client() -> AzureOpenAI:
    """Build and cache an Azure OpenAI client from environment variables."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "<your-api-key>":
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY is missing. Add it to the project's .env file."
        )

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", DEFAULT_ENDPOINT).strip()
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", DEFAULT_API_VERSION).strip()
    return AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=api_key,
    )


def create_chat_completion(
    messages: Sequence[dict[str, str]],
    *,
    temperature: float = 0.7,
    max_completion_tokens: int = 2048,
    response_format: dict[str, Any] | None = None,
) -> str:
    """Send a chat completion to the configured Azure deployment."""
    request: dict[str, Any] = {
        "model": get_deployment_name(),
        "messages": list(messages),
        "max_completion_tokens": max_completion_tokens,
        "temperature": temperature,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }
    if response_format is not None:
        request["response_format"] = response_format

    started = perf_counter()
    log_event(
        logger,
        logging.DEBUG,
        "azure_chat_completion_started",
        deployment=request["model"],
        message_count=len(messages),
        max_completion_tokens=max_completion_tokens,
        temperature=temperature,
        structured_response=response_format is not None,
    )
    try:
        response = get_azure_client().chat.completions.create(**request)
    except Exception:
        log_event(
            logger,
            logging.ERROR,
            "azure_chat_completion_failed",
            exc_info=True,
            deployment=request["model"],
            message_count=len(messages),
            duration_ms=round((perf_counter() - started) * 1000),
        )
        raise
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Azure OpenAI returned an empty response.")
    log_event(
        logger,
        logging.INFO,
        "azure_chat_completion_completed",
        deployment=request["model"],
        message_count=len(messages),
        response_chars=len(content),
        duration_ms=round((perf_counter() - started) * 1000),
    )
    return content


def chat_with_assistant(
    user_prompt: str,
    *,
    temperature: float = 0.7,
) -> str:
    """Run a standard NOVA assistant conversation."""
    return create_chat_completion(
        [
            {
                "role": "system",
                "content": "You are NOVA, a helpful customer-operations assistant.",
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
