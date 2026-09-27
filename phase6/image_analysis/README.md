# Landslide4Sense Image AI Module

## Phase 1: Infrastructure Foundation

This module provides the infrastructure for a future REAL Landslide4Sense satellite-image AI model in the SIH AI-Based Landslide Early Warning System (GeoShield AI).

**IMPORTANT: This is INFRASTRUCTURE ONLY in Phase 1.**
- No Landslide4Sense dataset is accessed
- No model is trained
- No fake predictions are generated
- Actual image AI implementation occurs in Phase 2

---

### 🏗️ Architecture Overview

The system maintains strict technical separation between satellite and citizen photo AI:

```
Satellite Path (This Module):
Landslide4Sense (14-band, 128x128) 
        → Preprocessing 
        → U-Net Model (Future) 
        → Inference 
        → Risk Conversion 
        → Risk Engine

Citizen Photo Path (Separate Future Implementation):
Mobile Phone Photos (RGB, variable)
        → Preprocessing 
        → Classification Model (Future) 
        → Inference 
        → Risk Conversion 
        → Risk Engine
```

### 📁 Directory Structure

```
phase6/image_analysis/
├── preprocessing/
│   ├── __init__.py
│   └── landslide4sense.py          # Landslide4Sense-specific preprocessing
├── models/
│   ├── __init__.py
│   └── loader.py                   # Model loading abstraction
├── inference/
│   ├── __init__.py
│   └── engine.py                   # Inference interface
├── training/
│   └── # To be implemented in Phase 2
├── evaluation/
│   └── # To be implemented in Phase 2
├── tests/
│   ├── __init__.py
│   ├── test_preprocessing.py
│   ├── test_model_loader.py
│   ├── test_inference.py
│   ├── test_api.py
│   └── test_config.py
├── config.py                       # Environment-variable configuration
├── api.py                          # API endpoints implementation
└── README.md                       # This file
```

### 🔧 Configuration

All configuration is managed via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `JARVIS_IMAGE_AI_ENABLED` | Enable/disable image AI | `false` |
| `JARVIS_IMAGE_MODEL_PATH` | Path to model file | `./models/landslide4sense_unet/not_available` |
| `JARVIS_IMAGE_MODEL_VERSION` | Model version string | `not-available-phase1` |
| `JARVIS_LANDSLIDE4SENSE_DATASET_PATH` | Path to dataset root | `./datasets/landslide4sense` |
| `JARVIS_IMAGE_NORMALIZE_BANDS` | Apply band normalization | `true` |
| `JARVIS_IMAGE_PREDICTION_THRESHOLD` | Prediction threshold (0.0-1.0) | `0.5` |

### 🧩 Component Responsibilities

#### Preprocessing (`preprocessing/landslide4sense.py`)
- Validates input dimensions: 128×128 pixels with 14 bands
- Converts data to float32
- Provides interface for normalization statistics
- **Does NOT**: Access dataset, perform actual normalization, load files

#### Model Loading (`models/loader.py`)
- Checks model file availability
- Reports model version and status
- Handles missing models gracefully
- **In Phase 1**: Always reports model as unavailable
- **Does NOT**: Load actual models (none exist in Phase 1)

#### Inference (`inference/engine.py`)
- Coordinates preprocessing → inference → postprocessing
- **In Phase 1**: Returns controlled unavailability states
- **Does NOT**: Perform actual inference or return fake predictions
- Distinguishes between: disabled, unavailable, not-implemented, failure

#### API (`api.py`)
REST-like endpoints:
- `GET /api/v1/image/health` - Service status
- `POST /api/v1/image/predict` - Image prediction 
- `GET /api/v1/model/info` - Model information

**Phase 1 Responses**:
- Clearly indicates when AI is disabled
- Reports when model is not available (no fake predictions)
- States when inference is not implemented (Phase 1 limitation)
- Uses appropriate HTTP status code equivalents in response bodies

### 🚫 Phase 1 Restrictions

To maintain system integrity and preparation for future phases:

**DO NOT**:
- Access or download the Landslide4Sense dataset
- Train any models during Phase 1
- Create mock AI predictions or simulate outputs
- Modify existing M1/M2/M3/risk engine/frontend/database code
- Blend satellite and citizen photo AI processing paths
- Return fake LOW/MEDIUM/HIGH predictions
- Claim scientific optimality for default thresholds

