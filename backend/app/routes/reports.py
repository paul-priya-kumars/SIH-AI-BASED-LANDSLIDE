from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, Query, HTTPException, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.report import HazardReport
from ..schemas.report import ReportCreate, ReportResponse, ReportStatusUpdate
from ..services.report_service import (
    create_report,
    get_reports,
    get_report_by_id,
    update_report_status
)
from ..utils.file_upload import save_uploaded_image

router = APIRouter(tags=["Citizen Hazard Reports"])

def _enrich_report_response(report: HazardReport, request: Request) -> ReportResponse:
    """Helper to attach public image_url to ReportResponse."""
    image_url = None
    if report.image_path:
        base_url = str(request.base_url).rstrip("/")
        # format: http://127.0.0.1:8000/uploads/filename.jpg
        image_url = f"{base_url}/{report.image_path}"

    return ReportResponse(
        id=report.id,
        report_id=report.report_id,
        user_id=report.user_id,
        latitude=report.latitude,
        longitude=report.longitude,
        location_name=report.location_name,
        hazard_type=report.hazard_type,
        description=report.description,
        severity=report.severity,
        image_path=report.image_path,
        image_url=image_url,
        contact_name=report.contact_name,
        contact_phone=report.contact_phone,
        status=report.status,
        created_at=report.created_at,
        updated_at=report.updated_at
    )

@router.post("/reports", response_model=ReportResponse, summary="Submit a citizen hazard report with optional photograph")
async def submit_hazard_report(
    request: Request,
    latitude: float = Form(..., description="Latitude coordinate of observed hazard"),
    longitude: float = Form(..., description="Longitude coordinate of observed hazard"),
    hazard_type: str = Form(..., description="Category: Road crack, Rockfall, Landslide, etc."),
    description: str = Form(..., min_length=5, description="Observation details"),
    severity: str = Form("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL"),
    location_name: Optional[str] = Form(None),
    contact_name: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Citizens submit field observations regarding cracks, soil shifts, and debris.
    Validates photograph format and saves to local upload storage.
    """
    image_path = None
    if image and image.filename:
        saved_path, _ = await save_uploaded_image(image)
        image_path = saved_path

    report_create = ReportCreate(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        hazard_type=hazard_type,
        description=description,
        severity=severity,
        contact_name=contact_name,
        contact_phone=contact_phone
    )

    db_report = create_report(db, report_create, image_path=image_path)
    return _enrich_report_response(db_report, request)

@router.get("/reports", response_model=List[ReportResponse], summary="Retrieve submitted citizen reports")
def list_hazard_reports(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status: PENDING, UNDER_REVIEW, VERIFIED, REJECTED, RESOLVED"),
    hazard_type: Optional[str] = Query(None, description="Filter by hazard category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    reports = get_reports(db, status=status, hazard_type=hazard_type, limit=limit, offset=offset)
    return [_enrich_report_response(r, request) for r in reports]

@router.get("/reports/{report_id}", response_model=ReportResponse, summary="Get details of a single report")
def get_single_report(report_id: str, request: Request, db: Session = Depends(get_db)):
    report = get_report_by_id(db, report_id)
    return _enrich_report_response(report, request)

@router.patch("/reports/{report_id}/status", response_model=ReportResponse, summary="Update report status (Authority)")
def change_report_status(
    report_id: str,
    status_update: ReportStatusUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    report = get_report_by_id(db, report_id)

    valid_statuses = [s.value for s in ReportStatus]
    if status_update.status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status_update.status}'. Allowed: {', '.join(valid_statuses)}"
        )

    report.status = status_update.status.upper()
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)
    return _enrich_report_response(report, request)