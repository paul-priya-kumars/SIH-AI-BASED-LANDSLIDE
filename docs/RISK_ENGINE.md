# GeoShield AI — Risk Engine

How the system turns a latitude/longitude into a final landslide risk, and
exactly which parts are real versus demo/mock. **Nothing here is fabricated:**
every component declares its own availability and provenance.

## Pipeline

```
latitude/longitude
      │
      ├─► M2 environment provider ──► 8-feature vector ──► M1 environmental model
      │        (mock, is_mock=True)     (real contract)      (REAL Phase 3 artifact)
      │                                            └─► environmental probability + level
      │
      ├─► M2 GIS provider (risk-zone lookup) ──────► spatial probability + level
      │        (DEMO adapter, is_real=False)
      │
      └─► M3 satellite model (explicit patch only) ─► satellite probability
               (REAL U-Net checkpoint)
                    │
                    ▼
        weight-renormalised combination ──► final probability + level
```

## M1 — environmental model (REAL)

* **Artifact:** `phase3/model_training/risk_model.joblib`
* **Type:** `sklearn.pipeline.Pipeline` = `StandardScaler` → `RandomForestClassifier`
  (`n_estimators=100`, `class_weight="balanced"`, `random_state=42`)
* **Produced by:** `phase3/model_training/train_model.py`
* **Feature order (fixed):**

  | # | feature | source |
  |---|---------|--------|
  | 1 | `rainfall_mm` | M2 environment provider (mock) |
  | 2 | `soil_moisture_pct` ← `soil_saturation_pct` | M2 environment provider (mock) |
  | 3 | `slope_deg` | M2 environment provider (mock) |
  | 4 | `elevation_m` | M2 environment provider (mock) |
  | 5 | `temperature_c` | M2 environment provider (mock) |
  | 6 | `river_level_m` | M2 environment provider (mock) |
  | 7 | `vegetation_index` ← `ndvi` | M2 environment provider (mock) |
  | 8 | `landslide_history` | M2 environment provider (mock) |

* **Output mapping (documented, deterministic):**
  * `risk_probability` = `P(class == HIGH)`
  * `confidence` = max class probability, taken from the model itself
  * `risk_level` = predicted class, with `MEDIUM → MODERATE`
  * `probabilities` = the model's full class distribution
* **Honest caveat:** the model is genuinely trained and executed, but the
  training set (`phase3/dataset/train_dataset.csv`) is a **12-row synthetic
  demo dataset**, so its probabilities are demo-grade, not validated
  real-world performance. Missing features raise an error — they are never
  invented.

## M2 — spatial / GIS (INTERFACE + DEMO ADAPTER)

* **Interface:** `backend/app/services/gis_provider.py::GisProvider`
* **Bundled provider:** `RiskZoneSeedGisProvider` with `is_real = False` and
  `data_source = "SEED_DEMO_RISK_ZONES (not real GIS vector data)"`
* **Mapping:** nearest seeded `risk_zones` row by haversine distance, with an
  `inside_zone` flag computed against the zone radius.
* **Honest caveat:** no genuine GIS vector dataset (shapefiles / GeoJSON hazard
  polygons / DEM) is bundled. Replace the provider by calling
  `set_gis_provider(...)` with any object satisfying `GisProvider`.

## M3 — satellite image model (REAL, but not per-coordinate)

* **Artifact:** `phase6/image_analysis/checkpoints/best_model.pth`
* **Architecture:** `UNetResNet34` (ResNet-34 encoder, 14 input channels,
  1 output channel); checkpoint records `epoch=45`, `best_val_dice≈0.8032`
* **Preprocessing:** `Landslide4SensePreprocessor` reconstructed from the
  checkpoint's fitted `band_means` / `band_stds`
* **Honest caveat:** the Landslide4Sense patches carry **no geographic
  metadata**, so there is no coordinate → patch mapping. M3 therefore never
  contributes to a per-coordinate score; it is exposed only for explicit patch
  input (`POST /api/ml/m3/predict`, or `image_patch_path` on the composite
  endpoint). See `coordinate_mapping_status()`.

## Composite combination (documented)

`backend/app/services/composite_risk_service.py`:

```
final = Σ(wᵢ · pᵢ) / Σ(wᵢ)     over components that are AVAILABLE only
```

| component | weight |
|-----------|--------|
| `environmental_m1` | 0.5 |
| `spatial_m2` | 0.3 |
| `satellite_m3` | 0.2 |

* Unavailable components are removed from **both** numerator and denominator —
  they are never substituted with an invented value.
* If no component is available, `final_risk.available = false` and
  `probability = null`.
* `final_level` thresholds: `≥0.75 VERY_HIGH`, `≥0.55 HIGH`, `≥0.35 MODERATE`,
  else `LOW`.

## Endpoints

| endpoint | purpose |
|----------|---------|
| `GET /api/health` | per-model availability (`environmental_m1`, `satellite_m3`) |
| `GET /api/ml/models/status` | detailed M1/M3 metadata + M3 coordinate-mapping status |
| `GET /api/risk` | M1-driven risk for a coordinate (real model, `is_mock=false`) |
| `GET /api/risk/composite` | M1 + M2 + M3 composite with per-component provenance |
| `GET /api/gis/zone` | coordinate → spatial context via the GIS provider |
| `POST /api/ml/m3/predict` | real U-Net segmentation on an uploaded `.h5` patch |

The pre-existing heuristic paths (environment mock, route mock, M1-mock
fallback) are unchanged and still report `is_mock = true`.
