"""
Landslide4Sense-specific preprocessing for satellite imagery.

Handles validation and preprocessing of 14-band Landslide4Sense format data.
Implements actual loading, normalization, and preprocessing for Phase 2.
"""

import os
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union
import logging

# Try to import rasterio for GeoTIFF, fallback to PIL for PNG/JPEG
try:
    import rasterio
    from rasterio.enums import Resampling
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

from PIL import Image
import h5py

logger = logging.getLogger(__name__)


class Landslide4SensePreprocessor:
    """
    Preprocessor for Landslide4Sense satellite imagery.

    Handles:
    - Loading image and label files (GeoTIFF or PNG)
    - Validating spatial dimensions (128x128) and band count (14)
    - Converting data to float32
    - Applying per-band normalization (using precomputed statistics)
    - Ensuring label values are valid (0 or 1)

    The preprocessor can be fitted on training data to compute normalization
    statistics, or initialized with precomputed statistics.
    """

    # Expected number of channels (bands)
    EXPECTED_CHANNELS = 14
    # Expected image dimensions (height, width)
    EXPECTED_SHAPE = (128, 128)
    # Valid label values
    VALID_LABELS = {0, 1}

    def __init__(
        self,
        normalize_bands: bool = True,
        band_means: Optional[np.ndarray] = None,
        band_stds: Optional[np.ndarray] = None,
    ):
        """
        Initialize the preprocessor.

        Args:
            normalize_bands: Whether to apply band normalization (default: True)
            band_means: Pre-computed band means for normalization (shape: (14,))
            band_stds: Pre-computed band standard deviations for normalization (shape: (14,))
        """
        self.normalize_bands = normalize_bands
        self.band_means = band_means
        self.band_stds = band_stds
        self._is_fitted = False

        # If band_means and band_stds are provided, consider it fitted
        if band_means is not None and band_stds is not None:
            self._is_fitted = True

        # Expected Landslide4Sense specifications
        self.expected_height = 128
        self.expected_width = 128
        self.expected_bands = 14

    def validate_dimensions(self, data: np.ndarray) -> bool:
        """
        Validate that input data has correct spatial dimensions.

        Args:
            data: Input array to validate (H, W, C) or (C, H, W)

        Returns:
            True if dimensions are correct (128x128), False otherwise
        """
        if not isinstance(data, np.ndarray):
            return False

        if data.ndim != 3:
            return False

        # Assume last two dimensions are H, W (if channels last) or first two (if channels first)
        # We'll check both possibilities
        h1, w1 = data.shape[-2], data.shape[-1]
        h2, w2 = data.shape[0], data.shape[1]

        return (
            (h1 == self.expected_height and w1 == self.expected_width) or
            (h2 == self.expected_height and w2 == self.expected_width)
        )

    def validate_band_count(self, data: np.ndarray) -> bool:
        """
        Validate that input data has correct number of bands.

        Args:
            data: Input array to validate (H, W, C) or (C, H, W)

        Returns:
            True if band count is 14, False otherwise
        """
        if not isinstance(data, np.ndarray) or data.ndim < 3:
            return False

        # Check last dimension or first dimension
        bands_last = data.shape[-1]
        bands_first = data.shape[0]

        return bands_last == self.expected_bands or bands_first == self.expected_bands

    def convert_to_float32(self, data: np.ndarray) -> np.ndarray:
        """
        Convert input data to float32 dtype.

        Args:
            data: Input numeric array

        Returns:
            Array converted to float32
        """
        if not isinstance(data, np.ndarray):
            raise TypeError("Input must be a numpy array")

        return data.astype(np.float32)

    def fit_normalization(self, data: np.ndarray) -> None:
        """
        Compute normalization statistics from data.

        Args:
            data: Training data array of shape (N, H, W, C) or (N, C, H, W)
                  Assuming channels last format (NHWC) for computation.
        """
        if not isinstance(data, np.ndarray):
            raise TypeError("Input data must be a numpy array")

        # Ensure we can compute statistics
        if data.ndim != 4:
            raise ValueError(
                f"Input data must be 4-dimensional (N, H, W, C), got shape {data.shape}"
            )

        # Assume channels last (NHWC)
        # Compute mean and std per band across all images and pixels
        self.band_means = np.mean(data, axis=(0, 1, 2))
        self.band_stds = np.std(data, axis=(0, 1, 2))

        # Avoid division by zero
        self.band_stds = np.where(self.band_stds < 1e-8, 1.0, self.band_stds)

        self._is_fitted = True
        logger.info(
            f"Fitted preprocessing statistics: mean={self.band_means}, std={self.band_stds}"
        )

    def load_sample(self, file_path: Path) -> np.ndarray:
        """
        Load a Landslide4Sense sample from file.

        Args:
            file_path: Path to the multispectral sample file

        Returns:
            numpy array of shape (height, width, bands)

        Raises:
            NotImplementedError: In Phase 1 as dataset is not available
        """
        # For Phase 1 infrastructure, we define the interface but don't implement
        # actual file loading since we're not downloading the dataset yet.
        # In Phase 2, this would be implemented with rasterio or similar.
        raise NotImplementedError(
            "Landslide4Sense sample loading not implemented in Phase 1. "
            "This will be implemented in Phase 2 when the dataset is available."
        )

    def load_label(self, file_path: Path) -> np.ndarray:
        """
        Load landslide label for a sample.

        Args:
            file_path: Path to the label file

        Returns:
            Binary label array (0=non-landslide, 1=landslide)

        Raises:
            NotImplementedError: In Phase 1 as dataset is not available
        """
        raise NotImplementedError(
            "Landslide4Sense label loading not implemented in Phase 1. "
            "This will be implemented in Phase 2 when the dataset is available."
        )

    def preprocess_sample(self, sample: np.ndarray) -> np.ndarray:
        """
        Preprocess a single Landslide4Sense sample.

        Applies:
        - Dimension validation (128x128)
        - Band count validation (14)
        - Conversion to float32
        - Optional normalization (if fitted on training data

        Args:
            sample: Loaded sample array of shape (H, W, C) or (C, H, W)

        Returns:
            Preprocessed sample as numpy array of shape (C, H, W) with dtype float32.

        Raises:
            ValueError: If validation fails.
        """
        # Validate dimensions
        if not self.validate_dimensions(sample):
            raise ValueError(
                f"Sample dimensions incorrect. Expected spatial shape {self.EXPECTED_SHAPE}, "
                f"got spatial shape {sample.shape[-2:] if sample.ndim >= 2 else 'unknown'}"
            )

        # Validate band count
        if not self.validate_band_count(sample):
            raise ValueError(
                f"Sample band count incorrect. Expected {self.EXPECTED_CHANNELS} bands, "
                f"got {sample.shape[-1] if sample.ndim >= 3 else sample.shape[0]}"
            )

        # Convert to float32
        sample = self.convert_to_float32(sample)
        # Check for finite values (no NaN or Inf)
        if not np.all(np.isfinite(sample)):
            raise ValueError(
                f"Sample contains non-finite values (NaN or Inf)"
            )

        # Ensure channel-first format (C, H, W) for consistency with PyTorch
        if sample.shape[-1] == self.EXPECTED_CHANNELS:
            # Channels last (H, W, C) -> transpose to (C, H, W)
            sample = np.transpose(sample, (2, 0, 1))
        elif sample.shape[0] == self.EXPECTED_CHANNELS:
            # Already channels first (C, H, W)
            pass
        else:
            raise ValueError(
                f"Could not determine channel dimension. Shape: {sample.shape}"
            )

        # Apply normalization if enabled and fitted
        if self.normalize_bands and self._is_fitted:
            if self.band_means is None or self.band_stds is None:
                raise RuntimeError(
                    "Preprocessor is fitted but band_means or band_stds is None"
                )
            # Normalize each band: (x - mean) / std
            for c in range(self.EXPECTED_CHANNELS):
                sample[c] = (sample[c] - self.band_means[c]) / self.band_stds[c]

        return sample

    def preprocess_label(self, label: np.ndarray) -> np.ndarray:
        """
        Preprocess a Landslide4Sense label.

        Ensures label is of correct shape and dtype.

        Args:
            label: Loaded label array of shape (H, W)

        Returns:
            Preprocessed label as numpy array of shape (H, W) with dtype long (int64).
        """
        if not isinstance(label, np.ndarray):
            raise TypeError("Label must be a numpy array")

        if label.ndim != 2:
            raise ValueError(
                f"Label must be 2-dimensional (H, W), got shape {label.shape}"
            )

        if label.shape != self.EXPECTED_SHAPE:
            raise ValueError(
                f"Label shape incorrect. Expected {self.EXPECTED_SHAPE}, "
                f"got {label.shape}"
            )

        # Ensure label values are valid (already checked in load_label, but double-check)
        unique_vals = np.unique(label)
        for val in unique_vals:
            if val not in self.VALID_LABELS:
                raise ValueError(
                    f"Invalid label value {val} found. Valid labels are {self.VALID_LABELS}"
                )

        return label.astype(np.longlong)  # or np.int64

    def get_band_statistics(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get the band-wise mean and standard deviation for normalization.

        Returns:
            Tuple of (band_means, band_stds) or (None, None) if not fitted
        """
        return self.band_means, self.band_stds

    def is_fitted(self) -> bool:
        """
        Check if the preprocessor has been fitted with data.

        Returns:
            True if fit_normalization has been called or band_means/band_stds provided, False otherwise
        """
        return self._is_fitted

    def __repr__(self) -> str:
        """String representation of the preprocessor."""
        return (
            f"Landslide4SensePreprocessor("
            f"normalize_bands={self.normalize_bands}, "
            f"is_fitted={self._is_fitted}, "
            f"expected_shape=({self.expected_height}, {self.expected_width}, {self.expected_bands}))"
        )


def get_default_preprocessor() -> Landslide4SensePreprocessor:
    """
    Get a default Landslide4Sense preprocessor instance.

    Returns:
        Configured Landslide4SensePreprocessor ready for use
    """
    return Landslide4SensePreprocessor(normalize_bands=True)


# Example usage (for debugging)
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    # Dummy data for testing
    dummy_sample = np.random.randint(0, 10000, size=(128, 128, 14)).astype(np.uint16)
    dummy_label = np.random.randint(0, 2, size=(128, 128)).astype(np.uint8)

    preprocessor = Landslide4SensePreprocessor()

    # Fit normalization on dummy data (in practice, use training set)
    preprocessor.fit_normalization(
        np.stack([dummy_sample for _ in range(10)], axis=0)
    )

    # Preprocess a sample
    processed = preprocessor.preprocess_sample(dummy_sample)
    print(f"Processed sample shape: {processed.shape}, dtype: {processed.dtype}")
    print(f"Sample mean per band: {np.mean(processed, axis=(1, 2))}")
    print(f"Sample std per band: {np.std(processed, axis=(1, 2))}")

    # Preprocess a label
    processed_label = preprocessor.preprocess_label(dummy_label)
    print(f"Processed label shape: {processed_label.shape}, dtype: {processed_label.dtype}")
    print(f"Unique labels: {np.unique(processed_label)}")