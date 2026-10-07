from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict

# HTTP Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Model Inference Metrics
MODEL_INFERENCE_DURATION_SECONDS = Histogram(
    "model_inference_duration_seconds",
    "Model inference duration in seconds",
    ["model_type"]
)

MODEL_LOADED = Gauge(
    "model_loaded",
    "Indicator if model is loaded (1) or not (0)",
    ["model_type"]
)

# Exception Metrics
EXCEPTION_TOTAL = Counter(
    "exception_total",
    "Total exceptions raised",
    ["exception_type"]
)

# Rate Limiting Metrics
RATE_LIMIT_EXCEEDED_TOTAL = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit exceeded events"
)

# Other Metrics
UPLOADED_FILES_TOTAL = Counter(
    "uploaded_files_total",
    "Total number of uploaded files"
)

DB_CONNECTION_ERRORS_TOTAL = Counter(
    "db_connection_errors_total",
    "Total database connection errors"
)

# Drift Detection Metrics
DRIFT_DETECTED_TOTAL = Counter(
    "drift_detected_total",
    "Total number of drift detections",
    ["model_name"]
)

DRIFT_SCORE = Gauge(
    "drift_score",
    "Current drift score (maximum PSI across bands)",
    ["model_name", "band_index"]
)

# Cache Metrics
CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["cache_type"]
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["cache_type"]
)

CACHE_ERRORS_TOTAL = Counter(
    "cache_errors_total",
    "Total cache errors",
    ["cache_type"]
)

def get_metrics() -> str:
    """
    Generate Prometheus metrics in text format.
    """
    return generate_latest()

def get_metrics_response() -> Dict[str, str]:
    """
    Return the metrics as a dictionary suitable for a FastAPI response.
    """
    return {"media_type": CONTENT_TYPE_LATEST, "content": get_metrics()}