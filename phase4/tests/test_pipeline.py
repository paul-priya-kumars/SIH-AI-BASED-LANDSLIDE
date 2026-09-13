"""
JARVIS Phase 4 - Final Pipeline Test
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


def test_full_pipeline():
    output = run_module(
        "phase4/integration/phase4_pipeline.py"
    )

    assert "PHASE 4 FULL PIPELINE PASSED" in output
    assert "Overall Risk : HIGH" in output
    assert "Safest Route  : Route A" in output
    assert "Required    : True" in output
    assert "Recommended : Route A" in output
    assert "Alert Required : True" in output
    assert "Alert Level    : CRITICAL" in output


def test_api():
    output = run_module(
        "phase4/api/endpoints.py"
    )

    assert "API endpoints: PASSED" in output
    assert "Overall Risk : HIGH" in output
    assert "Safest Route : Route A" in output
    assert "Rerouting    : True" in output
    assert "Alert Level  : CRITICAL" in output


if __name__ == "__main__":
    print("\n============================================")
    print("       PHASE 4 - FINAL PIPELINE TEST")
    print("============================================")

    test_full_pipeline()
    print("Full integration pipeline : PASSED")

    test_api()
    print("API integration           : PASSED")

    print("\n============================================")
    print("       PHASE 4 FINAL TESTS PASSED")
    print("============================================")