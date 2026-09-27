# GeoShield AI — Landslide Monitoring & Early Warning System

[![Phase](https://img.shields.io/badge/Phase-1%20Foundation-orange)](docs/API.md)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.12-blue)](backend/)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20TypeScript%20%7C%20Vite%20%7C%20Tailwind-emerald)](frontend/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20SQLAlchemy%202.0-indigo)](database/schema.sql)

---

## 1. Project Purpose

**GeoShield AI** is an intelligent early warning and disaster response system designed for mountainous and slope-failure-prone regions (such as the Nilgiris, Western Ghats, and Himalayas). 

The platform allows citizens and disaster response authorities to:
1. View live landslide risk probability and threat level gauges.
2. Interactively explore spatial GIS hazard zonation perimeters, slope gradients, and rainfall thresholds on a Leaflet map.
3. Assess travel route safety between mountain passes, identifying high-risk hairpins and recommended transit bypasses.
4. Report ground fissures, rockfalls, and mudslides with photograph uploads and automated GPS coordinate capture.
5. Browse citizen observation histories with real-time status tracking (`PENDING` → `UNDER REVIEW` → `VERIFIED` → `RESOLVED`).
6. Receive instantaneous emergency warning broadcasts and safety advisories.

---

## 2. System Architecture & Role Boundaries

The project is architected with three distinct modules:
- **M1 (AI / ML Team)**: Predictive machine learning models, image intelligence, and risk classification.
- **M2 (GIS / Spatial Data Team)**: Digital Elevation Models (DEM), slope analysis, precipitation radar, and spatial hazard polygons.
- **M3 (Full-Stack Platform — THIS CODEBASE)**: Web application, UI/UX, REST APIs, database persistence, citizen reporting, file storage, and isolated integration contracts.

```
                  ┌───────────────────────────────┐
                  │    Citizen / Emergency User   │
                  └───────────────┬───────────────┘
                                  │ Browser (HTTP / GPS)
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                      │
│  ├── Dashboard (Live Risk Gauge, Telemetry Cards, Alerts)        │
│  ├── Interactive Risk Map (Leaflet GIS Layers & Popups)          │
│  ├── Route Safety Analyzer (Comparative Corridor Evaluation)     │
│  └── Hazard Reporting (Photo Upload, GPS Auto-fill, Validation)   │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ REST API / JSON / Multipart Form
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI / ASGI)                     │
│  ├── Routers: /api/risk, /api/environment, /api/alerts, etc.     │
│  ├── Storage: /backend/uploads/ for field photos                 │
│  ├── Services Layer:                                             │
│  │   ├── risk_service.py        ───► [M1 AI/ML Swap Point]       │
│  │   ├── environment_service.py ───► [M2 GIS Swap Point]         │
│  │   ├── route_service.py                                        │
│  │   └── report_service.py                                       │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ SQLAlchemy 2.0 ORM
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│                      DATABASE (SQLite / PostGIS)                 │
│  Tables: reports, alerts, risk_zones (Auto-initialized on boot)  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4 with custom Disaster Theme & Glassmorphism
- **Routing**: React Router DOM v7
- **Mapping**: Leaflet + React Leaflet
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Server**: Uvicorn ASGI
- **Data Validation**: Pydantic v2
- **ORM & Database**: SQLAlchemy 2.0 with SQLite (`landslide.db`)
- **Multipart Uploads**: `python-multipart`

---

## 4. Folder Structure

```
landslide-ai/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/       # Header, Navigation, Footer, States
│   │   │   ├── dashboard/    # RiskCard, RiskBadge, EnvironmentalCard, LocationCard
│   │   │   ├── map/          # MapView, ZoneDetailModal
│   │   │   └── reports/      # ReportCard, StatusBadge, ReportDetailModal
│   │   ├── pages/            # Home, RiskMap, RouteSafety, ReportHazard, ReportsHistory, Alerts
│   │   ├── layouts/          # MainLayout
│   │   ├── services/         # api.ts (Typed client with offline fallbacks)
│   │   ├── hooks/            # useGeolocation.ts (GPS + fallback)
│   │   ├── types/            # index.ts (TypeScript interfaces)
│   │   ├── data/             # mockData.ts (Centralized fallback fixtures)
│   │   ├── App.tsx           # Route declarations
│   │   ├── main.tsx          # Application entrypoint
│   │   └── index.css         # Tailwind & theme styles
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint, CORS, static mounts
│   │   ├── config.py         # App settings & environment loader
│   │   ├── database.py       # Engine, SessionLocal, and DB seeder
│   │   ├── models/           # HazardReport, Alert, RiskZone
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routes/           # risk, environment, alerts, reports, routes, ml_contract
│   │   ├── services/         # Isolated business logic & M1/M2 hooks
│   │   └── utils/            # Image validation and storage
│   ├── uploads/              # Stored citizen hazard photographs
│   ├── requirements.txt
│   └── README.md
│
├── database/
│   └── schema.sql            # Exportable database schema
│
├── docs/
│   ├── API.md                # Complete REST API documentation
│   ├── M1_INTEGRATION.md     # AI/ML contract documentation
│   └── M2_INTEGRATION.md     # GIS and spatial data contract documentation
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ (Node 24 recommended)
- npm or yarn

### 1. Backend Setup & Startup

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# or Linux / macOS:
# source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start backend development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be accessible at:
- **API Base**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

*Note: On first startup, the database `backend/landslide.db` is automatically created and populated with demo alerts, hazard zones, and reports.*

---

### 2. Frontend Setup & Startup

```bash
# In a new terminal, navigate to frontend folder
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Frontend will be accessible at:
- **Web App**: [http://localhost:5173](http://localhost:5173)

---

## 6. Environment Variables (`.env`)

Copy `.env.example` to `backend/.env`:

```env
PORT=8000
HOST=0.0.0.0
DEBUG=True
DATABASE_URL=sqlite:///./landslide.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
MOCK_M1_ML=True
MOCK_M2_GIS=True
```

---

## 7. Key REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/risk?latitude={lat}&longitude={lon}` | Predicts landslide threat level & probability |
| `GET` | `/api/environment?latitude={lat}&longitude={lon}` | Environmental telemetry (Rainfall, Slope, NDVI) |
| `GET` | `/api/risk-zones` | GIS hazard zones for Leaflet map overlay |
| `GET` | `/api/route-risk?start={loc}&destination={dest}` | Travel route hazard comparative assessment |
| `GET` | `/api/alerts` | Active civil defense landslide advisories |
| `POST`| `/api/reports` | Citizen hazard report submission (with photo upload) |
| `GET` | `/api/reports` | List submitted hazard reports |
| `GET` | `/api/reports/{id}` | Get report by ID |
| `PATCH`| `/api/reports/{id}/status` | Authority status update (`PENDING`, `VERIFIED`, etc.) |
| `POST`| `/api/ml/predict` | M1 Machine Learning prediction contract endpoint |

Full documentation: See [`docs/API.md`](docs/API.md).

---

## 8. M1 & M2 Integration Contracts

- **M1 (AI / Machine Learning)**:
  - Documented in [`docs/M1_INTEGRATION.md`](docs/M1_INTEGRATION.md).
  - Isolated in `backend/app/services/risk_service.py` (`get_risk_prediction`).
  - Contract endpoint: `POST /api/ml/predict`.
- **M2 (GIS, Terrain, Spatial Data)**:
  - Documented in [`docs/M2_INTEGRATION.md`](docs/M2_INTEGRATION.md).
  - Isolated in `backend/app/services/environment_service.py` (`get_environment_data`).
  - Contract endpoint: `GET /api/risk-zones`.

---

## 9. Troubleshooting

1. **Port 8000 in use**:
   Change `PORT=8001` in `.env` and adjust the proxy target in `frontend/vite.config.ts`.
2. **GPS Geolocation Denied**:
   The application automatically degrades gracefully to default mountain coordinates (Ooty Center) with a friendly notification banner.
3. **Uploaded Images 404**:
   Verify that `backend/uploads/` exists and the backend is running so the static file handler can serve `/uploads/{filename}`.
