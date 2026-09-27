#!/usr/bin/env python3
"""
Simple diagnostic that works within the existing environment.
"""

import os
import sys

# Add paths to make imports work
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("Simple diagnostic: Checking if we can import required modules")

    # Try the imports that worked in test_risk_service.py
    try:
        from app.services.risk_service import get_risk_prediction
        print("[*] Successfully imported get_risk_prediction")
    except Exception as e:
        print(f"[!] Failed to import get_risk_prediction: {e}")
        return

    # Try importing the model components directly
    try:
        from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
        from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor
        print("[*] Successfully imported model components")
    except Exception as e:
        print(f"[!] Failed to import model components: {e}")
        return

    # Check if the fixed image file exists
    fixed_image_path = r"C:\Users\jayav\OneDrive\Desktop\land 2\datasets\landslide4sense\train\images\image_1.h5"
    if os.path.exists(fixed_image_path):
        print(f"[*] Fixed image file exists: {fixed_image_path}")
    else:
        print(f"[X] Fixed image file not found: {fixed_image_path}")

    # Check if model file exists
    model_path = os.path.join(os.path.dirname(__file__), "checkpoints", "best_model.pth")
    if os.path.exists(model_path):
        print(f"[*] Model file exists: {model_path}")
    else:
        print(f"[X] Model file not found: {model_path}")

if __name__ == "__main__":
    main()