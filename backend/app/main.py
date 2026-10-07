import os
import time
import uuid
import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse

from .config import settings
from .database import init_db
from .cache import initialize_cache, shutdown_cache, get_prediction_cache
from .exceptions import GeoShieldException
from .routes import (
    risk_router,
    environment_router,
    alerts_router,
    reports_router,
    routes_router,
    ml_router,
    batch_router
)
from .logging import setup_logging, generate_request_id
from .metrics import (
    HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS, MODEL_INFERENCE_DURATION_SECONDS, MODEL_LOADED, UPLOADED_FILES_TOTAL, DB_CONNECTION_ERRORS_TOTAL, RATE_LIMIT_EXCEEDED_TOTAL, EXCEPTION_TOTAL,
    get_metrics, CONTENT_TYPE_LATEST
)

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    SLOWAPI_AVAILABLE = True
except Exception:
    SLOWAPI_AVAILABLE = False
    Limiter = None
    _rate_limit_exceeded_handler = None
    get_remote_address = None
    RateLimitExceeded = None
    SlowAPIMiddleware = None

# Setup structured JSON logging (Phase 4 observability)
setup_logging(settings.LOG_LEVEL)

# Health check helper functions (moved to module scope for better testability)
def check_database() -> str:
    """Check database connectivity and return status."""
    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            db_path = db_url[10:]  # remove "sqlite:////"
            if not os.path.isabs(db_path):
                # Assuming the path is relative to the project root
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                db_path = os.path.join(root_dir, db_path)
            if os.path.exists(db_path) and os.path.isfile(db_path):
                return "loaded"
            else:
                return "not_found"
        else:
            # For other databases, we assume not SQLite and return not_found for simplicity
            return "not_found"
    except Exception:
        return "error"

def check_environmental_m1_model() -> str:
    """Check environmental M1 model availability and return status."""
    try:
        from backend.app.services.risk_service import _model_path
        if os.path.exists(_model_path):
            # Check if we're using mock or real model based on settings
            if settings.MOCK_M1_ML:
                return "mock"
            else:
                return "loaded"
        else:
            return "not_found"
    except Exception:
        return "error"

def check_satellite_m3_model() -> str:
    """Check satellite M3 model availability and return status."""
    try:
        # The satellite_m3_model is the Landsat model, which uses the same _model_path as the M1 model
        from backend.app.services.risk_service import _model_path
        if os.path.exists(_model_path):
            # Check if we're using mock or real model based on settings
            if settings.MOCK_M1_ML:
                return "mock"
            else:
                return "loaded"
        else:
            return "not_found"
    except Exception:
        return "error"

def check_environment_service() -> str:
    """Check environment service availability and return status."""
    try:
        # We can just check if the environment_service module can be imported and the function exists.
        # We already import get_environment_data below, so if we are here, it's available.
        from backend.app.services.environment_service import get_environment_data
        # If we successfully imported, the service is available
        return "loaded"
    except Exception:
        return "error"

def check_cache() -> str:
    """Check cache functionality and return status."""
    try:
        cache = get_prediction_cache()
        test_key = "__health_check_test__"
        test_value = "ok"
        cache.set(test_key, test_value, ttl=1)
        retrieved = cache.get(test_key)
        cache.delete(test_key)
        if retrieved == test_value:
            return "loaded"
        else:
            return "error"
    except Exception:
        return "error"


from phase6.image_analysis.models.loader import get_default_model_loader
image_model_loader = get_default_model_loader()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure upload folder exists and initialize database with seed data
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    init_db()
    # Initialize cache
    initialize_cache()
    # Initialize drift monitor from settings (DRIFT_ENABLED / window / threshold)
    try:
        from .services.drift_monitor import initialize_drift_monitor_from_config
        initialize_drift_monitor_from_config()
    except Exception:
        logging.getLogger("error").exception("Failed to initialize drift monitor")
    yield
    # Shutdown logic
    shutdown_cache()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    API_V1_STR=settings.API_V1_STR,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter if slowapi is available and enabled
