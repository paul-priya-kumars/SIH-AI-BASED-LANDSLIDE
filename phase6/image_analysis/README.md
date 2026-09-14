# Landslide4Sense Image AI Module

## Purpose
This module provides the infrastructure for integrating real AI-based image analysis into the SIH AI-Based Landslide Early Warning System using the Landslide4Sense dataset.

**Important Notes:**
- M2 remains MOCK (using mock environmental data)
- Environmental M1 is REAL (trained Random Forest model)
- Image AI model is NOT YET TRAINED (Phase 1 infrastructure only)

## Landslide4Sense Data Type
The Landslide4Sense dataset provides:
- 3,799 training patches, 245 validation patches, 800 test patches
- 128x128 image patches
- 14 bands (Sentinel-2 multispectral bands + slope + DEM)
- Pixel-wise landslide/non-landslide labels (class 0 = non-landslide, class 1 = landslide)
- Official source: https://zenodo.org/records/10463239 (CC-BY-4.0 license)

## Why Satellite AI is Separate from Citizen-Photo AI
1. **Different Data Characteristics**:
   - Satellite: Multispectral (14 bands), consistent resolution (128x128), georeferenced
   - Citizen photos: RGB (3 bands), variable resolution/uncontrolled conditions, not georeferenced without explicit tagging

2. **Different Processing Requirements**:
   - Satellite: Requires handling of multispectral data, radiometric calibration, geometric correction
   - Citizen photos: Requires handling of variable lighting, perspective, occlusion, blur

3. **Different Model Architectures**:
   - Satellite: U-Net or similar segmentation model for pixel-wise landslide detection
   - Citizen photos: Classification model (CNN) to detect presence of landslide evidence

4. **Different Use Cases**:
   - Satellite: Regional monitoring, predictive analysis
   - Citizen photos: Ground truth validation, real-time citizen reporting

## Directory Structure
```
phase6/image_analysis/
├── api.py                  # API skeleton showing intended interface
├── config.py               # Configuration via environment variables
├── __init__.py             # Package initializer
│
├── preprocessing/          # Data preprocessing utilities
│   ├── __init__.py
│   └── landsat4sense.py    # Landslide4Sense-specific preprocessing
│
├── models/                 # Model loading and management
│   ├── __init__.py
│   └── loader.py           # Model loading abstraction
│
├── inference/              # Inference engine
│   ├── __init__.py
│   └── engine.py           # Inference interface
│
└── tests/                  # Test suite for Phase 1 infrastructure
    ├── __init__.py
    ├── test_preprocessing.py
    ├── test_model_loader.py
    ├── test_inference.py
    ├── test_config.py
    └── test_api.py
```

## Configuration
The module uses environment variables for configuration:

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `JARVIS_IMAGE_MODEL_PATH` | Path to trained model file | `./models/landsat4sense_unet/not_available` |
| `JARVIS_IMAGE_MODEL_VERSION` | Version identifier for the model | `not-available-phase1` |
| `JARVIS_IMAGE_AI_ENABLED` | Enable/disable image AI functionality | `false` |
| `JARVIS_LANDSLIDE4SENSE_DATASET_PATH` | Path to Landslide4Sense dataset | `./datasets/landsat4sense` |

Example usage:
```bash
export JARVIS_IMAGE_AI_ENABLED=true
export JARVIS_IMAGE_MODEL_PATH="./models/landsat4sense_unet/best_model.pth"
export JARVIS_IMAGE_MODEL_VERSION="landsat4sense_unet_v1.0"
```

## Model-Loading Design
The model loading abstraction (`phase6/image_analysis/models/loader.py`) provides:

1. **Availability Checking**: `is_model_available()` checks if model file exists
2. **Clear Error Handling**: Returns `ImageModelNotAvailableError` with message "IMAGE MODEL NOT AVAILABLE" when no model is found
3. **Model Caching**: Optional caching to avoid reloading large models
4. **Version Tracking**: Tracks model version for reproducibility
5. **Fallback Safety**: Default loader points to non-existent path to clearly indicate unavailability

## Preprocessing Design
The preprocessing abstraction (`phase6/image_analysis/preprocessing/landsat4sense.py`) provides:

1. **Dimension Validation**: Validates 128x128x14 tensor shape
2. **Band Count Validation**: Ensures exactly 14 bands
3. **Data Type Conversion**: Converts to float32 for numerical stability
4. **Normalization**: Optional per-band normalization (zero mean, unit variance)
5. **Extensible Interface**: Designed for easy implementation of actual loading in Phase 2

Note: Actual file loading (GeoTIFF, NPY, etc.) is not implemented in Phase 1 since the dataset is not downloaded.

## Future U-Net Training Flow (Phase 2)
1. Download Landslide4Sense dataset from Zenodo
2. Preprocess data using Landslide4SensePreprocessor
3. Split into training/validation/test sets (use official splits)
4. Implement U-Net model architecture suitable for 14-band input
5. Train with weighted cross-entropy loss (address class imbalance)
6. Validate using IoU (Jaccard index) and F1-score metrics
7. Save best model based on validation IoU
8. Export model to the configured model path

## Future Inference Flow (Phase 2)
1. Load image sample (GeoTIFF/NPY format)
2. Validate dimensions and band count
3. Preprocess using Landslide4SensePreprocessor
4. Load trained model using Landslide4SenseModelLoader
5. Run forward pass to get segmentation probability map
6. Post-process to extract:
   - Overall landslide probability (mean/max of probability map)
   - Confidence score (entropy-based or max probability)
   - Binary detection map (threshold at 0.5)
7. Return structured results matching expected interface

## Current Limitations (Phase 1)
- No actual image model exists (intentionally)
- No dataset downloading or preprocessing
- No actual inference capabilities
- All infrastructure components return controlled errors indicating unavailability
- API skeleton shows intended interface but is not connected to main system

## Dependencies for Phase 1
- numpy (added for Phase 1 infrastructure)

## Dependencies for Phase 2 (to be added)
- torch (PyTorch for U-Net implementation)
- rasterio or tifffile (for GeoTIFF handling)
- Optional: torchvision (for utilities)

## Backward Compatibility
This implementation:
- Does NOT modify any existing files
- Does NOT break existing M3 functionality
- Does NOT affect the REAL environmental M1 model
- Does NOT affect M2 mock environmental data
- Does NOT affect existing risk engine, routing, or alerting
- Adds new functionality in phase6/ directory only