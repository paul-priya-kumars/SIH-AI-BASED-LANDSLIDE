"""
JARVIS Phase 4 - Alert Tests
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_module(module_path):
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / module_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise AssertionError(
            f"{module_path} failed."
        )

    return result.stdout


def test_alert_rules():
    output = run_module(
        "phase4/alerts/alert_rules.py"
    )

    assert "Alert rules: PASSED" in output


def test_alert_engine():
    output = run_module(
        "phase4/alerts/alert_engine.py"
    )

    assert "Alert engine: PASSED" in output
    assert "Alert Level     : CRITICAL" in output


def test_notification():
    output = run_module(
        "phase4/alerts/notification.py"
    )

    assert "Notification: PASSED" in output
    assert "Type    : SAFETY_ALERT" in output


if __name__ == "__main__":
    print("\n============================================")
    print("       PHASE 4 - ALERT TESTS")
    print("============================================")

    test_alert_rules()
    print("Alert rules       : PASSED")

    test_alert_engine()
    print("Alert engine      : PASSED")

    test_notification()
    print("Notification      : PASSED")

    print("\n============================================")
    print("       ALL ALERT TESTS PASSED")
    print("============================================")