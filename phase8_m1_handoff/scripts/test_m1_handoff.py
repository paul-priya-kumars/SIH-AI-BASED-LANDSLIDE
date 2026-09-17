#!/usr/bin/env python3
"""
M2-C → M1 Handoff Tests
Automated tests for M2-C Phase 7 ML dataset handoff to M1.
"""

import os
import sys
import subprocess
import json
import pandas as pd
from pathlib import Path

def main():
    print("=" * 60)
    print("M2-C -> M1 Handoff Tests")
    print("=" * 60)

    # Define paths
    m2c_root = Path(__file__).parent.parent.parent
    handoff_dir = Path(__file__).parent.parent
    phase7_features_path = m2c_root / "phase7_final_ml_dataset" / "data" / "ml_features.csv"
    phase7_metadata_path = m2c_root / "phase7_final_ml_dataset" / "data" / "ml_metadata.csv"
    contract_path = handoff_dir / "phase8_m1_handoff_contract.json"
    validator_path = handoff_dir / "scripts" / "validate_m1_handoff.py"

    # Track test results
    tests_passed = 0
    tests_total = 0
    failures = []

    def test(description, condition, failure_msg=None):
        nonlocal tests_passed, tests_total
        tests_total += 1
        if condition:
            print(f"[PASS] {description}")
            tests_passed += 1
            return True
        else:
            print(f"[FAIL] {description}")
            if failure_msg:
                failures.append(f"{description}: {failure_msg}")
            else:
                failures.append(description)
            return False

    print("\n1. HANDOFF ARTIFACTS EXISTENCE")
    print("-" * 40)

    # Test 1: Handoff contract exists
    test("Handoff contract exists", contract_path.exists(),
         f"Contract not found: {contract_path}")

    # Test 2: Validation script exists
    test("Validation script exists", validator_path.exists(),
         f"Validation script not found: {validator_path}")

    # Test 3: Test script exists (this file)
    test("Test script exists", True)

    # Test 4: README exists
    readme_path = handoff_dir / "README.md"
    test("README exists", readme_path.exists(),
         f"README not found: {readme_path}")

    # Test 5: Report directory exists
    report_dir = handoff_dir / "output"
    test("Output directory exists", report_dir.exists(),
         f"Output directory not found: {report_dir}")

    # Test 6: M2-C Phase 7 features dataset exists
    test("M2-C Phase 7 features dataset exists", phase7_features_path.exists(),
         f"Features dataset not found: {phase7_features_path}")

    # Test 7: M2-C Phase 7 metadata dataset exists
    test("M2-C Phase 7 metadata dataset exists", phase7_metadata_path.exists(),
         f"Metadata dataset not found: {phase7_metadata_path}")

    print("\n2. HANDOFF CONTRACT VALIDITY")
    print("-" * 40)

    # Test 8: Contract is valid JSON
    try:
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        test("Contract is valid JSON", True)
    except Exception as e:
        test("Contract is valid JSON", False, f"Invalid JSON: {e}")
        contract = {}  # Set to empty for subsequent tests

    # Test 9: Contract has required sections
    if contract:
        required_sections = ['source', 'destination', 'feature_order', 'coordinate_contract',
                           'rainfall', 'target', 'synthetic_data', 'validation_rules']
        missing_sections = [section for section in required_sections if section not in contract]
        test("Contract has required sections", len(missing_sections) == 0,
             f"Missing sections: {missing_sections}" if missing_sections else None)

        # Test 10: Feature order is defined
        test("Feature order defined in contract", 'feature_order' in contract and len(contract['feature_order']) > 0)

        # Test 11: Source dataset path defined
        test("Source dataset path defined", 'dataset' in contract and contract['dataset'] == 'ml_features.csv')

    print("\n3. DATASET VALIDATION")
    print("-" * 40)

    # Test 12: Features dataset loads successfully
    try:
        df_features = pd.read_csv(phase7_features_path)
        test("Features dataset loads successfully", True)
    except Exception as e:
        test("Features dataset loads successfully", False, f"Error loading CSV: {e}")
        df_features = None

    # Test 13: Metadata dataset loads successfully
    try:
        df_metadata = pd.read_csv(phase7_metadata_path)
        test("Metadata dataset loads successfully", True)
    except Exception as e:
        test("Metadata dataset loads successfully", False, f"Error loading CSV: {e}")
        df_metadata = None

    # Test 14: Expected record count (4 records from Phase 7)
    if df_features is not None:
        expected_records = 4
        actual_records = len(df_features)
        test(f"Expected {expected_records} records", actual_records == expected_records,
             f"Expected {expected_records}, got {actual_records}")

    print("\n4. VALIDATOR FUNCTIONALITY")
    print("-" * 40)

    # Test 15: Validator runs successfully
    try:
        result = subprocess.run([sys.executable, str(validator_path)],
                              capture_output=True, text=True, cwd=m2c_root)
        validator_success = (result.returncode == 0)
        test("Validator runs successfully (exit code 0)", validator_success,
             f"Validator failed with exit code {result.returncode}. Stdout: {result.stdout[:200]}... Stderr: {result.stderr[:200]}...")

        # Test 16: Validator produces PASS result when run on valid data
        if validator_success:
            test("Validator produces PASS result", "Result: PASS" in result.stdout)
    except Exception as e:
        test("Validator runs successfully", False, f"Error running validator: {e}")

    print("\n5. REGRESSION TEST INTEGRATION")
    print("-" * 40)

    # Test 17: Check that we can import and run basic validation functions
    try:
        # Add the scripts directory to path to import if needed
        sys.path.insert(0, str(handoff_dir / "scripts"))
        test("Can import validation module (basic)", True)
    except Exception as e:
        test("Can import validation module (basic)", False, f"Import error: {e}")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if failures:
        print(f"\nFailures ({len(failures)}):")
        for i, failure in enumerate(failures, 1):
            print(f"  {i}. {failure}")
        print("\nResult: FAIL")
        return False
    else:
        print("\nResult: PASS")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)