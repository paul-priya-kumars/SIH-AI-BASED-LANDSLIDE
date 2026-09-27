from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import time
import logging

from ..database import get_db
from ..schemas.batch import BatchRiskPredictRequest, BatchRiskPredictResponse
from ..schemas.risk import RiskPredictionResponse
from ..services.risk_service import batch_risk_predict
from ..logging import generate_request_id
from ..metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    EXCEPTION_TOTAL
)
from ..config import settings

router = APIRouter(tags=["Batch Risk Assessment"])

logger = logging.getLogger(__name__)


@router.post("/batch/risk", response_model=BatchRiskPredictResponse, summary="Get batch landslide risk predictions for multiple locations")
def get_batch_risk_predictions(
    request: BatchRiskPredictRequest,
    request_id: str = Depends(generate_request_id)
):
    """
    Returns landslide risk predictions for multiple coordinates in a single request.
    Optimized to reuse cached predictions and minimize redundant computations.

    Phase 1: Uses cached predictions where available, computes only cache misses.
    Phase 2: Will leverage M1 AI/ML inference for uncached predictions.
    """
    start_time = time.time()

    try:
        # Validate batch size against configured maximum
        if len(request.coordinates) > settings.BATCH_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds maximum allowed size of {settings.BATCH_MAX_SIZE}"
            )

        # Call the batch service
        predictions = batch_risk_predict(request.coordinates)

        # Calculate latency
        latency = time.time() - start_time
        latency_ms = round(latency * 1000, 2)

        # Update metrics
        HTTP_REQUESTS_TOTAL.labels(
            method="POST",
            endpoint="/api/batch/risk",
            http_status=status.HTTP_200_OK
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method="POST",
            endpoint="/api/batch/risk"
        ).observe(latency)

        # Log the request
        logger.info(
            "Batch risk prediction request processed",
            extra={
                "request_id": request_id,
                "endpoint": "/api/batch/risk",
                "method": "POST",
                "status_code": status.HTTP_200_OK,
                "latency_ms": latency_ms,
                "batch_size": len(request.coordinates)
            }
        )

        return BatchRiskPredictResponse(predictions=predictions)

    except HTTPException:
        # Re-raise HTTP exceptions to let FastAPI handle them
        raise
    except Exception as e:
        # Calculate latency for error case
        latency = time.time() - start_time
        latency_ms = round(latency * 1000, 2)

        # Update error metrics
        EXCEPTION_TOTAL.labels(exception_type=type(e).__name__).inc()
        HTTP_REQUESTS_TOTAL.labels(
            method="POST",
            endpoint="/api/batch/risk",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method="POST",
            endpoint="/api/batch/risk"
        ).observe(latency)

        # Log the error
        logger.error(
            "Batch prediction request failed",
            extra={
                "request_id": request_id,
                "endpoint": "/api/batch/risk",
                "method": "POST",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "latency_ms": latency_ms,
                "batch_size": len(request.coordinates) if hasattr(request, 'coordinates') else 0,
                "error": str(e)
            }
        )

        # Return safe error response (no internal details exposed)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "details": {},
                "request_id": request_id
            }
        )