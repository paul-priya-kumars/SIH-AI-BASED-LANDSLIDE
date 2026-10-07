from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database schema and populates mock demonstration data for Phase 1."""
    from .models.report import HazardReport
    from .models.alert import Alert
    from .models.risk_zone import RiskZone

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if alerts already exist
        if db.query(Alert).count() == 0:
            demo_alerts = [
                Alert(
                    alert_id="ALT-2026-001",
                    title="Flash Landslide Warning: Ooty Ghat Road",
                    message="Heavy rainfall exceeding 145mm and saturated slope detected. High risk of debris flow.",
                    severity="CRITICAL",
                    location="Ooty - Coonoor Ghat Road (NH 181)",
                    latitude=11.3833,
                    longitude=76.7588,
                    issued_at=datetime.utcnow(),
                    recommended_action="Avoid unnecessary travel through high-risk slopes. Ghat road restricted to emergency vehicles only.",
                    is_active=True
                ),
                Alert(
                    alert_id="ALT-2026-002",
                    title="Slope Instability Advisory: Kotagiri Highway",
                    message="Ground sensor movement of 4.2mm detected after continuous downpour.",
                    severity="HIGH",
                    location="Kotagiri Slopes km 18",
                    latitude=11.4285,
                    longitude=76.8622,
                    issued_at=datetime.utcnow(),
                    recommended_action="Exercise extreme caution. Heavy vehicles diverted via Mettupalayam bypass.",
                    is_active=True
                ),
                Alert(
                    alert_id="ALT-2026-003",
                    title="Moderate Runoff Warning: Lovedale Valley",
                    message="Soil saturation level reached 84%. Minor surface mudslides reported.",
                    severity="MODERATE",
                    location="Lovedale Valley, Nilgiris",
                    latitude=11.3850,
                    longitude=76.7110,
                    issued_at=datetime.utcnow(),
                    recommended_action="Local residents in low-lying terrace slopes advised to monitor retaining walls.",
                    is_active=True
                ),
                Alert(
                    alert_id="ALT-2026-004",
                    title="Precautionary Notice: Avalanche Lake Route",
                    message="Intermittent rainfall with elevated soil moisture in upper catchment.",
                    severity="LOW",
                    location="Avalanche Lake Access Corridor",
                    latitude=11.3120,
                    longitude=76.6020,
                    issued_at=datetime.utcnow(),
                    recommended_action="Routine monitoring in place. Standard advisory for tourists to stick to paved paths.",
                    is_active=True
                ),
                Alert(
                    alert_id="ALT-2026-005",
                    title="Critical Hazard Alert: Gudalur Mountain Pass",
                    message="Massive boulder displacement reported along steep cut slope.",
                    severity="CRITICAL",
                    location="Gudalur Pass (State Highway 17)",
                    latitude=11.5074,
                    longitude=76.4922,
                    issued_at=datetime.utcnow(),
                    recommended_action="Immediate route closure in effect. National Disaster Response Force deployed.",
                    is_active=True
                )
            ]
            db.add_all(demo_alerts)

        # Check if risk zones exist
        if db.query(RiskZone).count() == 0:
            demo_zones = [
                RiskZone(
                    zone_id="ZONE-OOTY-CENTRAL",
                    name="Ooty Urban Valley Slope",
                    risk_level="VERY_HIGH",
                    risk_probability=0.82,
                    latitude=11.4102,
                    longitude=76.6950,
                    radius_meters=1800.0,
                    rainfall_mm=145.0,
                    slope_deg=37.0,
                    elevation_m=2240.0,
                    soil_type="Colluvial clay with weathered gneiss",
                    polygon_geojson='{"type":"Polygon","coordinates":[[[76.685,11.400],[76.705,11.400],[76.705,11.420],[76.685,11.420],[76.685,11.400]]]}'
                ),
                RiskZone(
                    zone_id="ZONE-COONOOR-GHAT",
                    name="Coonoor Gorge & Hairpin Slopes",
                    risk_level="HIGH",
                    risk_probability=0.74,
                    latitude=11.3530,
                    longitude=76.7959,
                    radius_meters=2200.0,
                    rainfall_mm=128.0,
                    slope_deg=41.0,
                    elevation_m=1850.0,
                    soil_type="Residual lateritic soil over charnockite",
                    polygon_geojson='{"type":"Polygon","coordinates":[[[76.780,11.340],[76.810,11.340],[76.810,11.365],[76.780,11.365],[76.780,11.340]]]}'
                ),
                RiskZone(
                    zone_id="ZONE-KOTAGIRI-EAST",
                    name="Kotagiri Eastern Ridge",
                    risk_level="MODERATE",
                    risk_probability=0.58,
                    latitude=11.4285,
                    longitude=76.8622,
                    radius_meters=1500.0,
                    rainfall_mm=94.0,
                    slope_deg=28.0,
                    elevation_m=1790.0,
                    soil_type="Red sandy loam with high drainage capacity",
                    polygon_geojson='{"type":"Polygon","coordinates":[[[76.850,11.415],[76.875,11.415],[76.875,11.440],[76.850,11.440],[76.850,11.415]]]}'
                ),
                RiskZone(
                    zone_id="ZONE-PYKARA-BASIN",
                    name="Pykara Waterfalls Escarpment",
                    risk_level="LOW",
                    risk_probability=0.22,
                    latitude=11.4550,
                    longitude=76.5980,
                    radius_meters=1200.0,
                    rainfall_mm=45.0,
                    slope_deg=18.0,
                    elevation_m=2060.0,
                    soil_type="Stable granitic basement with thick forest cover",
                    polygon_geojson='{"type":"Polygon","coordinates":[[[76.585,11.445],[76.610,11.445],[76.610,11.465],[76.585,11.465],[76.585,11.445]]]}'
                ),
                RiskZone(
                    zone_id="ZONE-GUDALUR-PASS",
                    name="Gudalur Mudumalai Escarpment",
                    risk_level="VERY_HIGH",
                    risk_probability=0.88,
                    latitude=11.5074,
                    longitude=76.4922,
                    radius_meters=2500.0,
                    rainfall_mm=162.0,
                    slope_deg=44.0,
                    elevation_m=1120.0,
                    soil_type="Unconsolidated debris over fractured gneiss",
                    polygon_geojson='{"type":"Polygon","coordinates":[[[76.475,11.490],[76.510,11.490],[76.510,11.525],[76.475,11.525],[76.475,11.490]]]}'
                ),
                RiskZone(
                    zone_id="ZONE-DODDABETTA-PEAK",
                    name="Doddabetta Upper Shola Ridgeline",
                    risk_level="LOW",
                    risk_probability=0.18,
                    latitude=11.4010,
                    longitude=76.7350,
                    radius_meters=1400.0,
                    rainfall_mm=62.0,
                    slope_deg=22.0,
                    elevation_m=2637.0,
                    soil_type="Organic montane humic layer",
                    polygon_geojson='{"type":"Polygon","coordinates":[[[76.720,11.390],[76.750,11.390],[76.750,11.412],[76.720,11.412],[76.720,11.390]]]}'
                )
            ]
            db.add_all(demo_zones)

        # Check if initial citizen reports exist
        if db.query(HazardReport).count() == 0:
            demo_reports = [
                HazardReport(
                    report_id="LSR-2026-0001",
                    user_id="citizen-402",
                    latitude=11.4125,
                    longitude=76.6980,
                    location_name="Ooty - Fern Hill Road",
                    hazard_type="Road crack",
                    description="Deep longitudinal fissure extending 15 meters along the asphalt shoulder after intense morning rain. Sinking evident.",
                    severity="HIGH",
                    image_path=None,
                    contact_name="Arun Kumar",
                    contact_phone="+91 98401 23456",
                    status="UNDER_REVIEW",
                    created_at=datetime.utcnow()
                ),
                HazardReport(
                    report_id="LSR-2026-0002",
                    user_id="citizen-108",
                    latitude=11.3580,
                    longitude=76.7910,
                    location_name="Coonoor Valley km 7",
                    hazard_type="Rockfall",
                    description="Multiple melon-sized boulders tumbled down the retaining wall into the outer driving lane.",
                    severity="CRITICAL",
                    image_path=None,
                    contact_name="Divya Raman",
                    contact_phone="+91 97890 54321",
                    status="VERIFIED",
                    created_at=datetime.utcnow()
                ),
                HazardReport(
                    report_id="LSR-2026-0003",
                    user_id="citizen-751",
                    latitude=11.4250,
                    longitude=76.8580,
                    location_name="Kotagiri Tea Estate Slope",
                    hazard_type="Water seepage",
                    description="Unusual muddy water spring emerging from mid-slope embankment above residential cottages.",
                    severity="MEDIUM",
                    image_path=None,
                    contact_name="M. Selvam",
                    contact_phone=None,
                    status="PENDING",
                    created_at=datetime.utcnow()
                )
            ]
            db.add_all(demo_reports)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
