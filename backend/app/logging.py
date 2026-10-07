import json
import logging
import sys
import uuid
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output log records as JSON lines.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "endpoint"):
            log_record["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "status_code"):
            log_record["status_code"] = record.status_code
        if hasattr(record, "latency_ms"):
            log_record["latency_ms"] = record.latency_ms
        if hasattr(record, "model_type"):
            log_record["model_type"] = record.model_type
        if hasattr(record, "model_status"):
            log_record["model_status"] = record.model_status
        # Include any other extra attributes
        for key, value in record.__dict__.items():
            if key not in log_record and key not in ["args", "exc_info", "exc_text", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "msg", "name", "pathname", "process", "processName", "relativeCreated", "stack_info", "thread", "threadName"]:
                log_record[key] = value
        return json.dumps(log_record, ensure_ascii=False)

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure root logger to output JSON lines to stdout.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level.upper())

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent duplicate logs in Uvicorn
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn").handlers.clear()

# Dependency to get a request ID (can be used in endpoints)
def generate_request_id() -> str:
    return str(uuid.uuid4())