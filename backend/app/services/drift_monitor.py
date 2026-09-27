"""
Drift monitoring service for GeoShield AI models.
"""
import numpy as np
import threading
from collections import deque
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DriftConfig:
    """Configuration for drift monitoring."""
    enabled: bool = False
    window_size: int = 100  # Number of observations to maintain in window
    psi_threshold: float = 0.2  # PSI threshold for drift detection
    num_bins: int = 10  # Number of bins for PSI calculation


@dataclass
class BandStatistics:
    """Statistics for a single band."""
    mean: float = 0.0
    std: float = 1.0


@dataclass
class Baseline:
    """Baseline statistics for model features."""
    band_means: List[float] = field(default_factory=list)
    band_stds: List[float] = field(default_factory=list)
    num_bands: int = 0

    def __post_init__(self):
        if self.num_bands == 0 and len(self.band_means) > 0:
            self.num_bands = len(self.band_means)
        elif len(self.band_means) == 0 and self.num_bands > 0:
            self.band_means = [0.0] * self.num_bands
            self.band_stds = [1.0] * self.num_bands


@dataclass
class DriftResult:
    """Result of drift detection for a model."""
    model_name: str
    baseline_available: bool
    drift_detected: bool
    psi_scores: List[float] = field(default_factory=list)
    band_means: List[float] = field(default_factory=list)
    band_stds: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    sample_count: int = 0