if SLOWAPI_AVAILABLE and settings.RATE_LIMIT_ENABLED:
    limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
    app.state.limiter = limiter
    # Custom rate limit exceeded handler: MUST be synchronous so slowapi's
    # BaseHTTPMiddleware can invoke it (async handlers are silently replaced
    # by slowapi's default handler, dropping metrics/request_id).
    def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        RATE_LIMIT_EXCEEDED_TOTAL.inc()

        # Ensure a request ID exists even when rate limiting short-circuits the
        # request before (or independently of) the request-logging middleware.
        request_id = getattr(request.state, 'request_id', None)
        if not request_id:
            request_id = generate_request_id()
            try:
                request.state.request_id = request_id
            except Exception:
                pass

        # Log the rate limit event
        logger = logging.getLogger("error")
        logger.warning(
            f"Rate limit exceeded",
            extra={
                "request_id": request_id,
                "endpoint": request.url.path,
                "method": request.method,
            }
        )

        # Build a proper JSONResponse (HTTP 429) including the request_id,
        # instead of mutating the default handler's response body in place.
        import json
        from fastapi.responses import JSONResponse
        default_response = _rate_limit_exceeded_handler(request, exc)
        try:
            payload = json.loads(default_response.body)
            if not isinstance(payload, dict):
                payload = {"error": str(payload)}
        except (json.JSONDecodeError, TypeError, AttributeError):
            payload = {"error": "Rate limit exceeded", "error_code": "RATE_LIMIT_EXCEEDED"}
        payload["request_id"] = request_id

        preserved_headers = {
            name.decode("latin-1"): value.decode("latin-1")
            for name, value in getattr(default_response, "raw_headers", [])
            if name.decode("latin-1").lower() not in ("content-length", "content-type")
        }
        return JSONResponse(
            status_code=default_response.status_code,
            content=payload,
            headers=preserved_headers,
        )
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    # Add slowapi middleware
    app.add_middleware(SlowAPIMiddleware)
else:
    limiter = None

