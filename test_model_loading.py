#!/usr/bin/env python3
"""
Test the model loading logic from risk_service.py to verify it works correctly.
"""

import os
import torch
import numpy as np
from pathlib import Path

# Import the model components (same as in risk_service.py)
try:
    from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
    from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor
    LANDSLIDE4SENSE_MODEL_AVAILABLE = True
    print("[*] Successfully imported Landslide4sense model components")
except ImportError as e:
    print(f"[!] Could not import Landslide4sense model components: {e}")
    LANDSLIDE4SENSE_MODEL_AVAILABLE = False

def test_landsat_model_loading():
    """Test the Landsat model loading logic."""
    if not LANDSLIDE4SENSE_MODEL_AVAILABLE:
        print("✗ Skipping test: Landslide4sense model components not available")
        return False

    # Set up paths (same as in risk_service.py)
    model_path = os.path.join(os.path.dirname(__file__), "checkpoints", "best_model.pth")
    print(f"Testing model loading from: {model_path}")

    if not os.path.exists(model_path):
        print(f"[X] Model file not found at {model_path}")
        return False

    # Global variables for model (same as in risk_service.py)
    _landsat_model = None
    _landsat_preprocessor = None
    _landsat_model_loaded = False

    try:
        if os.path.exists(model_path):
            print("  Attempting to load checkpoint...")
            # Load checkpoint with proper handling for PyTorch 2.6+ weights_only security feature
            try:
                # First try with weights_only=True (secure default)
                print("    Trying weights_only=True...")
                checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
                print("    [*] Success with weights_only=True")
            except Exception as e:
                print(f"    [X] Failed with weights_only=True: {e}")
                # If that fails, try with weights_only=False (less secure but needed for our checkpoints)
                # Since we trust our own checkpoint files, we can use weights_only=False directly
                print("    Trying weights_only=False (trusted checkpoint)...")
                checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
                print("    [*] Success with weights_only=False")

            # Initialize model
            print("  Initializing model...")
            in_channels = checkpoint.get("config", {}).get("in_channels", 14)
            num_classes = checkpoint.get("config", {}).get("num_classes", 1)
            print(f"  Model config: in_channels={in_channels}, num_classes={num_classes}")

            _landsat_model = UNetResNet34(
                in_channels=in_channels,
                num_classes=num_classes,
                pretrained=False,
            )
            _landsat_model.load_state_dict(checkpoint["model_state_dict"])
            _landsat_model.eval()
            print("  [*] Model initialized and state dict loaded")

            # Initialize preprocessor
            print("  Initializing preprocessor...")
            preprocessor_state = checkpoint.get("preprocessor_state", {})
            _landsat_preprocessor = Landslide4SensePreprocessor(
                normalize_bands=preprocessor_state.get("normalize_bands", True),
                band_means=np.array(preprocessor_state["band_means"]) if preprocessor_state.get("band_means") is not None else None,
                band_stds=np.array(preprocessor_state["band_stds"]) if preprocessor_state.get("band_stds") is not None else None,
            )
            print("  [*] Preprocessor initialized")

            print(f"[*] Landslide4Sense model loaded successfully from {model_path}")
            _landsat_model_loaded = True

            # Test inference with a dummy input
            print("  Testing inference with dummy input...")
            dummy_input = torch.randn(1, 14, 128, 128)  # Batch size 1, 14 channels, 128x128
            with torch.no_grad():
                logits = _landsat_model(dummy_input)
                probs = torch.sigmoid(logits)

            print(f"  Input shape: {dummy_input.shape}")
            print(f"  Output logits shape: {logits.shape}")
            print(f"  Output probabilities shape: {probs.shape}")
            print(f"  Probabilities range: {probs.min().item():.6f} to {probs.max().item():.6f}")

            # Check for NaN or Inf values
            if torch.isnan(probs).any() or torch.isinf(probs).any():
                print("  [X] ERROR: Model output contains NaN or Inf values")
                return False
            else:
                print("  [*] Model output is valid (no NaN or Inf values)")

            return True
        else:
            print(f"[X] No Landslide4Sense model found at {model_path}")
            _landsat_model_loaded = True
            return False
    except Exception as e:
        print(f"[X] Error loading Landslide4Sense model: {e}")
        import traceback
        traceback.print_exc()
        _landsat_model_loaded = True
        _landsat_model = None
        _landsat_preprocessor = None
        return False

if __name__ == "__main__":
    print("Testing Landslide4Sense model loading logic...")
    print("=" * 50)

    success = test_landsat_model_loading()

    print("=" * 50)
    if success:
        print("RESULT: MODEL LOADING TEST — PASSED")
    else:
        print("RESULT: MODEL LOADING TEST — FAILED")