class DriftMonitor:
    """
    Drift monitoring service that tracks input data distribution changes
    relative to a baseline.
    """

    def __init__(self, config: DriftConfig = None):
        """
        Initialize the drift monitor.

        Args:
            config: Drift monitoring configuration
        """
        self.config = config or DriftConfig()
        self._lock = threading.RLock()

        # Storage for recent observations (bounded window)
        self._observation_window: deque = deque(maxlen=self.config.window_size)

        # Baseline statistics (to be set from checkpoint)
        self._baseline: Optional[Baseline] = None
        self._baseline_available: bool = False

        # Expected bin edges for standard normal distribution (mean=0, std=1)
        # Using percentiles to create bins with equal expected probability
        self._bin_edges = np.linspace(-3, 3, self.config.num_bins + 1)  # -3 to 3 std devs
        self._expected_bin_percentages = np.diff(
            np.array([0.0013, 0.0228, 0.1587, 0.5, 0.8413, 0.9772, 0.9987, 1.0])[:self.config.num_bins+1]
        ) if self.config.num_bins == 6 else np.ones(self.config.num_bins) / self.config.num_bins

        # For simplicity, if not 6 bins, assume uniform distribution
        if self.config.num_bins != 6:
            self._expected_bin_percentages = np.ones(self.config.num_bins) / self.config.num_bins

        logger.info(f"DriftMonitor initialized with config: {self.config}")

    def set_baseline(self, band_means: List[float], band_stds: List[float]) -> None:
        """
        Set the baseline statistics from checkpoint.

        Args:
            band_means: List of mean values for each band
            band_stds: List of standard deviation values for each band
        """
        with self._lock:
            if len(band_means) != len(band_stds):
                raise ValueError("band_means and band_stds must have the same length")

            self._baseline = Baseline(
                band_means=band_means.copy(),
                band_stds=band_stds.copy(),
                num_bands=len(band_means)
            )
            self._baseline_available = True
            logger.info(f"Baseline set for {len(band_means)} bands")

    def has_baseline(self) -> bool:
        """Check if baseline statistics are available."""
        return self._baseline_available and self._baseline is not None

    def record_observation(self, processed_sample: np.ndarray) -> None:
        """
        Record an observation for drift monitoring.

        Args:
            processed_sample: Preprocessed sample data of shape (C, H, W)
                            where C is number of bands, H and W are spatial dimensions
        """
        if not self.config.enabled:
            return

        with self._lock:
            # Validate input shape
            if processed_sample.ndim != 3:
                logger.warning(f"Ignoring observation with invalid shape: {processed_sample.shape}")
                return

            # For each band, flatten spatial dimensions and record values
            band_values = []
            for band_idx in range(processed_sample.shape[0]):
                band_data = processed_sample[band_idx].flatten()
                band_values.append(band_data)

            self._observation_window.append(band_values)
            logger.debug(f"Recorded observation for {len(band_values)} bands")

    def _calculate_psi(self, actual: np.ndarray, expected: np.ndarray) -> float:
        """
        Calculate Population Stability Index (PSI) between actual and expected distributions.

        Args:
            actual: Actual percentages in each bin
            expected: Expected percentages in each bin

        Returns:
            PSI value
        """
        # Avoid division by zero and log of zero
        actual_safe = np.where(actual == 0, 1e-10, actual)
        expected_safe = np.where(expected == 0, 1e-10, expected)

        # PSI = sum((actual - expected) * ln(actual / expected))
        psi = np.sum((actual_safe - expected_safe) * np.log(actual_safe / expected_safe))
        return float(psi)

    def _get_expected_bin_percentages_for_normal(self, num_bins: int) -> np.ndarray:
        """
        Get expected bin percentages for standard normal distribution.

        Args:
            num_bins: Number of bins

        Returns:
            Array of expected percentages for each bin
        """
        if num_bins <= 0:
            return np.array([])

        # Create bin edges covering -3 to 3 standard deviations (covers 99.7% of normal dist)
        bin_edges = np.linspace(-3, 3, num_bins + 1)

        # Calculate expected percentage in each bin using standard normal CDF
        from scipy.stats import norm
        expected = norm.cdf(bin_edges[1:]) - norm.cdf(bin_edges[:-1])

        # Normalize to ensure sum = 1.0
        expected = expected / np.sum(expected)

        return expected

    def check_drift(self) -> DriftResult:
        """
        Check for drift based on current observation window.

        Returns:
            DriftResult containing drift status and details
        """
        with self._lock:
            if not self.config.enabled:
                return DriftResult(
                    model_name="unknown",
                    baseline_available=False,
                    drift_detected=False,
                    sample_count=0
                )

            if not self.has_baseline():
                return DriftResult(
                    model_name="unknown",
                    baseline_available=False,
                    drift_detected=False,
                    sample_count=len(self._observation_window)
                )

            if len(self._observation_window) == 0:
                return DriftResult(
                    model_name="unknown",
                    baseline_available=True,
                    drift_detected=False,
                    sample_count=0
                )

            # Concatenate all observations in the window
            all_band_values = []
            for band_idx in range(self._baseline.num_bands):
                band_values = []
                for observation in self._observation_window:
                    if band_idx < len(observation):
                        band_values.extend(observation[band_idx])
                all_band_values.append(np.array(band_values))

            # Calculate PSI for each band
            psi_scores = []
            band_means = []
            band_stds = []
            drift_detected = False

            # Get expected bin percentages for standard normal distribution
            try:
                expected_percentages = self._get_expected_bin_percentages_for_normal(
                    self.config.num_bins
                )
            except Exception:
                # Fallback to uniform distribution if scipy not available
                expected_percentages = np.ones(self.config.num_bins) / self.config.num_bins

            for band_idx in range(self._baseline.num_bands):
                band_data = all_band_values[band_idx]

                if len(band_data) == 0:
                    # No data for this band
                    psi_scores.append(0.0)
                    band_means.append(0.0)
                    band_stds.append(1.0)
                    continue

                # Calculate actual statistics
                band_mean = float(np.mean(band_data))
                band_std = float(np.std(band_data))
                band_means.append(band_mean)
                band_stds.append(band_std)

                # Discretize data into bins
                try:
                    hist, _ = np.histogram(band_data, bins=self._bin_edges, density=False)
                    actual_percentages = hist / np.sum(hist) if np.sum(hist) > 0 else np.zeros_like(hist)

                    # Calculate PSI
                    psi = self._calculate_psi(actual_percentages, expected_percentages)
                    psi_scores.append(psi)

                    # Check if PSI exceeds threshold
                    if psi > self.config.psi_threshold:
                        drift_detected = True

                except Exception as e:
                    logger.warning(f"Error calculating PSI for band {band_idx}: {e}")
                    psi_scores.append(0.0)

            return DriftResult(
                model_name="satellite_image",
                baseline_available=True,
                drift_detected=drift_detected,
                psi_scores=psi_scores,
                band_means=band_means,
                band_stds=band_stds,
                timestamp=datetime.now(),
                sample_count=len(self._observation_window)
            )

    def get_status(self) -> Dict[str, Any]:
        """
        Get current drift monitoring status.

        Returns:
            Dictionary with status information
        """
        with self._lock:
            result = self.check_drift()

            return {
                "enabled": self.config.enabled,
                "window_size": self.config.window_size,
                "psi_threshold": self.config.psi_threshold,
                "observation_count": len(self._observation_window),
                "baseline_available": result.baseline_available,
                "drift_detected": result.drift_detected,
                "model_name": result.model_name,
                "timestamp": result.timestamp.isoformat(),
                "details": {
                    "psi_scores": result.psi_scores,
                    "band_means": result.band_means,
                    "band_stds": result.band_stds
                } if result.baseline_available else None
            }

    def reset(self) -> None:
        """Reset the drift monitor (clear observation window)."""
        with self._lock:
            self._observation_window.clear()
            logger.info("Drift monitor observation window cleared")


