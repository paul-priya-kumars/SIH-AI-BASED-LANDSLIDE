-- Landslide AI Monitoring and Early Warning System
-- Phase 1 Database Schema (SQLite compatible; easily convertible to PostgreSQL/PostGIS)

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id VARCHAR(32) NOT NULL UNIQUE,
    user_id VARCHAR(64),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    location_name VARCHAR(255),
    hazard_type VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    image_path VARCHAR(512),
    contact_name VARCHAR(128),
    contact_phone VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_report_id ON reports(report_id);
CREATE INDEX IF NOT EXISTS idx_reports_lat_long ON reports(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id VARCHAR(32) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(32) NOT NULL,
    location VARCHAR(255) NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    recommended_action TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_id ON alerts(alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_is_active ON alerts(is_active);

CREATE TABLE IF NOT EXISTS risk_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    risk_level VARCHAR(32) NOT NULL,
    risk_probability REAL NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    radius_meters REAL DEFAULT 1000.0,
    polygon_geojson TEXT,
    rainfall_mm REAL DEFAULT 0.0 NOT NULL,
    slope_deg REAL DEFAULT 0.0 NOT NULL,
    elevation_m REAL DEFAULT 0.0 NOT NULL,
    soil_type VARCHAR(128),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_risk_zones_zone_id ON risk_zones(zone_id);
CREATE INDEX IF NOT EXISTS idx_risk_zones_risk_level ON risk_zones(risk_level);
