#!/usr/bin/env python3
"""
Test script to verify the risk service integration with Landslide4sense model.
"""

import sys
import os

# Add the backend directory and root directory to the path
backend_dir = os.path.join(os.path.dirname(__file__))
root_dir = os.path.dirname(backend_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, root_dir)

from app.services.risk_service import get_risk_prediction

def test_risk_service():
    """Test the risk service with sample coordinates."""
    print("Testing risk service with Landslide4sense model integration...")

    # Test coordinates in the Nilgiris region
    test_locations = [
        (11.41, 76.69, "Ooty center"),
        (11.35, 76.70, "Near Ooty"),
        (11.40, 76.50, "Western Nilgiris"),
        (11.50, 76.80, "Eastern Nilgiris"),
    ]

    for lat, lon, description in test_locations:
        print(f"\nTesting {description} (lat={lat}, lon={lon}):")
        try:
            prediction = get_risk_prediction(lat, lon)
            print(f"  Risk Probability: {prediction.risk_probability}")
            print(f"  Risk Level: {prediction.risk_level}")
            print(f"  Confidence: {prediction.confidence}")
            print(f"  Location Name: {prediction.location_name}")
            print(f"  Is Mock: {prediction.is_mock}")
            print(f"  Factors: {prediction.factors[:2]}...")  # Show first 2 factors

            # Verify we're getting real model predictions (not mock)
            if not prediction.is_mock:
                print("  [*] Using REAL Landslide4sense model")
            else:
                print("  [!] Using mock predictions (model may not be loaded)")

        except Exception as e:
            print(f"  [X] Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_risk_service()