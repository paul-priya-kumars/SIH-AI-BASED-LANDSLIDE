# M1 Model Integration

To integrate the real M1 AI/ML model into the GeoShield AI system:

## Supported Model Formats
The system is designed to work with:
- Scikit-learn models (.pkl files)
- XGBoost models (.pkl or .json files)
- CatBoost models (.pkl or .cbm files)
- Any joblib-serializable model

## Expected Model Interface
The model should support:
- `predict_proba(X)` - Returns probability estimates for each class
- OR `predict(X)` - Returns class predictions (will be converted to probabilities)
- OR `decision_function(X)` - Returns confidence scores (will be converted to probabilities via sigmoid)

## Feature Order
The model expects features in this order:
1. Rainfall (mm) - 24h cumulative precipitation
2. Slope (degrees) - Terrain inclination
3. Elevation (meters) - Altitude above sea level
4. NDVI (-1 to +1) - Normalized Difference Vegetation Index

## Placement
Place your trained model file in this directory as:
- `landslide_model.pkl` (or .joblib, .cbm, .json, etc.)

Optional: You can also place a feature scaler as:
- `feature_scaler.pkl` (for StandardScaler, MinMaxScaler, etc.)

## Automatic Loading
The system will automatically:
1. Load the model when the first prediction request is made
2. Use the model for all subsequent predictions (cached in memory)
3. Fall back to mock predictions if model loading fails
4. Print status messages to the console indicating whether real or mock predictions are being used

## Verification
To verify the real model is being used:
1. Check the console output for "ML model loaded from..." message
2. Check API responses for `"is_mock": false` in the risk prediction response
3. Check the `/ml/predict` endpoint for `"model_version": "M1-REAL-v1.0"`

## Security Note
Only load models from trusted sources as joblib/pickle can execute arbitrary code during deserialization.
