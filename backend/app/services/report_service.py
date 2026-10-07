from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.report import HazardReport, ReportStatus
from ..schemas.report import ReportCreate, ReportStatusUpdate

def generate_report_id(db: Session) -> str:
    """Generates a sequential human-readable report ID, e.g. LSR-2026-0004"""
    current_year = datetime.utcnow().year
    count = db.query(HazardReport).count() + 1
    return f"LSR-{current_year}-{count:04d}"

def create_report(
    db: Session,
    report_data: ReportCreate,
    image_path: Optional[str] = None
) -> HazardReport:
    """Stores a newly submitted citizen hazard report."""
    report_id = generate_report_id(db)

    db_report = HazardReport(
        report_id=report_id,
        user_id="citizen-anon",
        latitude=report_data.latitude,
        longitude=report_data.longitude,
        location_name=report_data.location_name or f"Coordinates ({report_data.latitude:.4f}, {report_data.longitude:.4f})",
        hazard_type=report_data.hazard_type,
        description=report_data.description,
        severity=report_data.severity,
        image_path=image_path,
        contact_name=report_data.contact_name,
        contact_phone=report_data.contact_phone,
        status=ReportStatus.PENDING.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_reports(
    db: Session,
    status: Optional[str] = None,
    hazard_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[HazardReport]:
    """Retrieves list of reports with optional filtering."""
    query = db.query(HazardReport)
    if status:
        query = query.filter(HazardReport.status == status.upper())
    if hazard_type:
        query = query.filter(HazardReport.hazard_type.ilike(f"%{hazard_type}%"))
    return query.order_by(HazardReport.created_at.desc()).offset(offset).limit(limit).all()

def get_report_by_id(db: Session, report_id: str) -> HazardReport:
    """Fetches a specific hazard report by report_id or database id."""
    report = db.query(HazardReport).filter(
        (HazardReport.report_id == report_id) | (HazardReport.id == int(report_id) if report_id.isdigit() else False)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Hazard report '{report_id}' not found.")
    return report

def update_report_status(db: Session, report_id: str, status_update: ReportStatusUpdate) -> HazardReport:
    """Updates the processing status of a report (for authority review)."""
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
    return report