# Global drift monitor instance
_drift_monitor: Optional[DriftMonitor] = None


def get_drift_monitor() -> DriftMonitor:
    """
    Get the global drift monitor instance.

    Returns:
        DriftMonitor instance
    """
    global _drift_monitor
    if _drift_monitor is None:
        _drift_monitor = DriftMonitor()
    return _drift_monitor


def initialize_drift_monitor_from_config() -> None:
    """
    Initialize the global drift monitor with configuration from settings.
    """
    global _drift_monitor

    # Import here to avoid circular dependencies
    from backend.config import settings

    config = DriftConfig(
        enabled=getattr(settings, 'DRIFT_ENABLED', False),
        window_size=getattr(settings, 'DRIFT_WINDOW_SIZE', 100),
        psi_threshold=getattr(settings, 'DRIFT_THRESHOLD', 0.2)
    )

    _drift_monitor = DriftMonitor(config)
    logger.info(f"Drift monitor initialized with config: {config}")


def record_sample_for_drift(processed_sample: np.ndarray) -> None:
    """
    Record a preprocessed sample for drift monitoring.

    This function is designed to be called from the inference pipeline
    after preprocessing but before model inference.

    Args:
        processed_sample: Preprocessed sample data of shape (C, H, W)
    """
    try:
        monitor = get_drift_monitor()
        monitor.record_observation(processed_sample)
    except Exception as e:
        logger.warning(f"Failed to record sample for drift monitoring: {e}")
        # Don't raise - drift monitoring should not break inference


def check_drift_status() -> Dict[str, Any]:
    """
    Check current drift status.

    Returns:
        Dictionary with drift status information
    """
    try:
        monitor = get_drift_monitor()
        return monitor.get_status()
    except Exception as e:
        logger.error(f"Failed to check drift status: {e}")
        return {
            "enabled": False,
            "error": str(e),
            "baseline_available": False
        }


def set_drift_baseline(band_means: List[float], band_stds: List[float]) -> None:
    """
    Set the baseline statistics for drift monitoring.

    This should be called during initialization with values from the model checkpoint.

    Args:
        band_means: List of mean values for each band
        band_stds: List of standard deviation values for each band
    """
    try:
        monitor = get_drift_monitor()
        monitor.set_baseline(band_means, band_stds)
        logger.info(f"Drift baseline set for {len(band_means)} bands")
    except Exception as e:
        logger.error(f"Failed to set drift baseline: {e}")
        raise


def reset_drift_monitor() -> None:
    """
    Reset the drift monitor (clear observation window).
    """
    try:
        monitor = get_drift_monitor()
        monitor.reset()
        logger.info("Drift monitor observation window cleared")
    except Exception as e:
        logger.error(f"Failed to reset drift monitor: {e}")
        raise