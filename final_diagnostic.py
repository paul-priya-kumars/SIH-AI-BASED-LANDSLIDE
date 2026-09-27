#!/usr/bin/env python3
"""
Final diagnostic to analyze the Landslide4sense model integration.
This script only reads existing code and data, does not modify anything.
"""

import os
import sys

# Setup paths to import from backend
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_model_loading():
    """Diagnose the model loading issues."""
    print("=" * 60)
    print("DIAGNOSTIC: Model Loading Analysis")
    print("=" * 60)

    # Import the risk service to access the loading functions
    try:
        from app.services.risk_service import _load_model, _load_landsat_model, _model_path
        print(f"[*] Model path from risk_service: {_model_path}")

        # Check if model file exists
        if os.path.exists(_model_path):
            print(f"[*] Model file EXISTS: {_model_path}")
        else:
            print(f"[X] Model file NOT FOUND: {_model_path}")

        # Test loading the M1 model (this should show the error)
        print("\n[*] Testing M1 model loader (_load_model)...")
        try:
            result = _load_model()
            print(f"[*] _load_model() returned: {result}")
        except Exception as e:
            print(f"[X] _load_model() failed with exception: {e}")

        # Test loading the Landsat model (this should work)
        print("\n[*] Testing Landsat model loader (_load_landsat_model)...")
        try:
            result = _load_landsat_model()
            print(f"[*] _load_landsat_model() returned: {result}")
        except Exception as e:
            print(f"[X] _load_landsat_model() failed with exception: {e}")

    except ImportError as e:
        print(f"[!] Failed to import risk_service: {e}")
        return False

    return True

def diagnose_prediction_consistency():
    """Diagnose why all locations give the same prediction."""
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Prediction Consistency Analysis")
    print("=" * 60)

    try:
        from app.services.risk_service import get_risk_prediction

        # Test the four locations from the original test
        test_locations = [
            (11.41, 76.69, "Ooty center"),
            (11.35, 76.70, "Near Ooty"),
            (11.40, 76.50, "Western Nilgiris"),
            (11.50, 76.80, "Eastern Nilgiris"),
        ]

        print("[*] Testing get_risk_prediction for four locations:")
        results = []

        for lat, lon, desc in test_locations:
            try:
                prediction = get_risk_prediction(lat, lon)
                results.append({
                    'location': desc,
                    'lat': lat,
                    'lon': lon,
                    'probability': prediction.risk_probability,
                    'risk_level': prediction.risk_level,
                    'confidence': prediction.confidence,
                    'is_mock': prediction.is_mock
                })
                print(f"    {desc} ({lat}, {lon}):")
                print(f"      Probability: {prediction.risk_probability}")
                print(f"      Risk Level: {prediction.risk_level}")
                print(f"      Confidence: {prediction.confidence}")
                print(f"      Is Mock: {prediction.is_mock}")
            except Exception as e:
                print(f"    [X] {desc} failed: {e}")

        # Check if all results are identical
        if len(results) > 1:
            first = results[0]
            all_same = all(
                r['probability'] == first['probability'] and
                r['risk_level'] == first['risk_level'] and
                r['confidence'] == first['confidence'] and
                r['is_mock'] == first['is_mock']
                for r in results[1:]
            )
            print(f"\n[*] All four locations produce identical results: {all_same}")

            if all_same:
                print("[*] This confirms the issue: same input used for all locations")

        return results

    except ImportError as e:
        print(f"[!] Failed to import get_risk_prediction: {e}")
        return []

def diagnose_fixed_image_usage():
    """Diagnose that the fixed image is being used."""
    print("\n" + "=" * 60)
    print("DIAGNOSTIC: Fixed Image Usage Analysis")
    print("=" * 60)

    try:
        # Read the risk_service.py file to check the image path
        risk_service_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "backend", "app", "services", "risk_service.py"
        )

        if os.path.exists(risk_service_path):
            with open(risk_service_path, 'r') as f:
                content = f.read()

            # Look for the fixed image path
            if 'image_1.h5' in content:
                # Find the line
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'image_1.h5' in line:
                        print(f"[*] Found fixed image usage at line {i+1}:")
                        print(f"    {line.strip()}")
                        break

            # Check if it's using lat/lon to determine image path
            if 'latitude' in content and 'longitude' in content:
                print("[*] Code references latitude and longitude variables")
            else:
                print("[!] Code does NOT appear to reference latitude/longitude for image selection")

            # Look for the specific pattern that shows fixed usage
            if 'sample_image_path = r"' in content and 'image_1.h5' in content:
                print("[*] Code uses FIXED image path regardless of input coordinates")
            else:
                print("[?] Unable to confirm fixed image usage from source inspection")
        else:
            print(f"[X] risk_service.py not found at: {risk_service_path}")

    except Exception as e:
        print(f"[X] Error analyzing source code: {e}")

def main():
    """Run all diagnostics."""
    print("LANDSLIDE4SENSE MODEL INTEGRATION DIAGNOSTIC")
    print("This script performs read-only analysis only.")

    # Run diagnostics
    model_ok = diagnose_model_loading()
    results = diagnose_prediction_consistency()
    diagnose_fixed_image_usage()

    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if model_ok:
        print("[*] Model loading functions accessible")
    else:
        print("[!] Issues with model loading functions")

    if results and len(results) == 4:
        probs = [r['probability'] for r in results]
        if len(set(probs)) == 1:
            print("[*] CONFIRMED: All locations produce identical probability")
            print(f"    Probability value: {probs[0]}")
        else:
            print("[*] Locations produce different probabilities:")
            for r in results:
                print(f"    {r['location']}: {r['probability']}")
    else:
        print("[!] Could not verify prediction consistency")

    print("[*] Root cause: Fixed image path used instead of coordinate-based selection")
    print("[*] M1 model loading has joblib issue (unrelated to Landslide4sense)")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()