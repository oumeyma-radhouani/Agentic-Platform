"""Central logging configuration for the NOVA backend.

Logs contain operational metadata only. Callers should never put customer
comments, prompts, transcripts, document text, credentials, or connection
strings in the structured context.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Mapping


_HANDLER_MARKER = "_nova_logging_handler"


def _log_level() -> int:
    configured = os.getenv("NOVA_LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, configured, logging.INFO)


def anonymize_identifier(value: str) -> str:
    """Return a stable, non-reversible identifier for log correlation."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


class NovaFormatter(logging.Formatter):
    """Render either readable text or one-JSON-object-per-line logs."""

    def __init__(self, *, json_output: bool) -> None:
        super().__init__()
        self.json_output = json_output

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, timezone.utc).isoformat()
        event = getattr(record, "nova_event", record.getMessage())
        context = getattr(record, "nova_context", {})
        if not isinstance(context, Mapping):
            context = {}

        if self.json_output:
            payload: dict[str, Any] = {
                "timestamp": timestamp,
                "level": record.levelname,
                "logger": record.name,
                "event": event,
                **context,
            }
            if record.exc_info:
                payload["exception"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False, default=str)

        suffix = " ".join(
            f"{key}={json.dumps(value, ensure_ascii=False, default=str)}"
            for key, value in context.items()
        )
        message = f"{timestamp} {record.levelname} {record.name} {event}"
        if suffix:
            message += f" {suffix}"
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        return message


def configure_logging() -> None:
    """Configure NOVA logging once without removing server-owned handlers."""
    root = logging.getLogger()
    level = _log_level()
    root.setLevel(level)

    existing = next(
        (handler for handler in root.handlers if getattr(handler, _HANDLER_MARKER, False)),
        None,
    )
    json_output = os.getenv("NOVA_LOG_FORMAT", "text").strip().casefold() == "json"
    formatter = NovaFormatter(json_output=json_output)

    if existing is None:
        handler = logging.StreamHandler()
        setattr(handler, _HANDLER_MARKER, True)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        existing.setLevel(level)
        existing.setFormatter(formatter)

    # Keep application events visible without duplicating low-value SDK traffic.
    for noisy_logger in ("httpx", "httpcore", "openai", "pymongo"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    exc_info: bool = False,
    **context: Any,
) -> None:
    """Write a named event with explicitly supplied, non-sensitive context."""
    logger.log(
        level,
        event,
        extra={"nova_event": event, "nova_context": context},
        exc_info=exc_info,
    )
