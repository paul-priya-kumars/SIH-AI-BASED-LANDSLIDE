import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Landslide Monitoring & Early Warning System"
    VERSION: str = "1.0.0-phase1"
    DESCRIPTION: str = "Production-ready foundation for landslide risk monitoring, early alerts, and citizen hazard reporting."
    API_V1_STR: str = "/api"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./landslide.db"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10

    # Real Phase 3 M1 artifact is present -> prefer it. Set to True to force the
    # heuristic mock risk path (the M1 artifact is then reported as "mock").
    MOCK_M1_ML: bool = False
    MOCK_M2_GIS: bool = True

    # Observability settings
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = "INFO"

    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ENTRIES: int = 1000

    # Batch settings
    BATCH_MAX_SIZE: int = 100

    # Rate limiting settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Drift detection settings
    DRIFT_ENABLED: bool = False
    DRIFT_WINDOW_SIZE: int = 100
    DRIFT_THRESHOLD: float = 0.2

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()