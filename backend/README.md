# Landslide AI Monitoring & Early Warning System — Backend Service

FastAPI-powered asynchronous backend service delivering landslide hazard risk predictions, real-time weather/environmental telemetry, active emergency bulletins, and citizen field reports.

---

## Tech Stack
- **Framework**: FastAPI (Python 3.12+)
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite (SQLAlchemy 2.0 ORM) — designed for seamless migration to PostgreSQL/PostGIS in Phase 2
- **Validation**: Pydantic v2
- **Static Assets**: Uvicorn static files mount for `/uploads`

---

## Directory Layout
```
backend/
├── app/
│   ├── main.py              # FastAPI app definition & lifespan hooks
│   ├── config.py            # Environment & app configuration
│   ├── database.py          # SQLAlchemy engine, session maker & seed initialization
│   ├── models/              # Database entities (HazardReport, Alert, RiskZone)
│   ├── schemas/             # Pydantic request/response models
│   ├── routes/              # REST route controllers
│   ├── services/            # Business logic & M1/M2 service integration hooks
│   └── utils/               # File upload validation and helpers
├── uploads/                 # Uploaded citizen hazard photos
├── requirements.txt         # Pinned Python dependencies
└── landslide.db             # Local SQLite database (auto-seeded on startup)
```

---

## Setup & Running

### 1. Create Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API Documentation:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
