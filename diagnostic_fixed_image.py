#!/usr/bin/env python3
"""
Diagnostic script to check what probability the fixed image file produces.
This is read-only and does not modify any existing files.
"""

import os
import torch
import numpy as np

# Import the same components used in risk_service.py
try:
    from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
    from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor
    print("[*] Successfully imported required components")
except ImportError as e:
    print(f"[!] Failed to import components: {e}")
    exit(1)

def diagnose_fixed_image():
    """Check what the fixed image file produces."""

    # Fixed path used in the code
    fixed_image_path = r"C:\Users\jayav\OneDrive\Desktop\land 2\datasets\landslide4sense\train\images\image_1.h5"
    model_path = os.path.join(os.path.dirname(__file__), "checkpoints", "best_model.pth")

    print(f"[*] Loading model from: {model_path}")
    print(f"[*] Using fixed image: {fixed_image_path}")

    # Check if files exist
    if not os.path.exists(model_path):
        print(f"[X] Model file not found: {model_path}")
        return

    if not os.path.exists(fixed_image_path):
        print(f"[X] Image file not found: {fixed_image_path}")
        return

    try:
        # Load checkpoint (same logic as in risk_service.py)
        try:
            # First try with weights_only=True (secure default)
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=True)
            print("[*] Loaded checkpoint with weights_only=True")
        except Exception:
            # If that fails, use weights_only=False since we trust our own checkpoint files
            checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
            print("[*] Loaded checkpoint with weights_only=False")

        # Initialize model (same as in risk_service.py)
        model = UNetResNet34(
            in_channels=checkpoint.get("config", {}).get("in_channels", 14),
            num_classes=checkpoint.get("config", {}).get("num_classes", 1),
            pretrained=False,
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        print("[*] Model initialized successfully")

        # Initialize preprocessor (same as in risk_service.py)
        preprocessor_state = checkpoint.get("preprocessor_state", {})
        preprocessor = Landslide4SensePreprocessor(
            normalize_bands=preprocessor_state.get("normalize_bands", True),
            band_means=np.array(preprocessor_state["band_means"]) if preprocessor_state.get("band_means") is not None else None,
            band_stds=np.array(preprocessor_state["band_stds"]) if preprocessor_state.get("band_stds") is not None else None,
        )
        print("[*] Preprocessor initialized successfully")

        # Load and process the FIXED image (same as in risk_service.py)
        import h5py
        with h5py.File(fixed_image_path, 'r') as f:
            img_data = f['img'][:]  # shape: (128, 128, 14)

        print(f"[*] Loaded image data shape: {img_data.shape}")
        print(f"[*] Loaded image data dtype: {img_data.dtype}")
        print(f"[*] Image data min: {img_data.min()}, max: {img_data.max()}, mean: {img_data.mean()}")

        # Preprocess using our Landslide4Sense preprocessor
        img_processed = preprocessor.preprocess_sample(img_data)
        print(f"[*] Preprocessed image shape: {img_processed.shape}")
        print(f"[*] Preprocessed image min: {img_processed.min()}, max: {img_processed.max()}, mean: {img_processed.mean()}")

        # Convert to tensor and add batch dimension
        img_tensor = torch.from_numpy(img_processed).unsqueeze(0)  # (1, C, H, W)
        print(f"[*] Input tensor shape: {img_tensor.shape}")

        # Run inference
        with torch.no_grad():
            logits = model(img_tensor)
            probs = torch.sigmoid(logits)  # shape: (1, 1, 128, 128)

        print(f"[*] Output logits shape: {logits.shape}")
        print(f"[*] Output probs shape: {probs.shape}")
        print(f"[*] Output probs min: {probs.min().item():.6f}, max: {probs.max().item():.6f}, mean: {probs.mean().item():.6f}")

        # Convert to numpy and extract image-level probability (same as in risk_service.py)
        probs_np = probs.squeeze().cpu().numpy()  # shape: (H, W)
        print(f"[*] Probability numpy array shape: {probs_np.shape}")
        print(f"[*] Probability numpy min: {probs_np.min():.6f}, max: {probs_np.max():.6f}, mean: {probs_np.mean():.6f}")

        # Derive image-level probability: use maximum probability
        image_level_probability = float(np.max(probs_np))
        print(f"[*] Image-level probability (max): {image_level_probability:.6f}")

        # Show what risk level this would produce
        if image_level_probability >= 0.75:
            risk_level = "VERY_HIGH"
        elif image_level_probability >= 0.55:
            risk_level = "HIGH"
        elif image_level_probability >= 0.35:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"
        print(f"[*] Risk level for this probability: {risk_level}")

    except Exception as e:
        print(f"[X] Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("DIAGNOSTIC: Checking Fixed Image File Output")
    print("=" * 60)
    diagnose_fixed_image()
    print("=" * 60)