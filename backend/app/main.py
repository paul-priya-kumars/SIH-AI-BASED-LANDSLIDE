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
from .cache import initialize_cache, shutdown_cache
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
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    MODEL_INFERENCE_DURATION_SECONDS,
    MODEL_LOADED,
    EXCEPTION_TOTAL,
    UPLOADED_FILES_TOTAL,
    DB_CONNECTION_ERRORS_TOTAL,
    RATE_LIMIT_EXCEEDED_TOTAL,
    get_metrics,
    CONTENT_TYPE_LATEST
)
from .exceptions import GeoShieldException

# Rate limiting imports
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    Limiter = None
    _rate_limit_exceeded_handler = None
    get_remote_address = None
    RateLimitExceeded = Exception
    SlowAPIMiddleware = None

# Setup logging
setup_logging(settings.LOG_LEVEL)

# Import model loaders for health checks
try:
    from phase6.image_analysis.models.loader import Landslide4SenseModelLoader
    image_model_loader = Landslide4SenseModelLoader()
except Exception:
    image_model_loader = None

# Helper functions for health checks
def check_database() -> str:
    """Check if database is connected."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return "connected"
    except Exception:
        return "error"

def check_m1_model() -> str:
    """Check if environmental M1 model is available."""
    model_path = os.path.join(os.path.dirname(__file__), "models", "landslide_model.pkl")
    if not os.path.exists(model_path):
        return "not_found"
    # We assume it's a mock if the flag is set, otherwise we don't know without loading.
    if settings.MOCK_M1_ML:
        return "mock"
    # If not mock, we could try to load it, but we don't want to affect state.
    # For now, we'll return "unknown" if not mock and exists.
    return "unknown"

def check_m3_model() -> str:
    """Check if satellite M3/image model is available."""
    if image_model_loader is None:
        return "error"
    if image_model_loader.is_model_available():
        return "loaded"
    else:
        return "not_loaded"

def check_environment_service() -> str:
    """Environment service is always available (mock)."""
    return "active"

def check_cache() -> dict:
    """Check cache status."""
    if not settings.CACHE_ENABLED:
        return {
            "enabled": False,
            "status": "disabled"
        }

    try:
        cache = get_prediction_cache()
        return {
            "enabled": True,
            "status": "ok",
            "entries": cache.size(),
            "max_entries": cache.max_size()
        }
    except Exception as e:
        return {
            "enabled": True,
            "status": "error",
            "error": str(e)
        }

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure upload folder exists and initialize database with seed data
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    init_db()
    # Initialize cache
    initialize_cache()
    yield
    # Shutdown logic
    shutdown_cache()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter if slowapi is available and enabled
if SLOWAPI_AVAILABLE and settings.RATE_LIMIT_ENABLED:
    limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])
    app.state.limiter = limiter
    # Add custom rate limit exceeded exception handler to increment metrics and log
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        RATE_LIMIT_EXCEEDED_TOTAL.inc()
        # Log the rate limit event
        logger = logging.getLogger("security")
        logger.warning(
            f"Rate limit exceeded",
            extra={
                "request_id": getattr(request.state, 'request_id', None),
                "endpoint": request.url.path,
                "method": request.method,
                "client_host": request.client.host if request.client else None,
            }
        )
        return await _rate_limit_exceeded_handler(request, exc)
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
    try:
        response: Response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        EXCEPTION_TOTAL.labels(exception_type=type(e).__name__).inc()
        raise e
    finally:
        latency = time.time() - start_time
        latency_ms = round(latency * 1000, 2)

        # Update metrics
        method = request.method
        endpoint = request.url.path
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

    return response

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
    # Helper to safely execute check functions and return error status on failure
    def safe_string_check(check_func):
        try:
            return check_func()
        except Exception:
            return "error"

    # Get request ID from state
    request_id = getattr(request.state, 'request_id', None)

    # Execute each health check, handling exceptions gracefully
    try:
        database_status = check_database()
    except Exception:
        database_status = "error"

    try:
        environmental_m1_model_status = check_m1_model()
    except Exception:
        environmental_m1_model_status = "error"

    try:
        satellite_m3_model_status = check_m3_model()
    except Exception:
        satellite_m3_model_status = "error"

    try:
        environment_service_status = check_environment_service()
    except Exception:
        environment_service_status = "error"

    # check_cache already handles its own exceptions and returns a dict
    try:
        cache_status = check_cache()
    except Exception:
        cache_status = {
            "enabled": settings.CACHE_ENABLED,
            "status": "error",
            "error": "Cache check failed"
        }

    return {
        "status": "healthy",
        "database": database_status,
        "environmental_m1_model": environmental_m1_model_status,
        "satellite_m3_model": satellite_m3_model_status,
        "environment_service": environment_service_status,
        "cache": cache_status,
        "request_id": request_id
    }

@app.get("/api/metrics", tags=["System"])
def metrics():
    if not settings.ENABLE_METRICS:
        return PlainTextResponse("Metrics disabled", status_code=404)
    return PlainTextResponse(get_metrics(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/ml/model-info", tags=["ML - Model Information"])
def model_info():
    """Get information about the loaded Landslide4Sense model."""
    global image_model_loader

    # Initialize loader if not already done
    if image_model_loader is None:
        try:
            from phase6.image_analysis.models.loader import Landslide4SenseModelLoader
            image_model_loader = Landslide4SenseModelLoader()
        except Exception:
            image_model_loader = None

    if image_model_loader is None:
        return {
            "available": False,
            "error": "Model loader not initialized",
            "model_path": None,
            "model_version": None,
            "checksum": None,
            "load_time_seconds": None
        }

    try:
        return image_model_loader.get_model_info()
    except Exception as e:
        # Handle any unexpected errors from the model loader
        return {
            "available": False,
            "error": f"Failed to get model info: {str(e)}",
            "model_path": None,
            "model_version": None,
            "checksum": None,
            "load_time_seconds": None
        }


@app.get("/api/drift/status", tags=["Drift Detection"])
def drift_status():
    """
    Get drift detection status for monitored models.

    Returns information about baseline availability and drift detection status.
    """
    import logging
    logger = logging.getLogger("error")
    try:
        from app.services.drift_monitor import check_drift_status
        return check_drift_status()
    except Exception as e:
        logger.error(f"Failed to get drift status: {e}")
        return {
            "enabled": False,
            "error": f"Failed to get drift status: {str(e)}",
            "baseline_available": False
        }