#!/usr/bin/env python3
"""
Verify that the exported model can be loaded and used with the dataset loader.
"""

import torch
import numpy as np
from phase6.image_analysis.training.landslide4sense_dataset import Landslide4SenseDataset
from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor

def verify_model_loader():
    print("Verifying model loader compatibility...")

    # Load the best model
    checkpoint_path = "./checkpoints/best_model.pth"
    checkpoint = torch.load(checkpoint_path, map_location='cpu')

    # Initialize model
    model = UNetResNet34(
        in_channels=checkpoint.get("config", {}).get("in_channels", 14),
        num_classes=checkpoint.get("config", {}).get("num_classes", 1),
        pretrained=False,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Reconstruct preprocessor
    preprocessor_state = checkpoint.get("preprocessor_state", {})
    preprocessor = Landslide4SensePreprocessor(
        normalize_bands=preprocessor_state.get("normalize_bands", True),
        band_means=np.array(preprocessor_state["band_means"]) if preprocessor_state.get("band_means") is not None else None,
        band_stds=np.array(preprocessor_state["band_stds"]) if preprocessor_state.get("band_stds") is not None else None,
    )

    print(f"Model loaded successfully from epoch {checkpoint.get('epoch', 'unknown')}")
    print(f"Best validation Dice from checkpoint: {checkpoint.get('best_val_dice', 'unknown')}")

    # Test with a sample from the validation dataset
    dataset_path = r"C:\Users\jayav\OneDrive\Desktop\land 2\datasets\landslide4sense"
    dataset = Landslide4SenseDataset(
        root_dir=dataset_path,
        split="val",
        transform=None,
    )

    print(f"Validation dataset size: {len(dataset)}")

    # Get a sample
    image, mask = dataset[0]
    print(f"Sample image shape: {image.shape}, dtype: {image.dtype}")
    print(f"Sample mask shape: {mask.shape if mask is not None else None}, dtype: {mask.dtype if mask is not None else None}")

    # Preprocess
    image_np = image.numpy()
    mask_np = mask.numpy() if mask is not None else None

    try:
        image_processed = preprocessor.preprocess_sample(image_np)
        if mask_np is not None:
            mask_processed = preprocessor.preprocess_label(mask_np)
        else:
            mask_processed = None
        print("Preprocessing successful")
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        return False

    # Convert to tensor and add batch dimension
    image_tensor = torch.from_numpy(image_processed).unsqueeze(0)  # (1, C, H, W)

    # Run inference
    with torch.no_grad():
        logits = model(image_tensor)
        probs = torch.sigmoid(logits)

    print(f"Model output logits shape: {logits.shape}")
    print(f"Model output probs shape: {probs.shape}")
    print(f"Probs range: {probs.min().item():.4f} to {probs.max().item():.4f}")

    # Check if output is valid
    if torch.isnan(probs).any() or torch.isinf(probs).any():
        print("ERROR: Model output contains NaN or Inf values")
        return False

    print("✓ Model loader compatibility verification PASSED")
    return True

if __name__ == "__main__":
    success = verify_model_loader()
    if success:
        print("\n✓ Loader compatibility verified successfully")
    else:
        print("\n✗ Loader compatibility verification FAILED")