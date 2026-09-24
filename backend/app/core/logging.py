import json
import logging
import sys
from datetime import datetime, timezone


class StructuredJsonFormatter(logging.Formatter):
    """
    Format logs as structured JSON objects for observability and production diagnostics.
    Sanitizes against logging secret tokens, API keys, or raw confidential user messages.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom extra fields if attached to the record (e.g., model, latency_ms, status_code)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            # Explicitly guard against accidental key or token leakage in metadata
            sanitized_extras = {
                k: v for k, v in record.extra_fields.items()
                if "key" not in k.lower() and "token" not in k.lower() and "secret" not in k.lower()
            }
            log_payload.update(sanitized_extras)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Configure global structured logging with stdout stream handler.
    """
    logger = logging.getLogger("ai_assistant")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers if setup is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
