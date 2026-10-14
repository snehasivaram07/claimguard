import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONLogFormatter(logging.Formatter):
    """Formats log records as structured JSON without exposing secrets or document content."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include custom context attributes if injected
        for key in ("request_id", "user_id", "owner_id", "action", "resource_id", "outcome"):
            if hasattr(record, key):
                log_payload[key] = getattr(record, key)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures structured JSON logging for ClaimGuard."""
    log_level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("claimguard")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if re-invoked
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONLogFormatter())
        logger.addHandler(handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("falkordb").setLevel(logging.INFO)

    return logger


logger = setup_logging()
