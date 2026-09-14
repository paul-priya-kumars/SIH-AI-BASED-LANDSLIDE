"""
Landslide4Sense Preprocessing Utilities

Handles loading and preprocessing of Landslide4Sense multispectral satellite data.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np


class Landslide4SensePreprocessor:
    """
    Preprocessing pipeline for Landslide4Sense dataset.

    The Landslide4Sense dataset provides:
    - 128x128 image patches
    - 14 bands (Sentinel-2 multispectral + slope + DEM)
    - Pixel-wise landslide/non-landslide labels

    This class handles:
    - Loading multispectral data
    - Validating dimensions and band count
    - Numerical conversion
    - Normalization/preprocessing
    - Label loading (where applicable)
    """

    # Expected dataset specifications
    EXPECTED_HEIGHT = 128
    EXPECTED_WIDTH = 128
    EXPECTED_BANDS = 14

    def __init__(self,
                 normalize_bands: bool = True,
                 band_means: Optional[np.ndarray] = None,
                 band_stds: Optional[np.ndarray] = None):
        """
        Initialize the Landslide4Sense preprocessor.

        Args:
            normalize_bands: Whether to normalize bands to zero mean, unit variance
            band_means: Pre-computed band means for normalization (if None, compute from data)
            band_stds: Pre-computed band stds for normalization (if None, compute from data)
        """
        self.normalize_bands = normalize_bands
        self.band_means = band_means
        self.band_stds = band_stds
        self._is_fitted = band_means is not None and band_stds is not None

    def load_sample(self, file_path: Path) -> np.ndarray:
        """
        Load a Landslide4Sense sample from file.

        Args:
            file_path: Path to the multispectral sample file

        Returns:
            numpy array of shape (height, width, bands)

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is unsupported or data is invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Landslide4Sense sample not found: {file_path}")

        # For Phase 1 infrastructure, we define the interface but don't implement
        # actual file loading since we're not downloading the dataset yet.
        # In Phase 2, this would be implemented with rasterio or similar.
        raise NotImplementedError(
            "Landslide4Sense sample loading not implemented in Phase 1. "
            "This will be implemented in Phase 2 when the dataset is available."
        )

    def validate_dimensions(self, data: np.ndarray) -> bool:
        """
        Validate that the data has the expected Landslide4Sense dimensions.

        Args:
            data: Input data array

        Returns:
            True if dimensions are valid, False otherwise
        """
        if data.ndim != 3:
            return False

        height, width, bands = data.shape
        return (height == self.EXPECTED_HEIGHT and
                width == self.EXPECTED_WIDTH and
                bands == self.EXPECTED_BANDS)

    def validate_band_count(self, data: np.ndarray) -> bool:
        """
        Validate that the data has the expected number of bands.

        Args:
            data: Input data array

        Returns:
            True if band count is valid, False otherwise
        """
        if data.ndim < 3:
            return False
        return data.shape[-1] == self.EXPECTED_BANDS

    def convert_to_float32(self, data: np.ndarray) -> np.ndarray:
        """
        Convert data to float32 for numerical stability.

        Args:
            data: Input data array

        Returns:
            Data converted to float32
        """
        return data.astype(np.float32)

    def normalize_data(self, data: np.ndarray) -> np.ndarray:
        """
        Normalize the multispectral data.

        Args:
            data: Input data array of shape (height, width, bands)

        Returns:
            Normalized data array
        """
        if not self.normalize_bands:
            return data

        if not self._is_fitted:
            # Compute statistics from data if not pre-fitted
            # Note: In practice, these should be computed on training set only
            band_means = np.mean(data, axis=(0, 1))
            band_stds = np.std(data, axis=(0, 1))
            # Avoid division by zero
            band_stds = np.where(band_stds == 0, 1, band_stds)
        else:
            band_means = self.band_means
            band_stds = self.band_stds

        # Normalize each band
        normalized = (data - band_means) / band_stds
        return normalized

    def preprocess_sample(self, file_path: Path) -> np.ndarray:
        """
        Complete preprocessing pipeline for a Landslide4Sense sample.

        Args:
            file_path: Path to the multispectral sample file

        Returns:
            Preprocessed data array ready for model input

        Note:
            This method raises NotImplementedError in Phase 1 as actual
            implementation requires the dataset.
        """
        # Load the sample
        data = self.load_sample(file_path)

        # Validate dimensions
        if not self.validate_dimensions(data):
            raise ValueError(
                f"Invalid data dimensions. Expected ({self.EXPECTED_HEIGHT}, "
                f"{self.EXPECTED_WIDTH}, {self.EXPECTED_BANDS}), got {data.shape}"
            )

        # Convert to float32
        data = self.convert_to_float32(data)

        # Normalize
        data = self.normalize_data(data)

        return data

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

    def fit_normalization(self, data_samples: np.ndarray) -> None:
        """
        Compute normalization statistics from training data.

        Args:
            data_samples: Array of shape (n_samples, height, width, bands)
        """
        if data_samples.ndim != 4:
            raise ValueError(
                f"Expected 4D array (n_samples, H, W, B), got {data_samples.shape}"
            )

        # Compute mean and std across samples, height, width dimensions
        self.band_means = np.mean(data_samples, axis=(0, 1, 2))
        self.band_stds = np.std(data_samples, axis=(0, 1, 2))
        # Avoid division by zero
        self.band_stds = np.where(self.band_stds == 0, 1, self.band_stds)
        self._is_fitted = True


def get_default_preprocessor() -> Landslide4SensePreprocessor:
    """
    Get a default Landslide4Sense preprocessor instance.

    Returns:
        Configured Landslide4SensePreprocessor ready for use
    """
    return Landslide4SensePreprocessor(normalize_bands=True)