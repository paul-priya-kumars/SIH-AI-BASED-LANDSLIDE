"""
M2 GIS / Spatial Provider Boundary
==================================
Defines the *replaceable* interface through which the risk engine obtains the
spatial context (risk zone) for a coordinate.

Reality check (audited 2026-10-08)
----------------------------------
No genuine GIS vector dataset (shapefiles / GeoJSON hazard polygons / DEM) is
bundled in this repository. The ``risk_zones`` table is populated with Phase-1
seed rows created by ``backend/app/database.py`` for UI development.

Therefore the bundled provider is **explicitly a demo adapter**: it is honest
about ``is_real=False`` and ``data_source``, and it never pretends the seed
rows are authoritative geospatial data. A real implementation only has to
satisfy :class:`GisProvider` and be returned by :func:`get_gis_provider`.
"""

from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from ..config import settings

logger = logging.getLogger(__name__)

EARTH_RADIUS_M = 6_371_000.0


@dataclass
class SpatialContext:
    """Result of mapping a coordinate to a spatial risk zone."""

    latitude: float
    longitude: float
    zone_id: Optional[str]
    name: Optional[str]
    risk_level: Optional[str]
    risk_probability: Optional[float]
    distance_m: Optional[float]
    inside_zone: bool
    provider: str
    is_real: bool
    data_source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@runtime_checkable
class GisProvider(Protocol):
    """Replaceable spatial-context provider. Implement this to plug in real GIS."""

    name: str
    is_real: bool

    def describe(self) -> Dict[str, Any]:
        ...

    def find_zone(self, latitude: float, longitude: float) -> SpatialContext:
        ...


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


class RiskZoneSeedGisProvider:
    """
    DEMO adapter: nearest seeded risk zone from the application database.

    ``is_real`` is hard-coded ``False`` and ``data_source`` states plainly that
    the zones are seed/demo rows, so nothing downstream can mistake this for
    real GIS data.
    """

    name = "RISK_ZONE_SEED_PROVIDER"
    is_real = False
    data_source = "SEED_DEMO_RISK_ZONES (not real GIS vector data)"

    def _load_zones(self) -> list:
        try:
            from ..database import SessionLocal
            from ..models.risk_zone import RiskZone

            db = SessionLocal()
            try:
                return db.query(RiskZone).all()
            finally:
                db.close()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("GIS provider could not read risk zones: %s", exc)
            return []

    def find_zone(self, latitude: float, longitude: float) -> SpatialContext:
        zones = self._load_zones()
        best = None
        best_dist = None

        for zone in zones:
            dist = _haversine_m(latitude, longitude, float(zone.latitude), float(zone.longitude))
            if best_dist is None or dist < best_dist:
                best, best_dist = zone, dist

        if best is None:
            return SpatialContext(
                latitude=latitude,
                longitude=longitude,
                zone_id=None,
                name=None,
                risk_level=None,
                risk_probability=None,
                distance_m=None,
                inside_zone=False,
                provider=self.name,
                is_real=self.is_real,
                data_source=self.data_source,
            )

        radius = float(getattr(best, "radius_meters", 0.0) or 0.0)
        return SpatialContext(
            latitude=latitude,
            longitude=longitude,
            zone_id=best.zone_id,
            name=best.name,
            risk_level=best.risk_level,
            risk_probability=float(best.risk_probability) if best.risk_probability is not None else None,
            distance_m=round(best_dist, 2) if best_dist is not None else None,
            inside_zone=bool(best_dist is not None and best_dist <= radius),
            provider=self.name,
            is_real=self.is_real,
            data_source=self.data_source,
        )

    def describe(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "is_real": self.is_real,
            "data_source": self.data_source,
            "zone_count": len(self._load_zones()),
            "note": "Replace with a real GIS provider implementing GisProvider to use genuine vector data.",
        }


_default_provider: Optional[GisProvider] = None


def get_gis_provider() -> GisProvider:
    """Return the configured GIS provider (demo adapter until a real one is wired)."""
    global _default_provider
    if _default_provider is None:
        # MOCK_M2_GIS=True documents that the bundled provider is a demo adapter.
        _default_provider = RiskZoneSeedGisProvider()
        logger.info("GIS provider initialised: %s (is_real=%s)", _default_provider.name, _default_provider.is_real)
    return _default_provider


def set_gis_provider(provider: Optional[GisProvider]) -> None:
    """Override the provider (used by tests / future real GIS integration)."""
    global _default_provider
    _default_provider = provider