# Security headers middleware
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                # Add security headers
                # HSTS - only add if not localhost (for development compatibility)
                if not scope["server"][0].startswith("127.") and not scope["server"][0] == "localhost":
                    headers[ b"strict-transport-security" ] = b"max-age=31536000; includeSubDomains"
                # Other security headers
                headers[ b"x-content-type-options" ] = b"nosniff"
                headers[ b"x-frame-options" ] = b"DENY"
                headers[ b"referrer-policy" ] = b"strict-origin-when-cross-origin"
                # Content Security Policy - restrictive but allows Swagger UI to work
                headers[ b"content-security-policy" ] = b"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'self';"
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Serve uploaded citizen photographs statically
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Mount API Routers under /api
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(environment_router, prefix=settings.API_V1_STR)
app.include_router(alerts_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(routes_router, prefix=settings.API_V1_STR)
app.include_router(ml_router, prefix=settings.API_V1_STR)
app.include_router(batch_router, prefix=settings.API_V1_STR)

# Middleware for request logging and metrics
@app.middleware("http")
async def request_logging_and_metrics_middleware(request: Request, call_next):
    request_id = generate_request_id()
    start_time = time.time()

    # Add request_id to request state for potential use in endpoints
    request.state.request_id = request_id

    # Process request
    response = None
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # Handle any unexpected errors
        raise e
    finally:
        if response is not None:
            latency = time.time() - start_time
            latency_ms = round(latency * 1000, 2)

            # Update metrics
            method = request.method
            endpoint = request.url.path
            status_code = response.status_code
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(latency)

            # Log the request
            logger = logging.getLogger("access")
            logger.info(
                "Request processed",
                extra={
                    "request_id": request_id,
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": status_code,
                    "latency_ms": latency_ms
                }
            )


# Exception handlers
@app.exception_handler(GeoShieldException)
async def geoshield_exception_handler(request: Request, exc: GeoShieldException):
    """Handle GeoShield-specific exceptions with consistent error response format."""
    # Get request ID from state if available
    request_id = getattr(request.state, 'request_id', None)

    # Update exception metrics
    EXCEPTION_TOTAL.labels(exception_type=type(exc).__name__).inc()

    # Log the error (but don't expose internal details to client)
    logger = logging.getLogger("error")
    logger.error(
        f"GeoShield exception: {exc.error_code}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )

    # For security, return generic message and error code for 500 errors to avoid exposing internal details
    if exc.status_code == 500:
        error_message = "Internal server error"
        error_code = "INTERNAL_SERVER_ERROR"
    else:
        error_message = exc.message
        error_code = exc.error_code

    # Return structured error response
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_message,
            "error_code": error_code,
            "details": exc.details,
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with safe error response."""
    # Get request ID from state if available
    request_id = getattr(request.state, 'request_id', None)

    # Update exception metrics
    EXCEPTION_TOTAL.labels(exception_type=type(exc).__name__).inc()

    # Log the full exception details internally (but don't expose to client)
    logger = logging.getLogger("error")
    logger.error(
        f"Unexpected exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        },
        exc_info=True  # Include traceback in logs for debugging
    )

    # Return safe error response (no internal details exposed)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": {},
            "request_id": request_id
        }
    )


@app.get("/", tags=["System"])
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "phase": "Phase 1 - Full-Stack Foundation",
        "version": settings.VERSION,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "risk": f"{settings.API_V1_STR}/risk?latitude=11.4102&longitude=76.6950",
            "environment": f"{settings.API_V1_STR}/environment?latitude=11.4102&longitude=76.6950",
            "risk_zones": f"{settings.API_V1_STR}/risk-zones",
            "alerts": f"{settings.API_V1_STR}/alerts",
            "reports": f"{settings.API_V1_STR}/reports",
            "route_risk": f"{settings.API_V1_STR}/route-risk?start=Coonoor&destination=Ooty",
            "ml_contract": f"{settings.API_V1_STR}/ml/predict"
        }
    }


@app.get("/api/health", tags=["System"])
def health_check(request: Request):
    from backend.app.config import settings
    from backend.app.services.risk_service import _model_path
    from backend.app.services.environment_service import get_environment_data
    from backend.app.cache import get_prediction_cache

    try:
        database_status = check_database()
    except Exception:
        database_status = "error"

    try:
        environmental_m1_model_status = check_environmental_m1_model()
    except Exception:
        environmental_m1_model_status = "error"

    try:
        satellite_m3_model_status = check_satellite_m3_model()
    except Exception:
        satellite_m3_model_status = "error"

    try:
        environment_service_status = check_environment_service()
    except Exception:
        environment_service_status = "error"

    try:
        cache_status = check_cache()
    except Exception:
        cache_status = "error"

    # Determine overall status - healthy if all critical components are loaded or mock
    # For now, consider it healthy if no errors
    all_good = all([
        status != "error"
        for status in [database_status, environmental_m1_model_status, satellite_m3_model_status,
                      environment_service_status, cache_status]
    ])
    status = "healthy" if all_good else "unhealthy"

    # Get request ID from middleware state
    request_id = getattr(request.state, 'request_id', None)

    response = {
        "status": status,
        "database": database_status,
        "environmental_m1_model": environmental_m1_model_status,
        "satellite_m3_model": satellite_m3_model_status,
        "environment_service": environment_service_status,
        "cache": cache_status
    }

    # Add request ID to response if available
    if request_id:
        response["request_id"] = request_id

    return response


@app.get("/api/metrics", tags=["System"])
def metrics():
    """Expose Prometheus metrics in text exposition format (Phase 4 Step 1)."""
    if not settings.ENABLE_METRICS:
        return PlainTextResponse("Metrics disabled", status_code=404)
    return PlainTextResponse(get_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/ml/model-info", tags=["System"])
def model_info():
    """Get information about the loaded ML model (truthful, no fabrication)."""
    error_message = None
    info = None

    if image_model_loader is None:
        error_message = "Model loader not available"
    else:
        try:
            info = image_model_loader.get_model_info()
        except Exception as e:
            # Handle any unexpected errors from the model loader
            error_message = f"Failed to get model info: {str(e)}"

    if not isinstance(info, dict):
        info = {}
        available = False
    else:
        # Loader reports `model_available`; mocked/alternative loaders may report `available`.
        available = bool(info.get("model_available", info.get("available", False)))

    response = {
        "available": available,
        "error": error_message,
        "model_path": info.get("model_path"),
        "model_version": info.get("model_version"),
        "checksum": info.get("checksum"),
        "load_time_seconds": info.get("load_time_seconds")
    }

    # Pass through loader-provided metadata keys (frontend contract)
    for key in (
        "model_available", "image_ai_enabled", "cached_model", "model_loaded",
        "checkpoint_epoch", "checkpoint_best_val_dice"
    ):
        if key in info:
            response[key] = info[key]

    # Propagate checkpoint metadata when the loader provides it (never fabricated):
    # `epoch`/`best_val_dice` come from the caller, or map from the loader's
    # `checkpoint_epoch`/`checkpoint_best_val_dice` fields.
    if "epoch" in info:
        response["epoch"] = info["epoch"]
    elif "checkpoint_epoch" in info:
        response["epoch"] = info["checkpoint_epoch"]
    if "best_val_dice" in info:
        response["best_val_dice"] = info["best_val_dice"]
    elif "checkpoint_best_val_dice" in info:
        response["best_val_dice"] = info["checkpoint_best_val_dice"]

    return response


@app.get("/api/drift/status", tags=["Drift Detection"])
def drift_status():
    """
    Get drift detection status for monitored models.

    Returns truthful baseline availability and drift detection status from the
    drift monitor (no drift results are fabricated).
    """
    from backend.app.services.drift_monitor import check_drift_status
    return check_drift_status()