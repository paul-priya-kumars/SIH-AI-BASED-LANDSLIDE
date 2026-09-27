from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alert import Alert
from ..schemas.alert import AlertResponse, AlertCreate

router = APIRouter(tags=["Alerts & Warnings"])

@router.get("/alerts", response_model=List[AlertResponse], summary="Get active landslide alerts and warnings")
def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MODERATE, HIGH, CRITICAL"),
    active_only: bool = Query(True, description="Filter only active alerts"),
    db: Session = Depends(get_db)
):
    """
    Returns active disaster advisories and warnings for communities.
    """
    query = db.query(Alert)
    if active_only:
        query = query.filter(Alert.is_active == True)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    return query.order_by(Alert.issued_at.desc()).all()

@router.get("/alerts/{alert_id}", response_model=AlertResponse, summary="Get details for a single alert")
def get_single_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return alert