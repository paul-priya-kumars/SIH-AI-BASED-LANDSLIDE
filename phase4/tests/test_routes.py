"""
JARVIS Phase 4 - Route Tests

Tests the existing Phase 4 route modules by executing
their verified behavior directly.
"""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_module(module_path):
    """
    Run an existing Phase 4 module and return its output.
    """

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


def test_route_risk():

    output = run_module(
        "phase4/routing/route_risk.py"
    )

    assert "Route risk: PASSED" in output


def test_route_analyzer():

    output = run_module(
        "phase4/routing/route_analyzer.py"
    )

    assert "Route analyzer: PASSED" in output
    assert "Safest Route : Route A" in output


def test_alternative_routes():

    output = run_module(
        "phase4/routing/alternative_routes.py"
    )

    assert "Alternative route analysis: PASSED" in output
    assert "Safest Alternative : Route A" in output


def test_rerouting():

    output = run_module(
        "phase4/routing/rerouting.py"
    )

    assert "Rerouting: PASSED" in output
    assert "Recommended Route  : Route A" in output


if __name__ == "__main__":

    print("\n============================================")
    print("       PHASE 4 - ROUTE TESTS")
    print("============================================")

    test_route_risk()
    print("Route risk          : PASSED")

    test_route_analyzer()
    print("Route analyzer      : PASSED")

    test_alternative_routes()
    print("Alternative routes  : PASSED")

    test_rerouting()
    print("Rerouting           : PASSED")

    print("\n============================================")
    print("       ALL ROUTE TESTS PASSED")
    print("============================================")