**ALLOWED**:
- Infrastructure development and testing
- Configuration via environment variables
- API contracts defining future behavior
- Validation of interfaces without actual data
- Documentation of future implementation paths

### 📊 Expected Dataset: Landslide4Sense

When available in Phase 2:
- **Size**: 3,799 training / 245 validation / 800 test patches
- **Format**: 128×128 pixel patches
- **Bands**: 14 channels (Sentinel-2 multispectral + slope + DEM)
- **Labels**: Pixel-wise (0 = non-landslide, 1 = landslide)
- **License**: CC-BY-4.0 (requires attribution)
- **Usage**: Must provide attribution in all uses and derivatives

### 🏷️ Model Architecture (Phase 2 Planning)

**Recommended**: U-Net with ResNet34 encoder
- Input: (128, 128, 14) - height, width, bands
- Output: (128, 128, 1) - per-pixel landslide probability
- Activation: Sigmoid for pixel-wise probability
- Loss: Dice loss or focal loss (handles class imbalance)
- Optimizer: AdamW with learning rate scheduling

### 🔄 Risk Engine Integration

Image AI output integrates with existing risk engine as follows:
1. Model outputs per-pixel landslide probability (0.0-1.0)
2. Overall image probability = (pixels > threshold) / total pixels
3. Probability → risk level using M1-equivalent thresholds:
   - < 0.35 → LOW
   - 0.35-0.55 → MODERATE
   - 0.55-0.75 → HIGH
   - ≥ 0.75 → VERY_HIGH
4. Risk level fed to risk engine as `image_risk` parameter
5. Final risk = highest(ml_risk, route_risk, image_risk)

**No modifications needed** to existing risk engine - integration happens at API level.

### 🧪 Testing

Test suite validates:
- Configuration loading from environment variables
- Disabled AI behavior
- Missing model detection
- Model availability checking
- API unavailable responses
- Preprocessing interface
- Inference engine status reporting
- **All tests verify**: No fake predictions are returned

### 🔒 Backward Compatibility

Phase 1 implementation:
- Creates zero modifications to existing system files
- Maintains all existing M1/M2/M3/risk engine/frontend functionality
- Adds new capability in isolated `phase6/image_analysis/` directory
- Verified by running existing test suites before and after implementation

### 📝 Implementation Notes

**Naming Convention**: 
- Uses "Landslide4Sense" consistently (corrects common "Landsat4Sense" mistake)
- File: `preprocessing/landslide4sense.py` (not landsat4sense.py)

**Error Handling**:
- Distinct error codes for different unavailability states:
  - `IMAGE_AI_DISABLED`: AI turned off via configuration
  - `MODEL_NOT_AVAILABLE`: Model file missing/inaccessible
  - `NOT_IMPLEMENTED_PHASE1`: Infrastructure ready but inference not implemented (Phase 1)
  - `INVALID_INPUT`: Input validation fails
  - `INFERENCE_FAILURE`: Error during processing

**Future Readiness**:
- Infrastructure designed for seamless Phase 2 transition
- Configuration points to where model/dataset will be located
- API contracts designed for real implementation
- Clear documentation of limitations and next steps

---

### ⚠️ Phase 1 Limitations Clearly Stated

- **REAL IMAGE MODEL NOT TRAINED**
- **REAL IMAGE INFERENCE NOT ENABLED**
- **NO DATASET ACCESS IN PHASE 1**
- **NO MODEL LOADING IN PHASE 1**
- **NO PREDICTIONS GENERATED IN PHASE 1**

**READY FOR PHASE 2 WHEN**:
1. Landslide4Sense dataset is obtained and verified
2. Model is trained on Landslide4Sense training set
3. Trained model is placed at `JARVIS_IMAGE_MODEL_PATH`
4. `JARVIS_IMAGE_AI_ENABLED` is set to `true`

---

### 📖 References

- Landslide4Sense Dataset: [To be cited when dataset is obtained]
- U-Net: Ronneberger et al., 2015
- CC-BY-4.0 License: https://creativecommons.org/licenses/by/4.0/