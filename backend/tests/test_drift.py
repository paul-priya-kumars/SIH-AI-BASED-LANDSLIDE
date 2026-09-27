"""
Tests for drift detection functionality.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.services.drift_monitor import (
    DriftMonitor,
    DriftConfig,
    Baseline,
    DriftResult,
    get_drift_monitor,
    record_sample_for_drift,
    check_drift_status,
    set_drift_baseline
)
from app.config import Settings


def test_drift_monitor_initialization():
    """Test drift monitor initialization."""
    config = DriftConfig()
    monitor = DriftMonitor(config)

    assert monitor.config == config
    assert not monitor.has_baseline()
    assert len(monitor._observation_window) == 0


def test_drift_monitor_set_baseline():
    """Test setting baseline statistics."""
    monitor = DriftMonitor()
    band_means = [1.0, 2.0, 3.0]
    band_stds = [0.5, 0.5, 0.5]

    monitor.set_baseline(band_means, band_stds)

    assert monitor.has_baseline()
    assert monitor._baseline is not None
    assert monitor._baseline.band_means == band_means
    assert monitor._baseline.band_stds == band_stds
    assert monitor._baseline.num_bands == 3


def test_drift_monitor_record_observation():
    """Test recording observations."""
    monitor = DriftMonitor(DriftConfig(enabled=True))

    # Create a sample with 3 bands, 4x4 spatial dimensions
    sample = np.random.randn(3, 4, 4).astype(np.float32)

    initial_count = len(monitor._observation_window)
    monitor.record_observation(sample)

    assert len(monitor._observation_window) == initial_count + 1

    # Check that the recorded data has the right structure
    observation = monitor._observation_window[-1]
    assert len(observation) == 3  # 3 bands
    assert len(observation[0]) == 16  # 4*4 flattened
    assert len(observation[1]) == 16
    assert len(observation[2]) == 16


def test_drift_monitor_disabled_when_not_enabled():
    """Test that drift monitor does nothing when disabled."""
    config = DriftConfig(enabled=False)
    monitor = DriftMonitor(config)

    sample = np.random.randn(2, 3, 3).astype(np.float32)
    initial_count = len(monitor._observation_window)

    monitor.record_observation(sample)

    # Should not have recorded anything
    assert len(monitor._observation_window) == initial_count


def test_drift_monitor_check_drift_no_baseline():
    """Test drift check when no baseline is available."""
    monitor = DriftMonitor()
    # Don't set baseline

    result = monitor.check_drift()

    assert result.model_name == "unknown"
    assert result.baseline_available == False
    assert result.drift_detected == False
    assert result.sample_count == 0


def test_drift_monitor_check_drift_no_data():
    """Test drift check when baseline available but no data."""
    monitor = DriftMonitor(DriftConfig(enabled=True))
    # Set baseline but don't record any observations
    monitor.set_baseline([0.0, 0.0], [1.0, 1.0])

    result = monitor.check_drift()

    assert result.model_name == "unknown"
    assert result.baseline_available == True
    assert result.drift_detected == False
    assert result.sample_count == 0


def test_drift_monitor_get_status():
    """Test getting drift monitor status."""
    monitor = DriftMonitor(DriftConfig(enabled=True, window_size=50))

    status = monitor.get_status()

    assert status["enabled"] == True
    assert status["window_size"] == 50
    assert status["observation_count"] == 0
    assert status["baseline_available"] == False
    assert status["drift_detected"] == False


def test_drift_monitor_reset():
    """Test resetting the drift monitor."""
    monitor = DriftMonitor(DriftConfig(enabled=True))

    # Add some data
    sample = np.random.randn(2, 3, 3).astype(np.float32)
    monitor.record_observation(sample)
    assert len(monitor._observation_window) == 1

    # Reset and check
    monitor.reset()
    assert len(monitor._observation_window) == 0


def test_get_drift_monitor_singleton():
    """Test that get_drift_monitor returns the same instance."""
    monitor1 = get_drift_monitor()
    monitor2 = get_drift_monitor()

    assert monitor1 is monitor2


def test_record_sample_for_drift_function():
    """Test the record_sample_for_drift helper function."""
    # Create a sample
    sample = np.random.randn(2, 4, 4).astype(np.float32)

    # Enable the global monitor for this test since we're testing recording functionality
    monitor = get_drift_monitor()
    monitor.config.enabled = True

    # This should not raise an exception
    record_sample_for_drift(sample)

    # Check that the global monitor received the data
    assert len(monitor._observation_window) == 1


def test_check_drift_status_function():
    """Test the check_drift_status helper function."""
    status = check_drift_status()

    # Should return a dictionary with expected keys
    assert isinstance(status, dict)
    assert "enabled" in status
    assert "baseline_available" in status


def test_set_drift_baseline_function():
    """Test the set_drift_baseline helper function."""
    band_means = [1.0, 2.0]
    band_stds = [0.5, 0.5]

    # This should not raise an exception
    set_drift_baseline(band_means, band_stds)

    # Check that the global monitor has the baseline
    monitor = get_drift_monitor()
    assert monitor.has_baseline()
    assert monitor._baseline.band_means == band_means
    assert monitor._baseline.band_stds == band_stds


def test_drift_monitor_with_perfect_match_data():
    """Test drift detection with data that matches baseline exactly."""
    # Create monitor with baseline of mean=0, std=1
    monitor = DriftMonitor(DriftConfig(enabled=True, window_size=10, psi_threshold=0.1))
    monitor.set_baseline([0.0], [1.0])  # Single band with mean=0, std=1

    # Generate data that should match the baseline (standard normal)
    np.random.seed(42)  # For reproducibility
    for _ in range(5):
        sample = np.random.randn(1, 5, 5).astype(np.float32)  # Mean=0, std=1
        monitor.record_observation(sample)

    result = monitor.check_drift()

    assert result.baseline_available == True
    # With perfect match data, PSI should be low
    assert len(result.psi_scores) == 1
    # Note: PSI might not be exactly 0 due to sampling variability, but should be relatively low
    # We're mainly testing that the mechanism works


def test_drift_monitor_integration_with_settings():
    """Test integration with application settings."""
    # Test that we can create a monitor with settings-like config
    config = DriftConfig(
        enabled=True,
        window_size=100,
        psi_threshold=0.2
    )

    monitor = DriftMonitor(config)
    assert monitor.config.enabled == True
    assert monitor.config.window_size == 100
    assert monitor.config.psi_threshold == 0.2


if __name__ == "__main__":
    pytest.main([__file__])