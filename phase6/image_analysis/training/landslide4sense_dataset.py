"""
Landslide4Sense dataset loader for semantic segmentation.

This module provides a PyTorch Dataset class for loading the Landslide4Sense
dataset, including support for training, validation, and test splits.
"""

import os
import json
from pathlib import Path
from typing import Tuple, Optional, Callable, List
import logging

import numpy as np
import torch
from torch.utils.data import Dataset

# Try to import rasterio for GeoTIFF, fallback to PIL for PNG/JPEG
try:
    import rasterio
    from rasterio.enums import Resampling
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

from PIL import Image
import h5py
import numpy as np

logger = logging.getLogger(__name__)


class Landslide4SenseDataset(Dataset):
    """
    PyTorch Dataset for Landslide4Sense.

    Args:
        root_dir (str or Path): Root directory of the dataset.
        split (str): One of 'train', 'val', 'test'.
        transform (callable, optional): A function/transform that takes in a sample
            and returns a transformed version. Applied to both image and mask.
        target_transform (callable, optional): A function/transform that takes in the
            target and returns a transformed version.
        validate_samples (bool): If True, validate each sample's dimensions and
            channel count on loading. Increases I/O but catches corrupted data.
    """

    # Expected number of channels (bands)
    EXPECTED_CHANNELS = 14
    # Expected image dimensions (height, width)
    EXPECTED_SHAPE = (128, 128)
    # Valid label values
    VALID_LABELS = {0, 1}

    def __init__(
        self,
        root_dir: str | Path,
        split: str = "train",
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
        validate_samples: bool = True,
    ):
        self.root_dir = Path(root_dir)
        self.split = split.lower()
        self.transform = transform
        self.target_transform = target_transform
        self.validate_samples = validate_samples

        if self.split not in {"train", "val", "test"}:
            raise ValueError(
                f"Split must be one of 'train', 'val', 'test'. Got '{self.split}'"
            )

        # Define paths
        self.images_dir = self.root_dir / self.split / "images"
        self.masks_dir = self.root_dir / self.split / "masks"

        # Check if directories exist
        if not self.images_dir.is_dir():
            raise FileNotFoundError(
                f"Images directory not found: {self.images_dir}"
            )
        if not self.masks_dir.is_dir():
            # For test split, masks might not be provided (as per benchmark)
            if self.split != "test":
                raise FileNotFoundError(
                    f"Masks directory not found: {self.masks_dir}"
                )
            else:
                logger.warning(
                    f"Masks directory not found for test split: {self.masks_dir}. "
                    "Returns None for masks."
                )
                self.masks_dir = None

        # Build list of image files
        self.image_files = sorted(
            [f for f in self.images_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
        )
        if not self.image_files:
            raise FileNotFoundError(
                f"No image files found in {self.images_dir}"
            )

        # If masks exist, build list of mask files (assuming same naming)
        if self.masks_dir is not None:
            self.mask_files = sorted(
                [f for f in self.masks_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
            )
            if len(self.mask_files) != len(self.image_files):
                logger.warning(
                    f"Number of images ({len(self.image_files)}) and masks ({len(self.mask_files)}) "
                    f"do not match in split '{self.split}'."
                )
        else:
            self.mask_files = []

        logger.info(
            f"Landslide4SenseDataset initialized: {len(self.image_files)} samples "
            f"for split '{self.split}' from {self.root_dir}"
        )

    def __len__(self) -> int:
        return len(self.image_files)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Returns:
            tuple: (image, mask) where:
                - image: torch.Tensor of shape (C, H, W) with dtype float32
                - mask: torch.Tensor of shape (H, W) with dtype long (0 or 1) or None for test
        """
        img_path = self.image_files[idx]
        mask_path = self.mask_files[idx] if self.mask_files is not None and idx < len(self.mask_files) else None

        # Load image
        image = self._load_image(img_path)
        # Load mask (if available)
        mask = self._load_mask(mask_path) if mask_path is not None else None

        # Validate sample if requested
        if self.validate_samples:
            self._validate_sample(image, mask, idx)

        # Apply transforms
        if self.transform:
            image = self.transform(image)
        if self.target_transform and mask is not None:
            mask = self.target_transform(mask)

        return image, mask

    def _load_image(self, path: Path) -> torch.Tensor:
        """Load image from file and convert to tensor (C, H, W)."""
        try:
            # Handle HDF5 format (Landslide4Sense)
            if path.suffix.lower() in {".h5", ".hdf5"}:
                with h5py.File(path, 'r') as f:
                    # Assuming the dataset is named 'img' as per the dataset structure
                    if 'img' in f:
                        image = f['img'][:]  # shape: (H, W, C)
                    else:
                        # Fallback: try to find any dataset
                        keys = list(f.keys())
                        if not keys:
                            raise ValueError(f"No datasets found in HDF5 file {path}")
                        image = f[keys[0]][:]  # use first dataset
                    # Ensure we have the expected number of channels
                    if image.ndim != 3 or image.shape[2] != self.EXPECTED_CHANNELS:
                        raise ValueError(
                            f"Expected HDF5 image shape (H, W, {self.EXPECTED_CHANNELS}), got {image.shape}"
                            f" in {path}"
                        )
                    # Convert from HWC to CHW and to float32
                    image = np.transpose(image, (2, 0, 1))  # (C, H, W)
                    image = image.astype(np.float32)
            elif RASTERIO_AVAILABLE and path.suffix.lower() in {".tif", ".tiff"}:
                with rasterio.open(path) as src:
                    # Read all bands
                    image = src.read()  # shape: (C, H, W)
                    # Ensure we have the expected number of channels
                    if image.shape[0] != self.EXPECTED_CHANNELS:
                        raise ValueError(
                            f"Expected {self.EXPECTED_CHANNELS} channels, got {image.shape[0]}"
                            f" in {path}"
                        )
                    # Convert to float32
                    image = image.astype(np.float32)
            else:
                # Use PIL (supports PNG, JPEG, etc.)
                img = Image.open(path)
                # Convert to numpy array
                image = np.array(img)
                # If image is 2D (H, W), add channel dimension
                if image.ndim == 2:
                    image = np.expand_dims(image, axis=-1)  # (H, W, 1)
                # If image is 3D, check channel ordering
                elif image.ndim == 3:
                    # Assume HWC format
                    pass
                else:
                    raise ValueError(f"Unexpected image shape: {image.shape}")

                # Ensure we have the expected number of channels
                if image.shape[-1] != self.EXPECTED_CHANNELS:
                    # If not, maybe the image is in CHW format? Try to transpose.
                    # For safety, we raise an error.
                    raise ValueError(
                        f"Expected {self.EXPECTED_CHANNELS} channels, got {image.shape[-1]}"
                        f" in {path}. Image shape: {image.shape}"
                    )
                # Convert HWC to CHW
                image = np.transpose(image, (2, 0, 1))  # (C, H, W)
                image = image.astype(np.float32)

        except Exception as e:
            logger.error(f"Failed to load image {path}: {e}")
            raise

        return torch.from_numpy(image)  # (C, H, W) float32

    def _load_mask(self, path: Optional[Path]) -> Optional[torch.Tensor]:
        """Load mask from file and convert to tensor (H, W)."""
        if path is None:
            return None

        try:
            # Handle HDF5 format (Landslide4Sense)
            if path.suffix.lower() in {".h5", ".hdf5"}:
                with h5py.File(path, 'r') as f:
                    # Assuming the dataset is named 'mask' as per the dataset structure
                    if 'mask' in f:
                        mask = f['mask'][:]  # shape: (H, W)
                    else:
                        # Fallback: try to find any dataset
                        keys = list(f.keys())
                        if not keys:
                            raise ValueError(f"No datasets found in HDF5 file {path}")
                        mask = f[keys[0]][:]  # use first dataset
                    # Ensure mask is 2D
                    if mask.ndim != 2:
                        raise ValueError(
                            f"Expected HDF5 mask shape (H, W), got {mask.shape}"
                            f" in {path}"
                        )
                    # Ensure mask values are uint8 (0 or 1)
                    if mask.dtype != np.uint8:
                        # Convert to uint8 if values are 0 or 1
                        if np.all(np.isin(mask, [0, 1])):
                            mask = mask.astype(np.uint8)
                        else:
                            raise ValueError(
                                f"HDF5 mask contains unexpected values: {np.unique(mask)}"
                                f" in {path}"
                            )
            elif RASTERIO_AVAILABLE and path.suffix.lower() in {".tif", ".tiff"}:
                with rasterio.open(path) as src:
                    mask = src.read(1)  # Read first band, shape: (H, W)
            else:
                mask_img = Image.open(path)
                mask = np.array(mask_img)
                # Ensure mask is 2D
                if mask.ndim != 2:
                    # If mask has channel dimension (e.g., RGB), convert to grayscale
                    if mask.ndim == 3 and mask.shape[2] == 3:
                        mask = np.mean(mask, axis=2).astype(np.uint8)
                    else:
                        raise ValueError(
                            f"Unexpected mask shape: {mask.shape} in {path}"
                        )

        except Exception as e:
            logger.error(f"Failed to load mask {path}: {e}")
            raise

        # Convert to long tensor
        mask_tensor = torch.from_numpy(mask).long()

        # Validate label values
        unique_vals = torch.unique(mask_tensor)
        for val in unique_vals:
            if val.item() not in self.VALID_LABELS:
                raise ValueError(
                    f"Invalid label value {val.item()} found in mask {path}. "
                    f"Valid labels are {self.VALID_LABELS}"
                )

        return mask_tensor  # (H, W) long

    def _validate_sample(
        self, image: torch.Tensor, mask: Optional[torch.Tensor], idx: int
    ) -> None:
        """Validate image and mask dimensions and channel count."""
        # Check image shape
        if image.shape[0] != self.EXPECTED_CHANNELS:
            raise ValueError(
                f"Image {self.image_files[idx]} has {image.shape[0]} channels, "
                f"expected {self.EXPECTED_CHANNELS}"
            )
        if image.shape[1:] != self.EXPECTED_SHAPE:
            raise ValueError(
                f"Image {self.image_files[idx]} has shape {image.shape[1:]}, "
                f"expected {self.EXPECTED_SHAPE}"
            )

        # Check mask shape if present
        if mask is not None:
            if mask.shape != self.EXPECTED_SHAPE:
                raise ValueError(
                    f"Mask {self.mask_files[idx] if self.mask_files else 'unknown'} "
                    f"has shape {mask.shape}, expected {self.EXPECTED_SHAPE}"
                )

    def get_image_path(self, idx: int) -> Path:
        """Return the file path of the image at index."""
        return self.image_files[idx]

    def get_mask_path(self, idx: int) -> Optional[Path]:
        """Return the file path of the mask at index (or None)."""
        if self.mask_files is not None and idx < len(self.mask_files):
            return self.mask_files[idx]
        return None


# Example usage (for debugging)
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    # Example: replace with actual dataset path
    dataset_path = "./datasets/landslide4sense"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        print("Please download the Landslide4sense dataset and place it there.")
        sys.exit(1)

    try:
        train_dataset = Landslide4SenseDataset(dataset_path, split="train")
        print(f"Training dataset size: {len(train_dataset)}")
        image, mask = train_dataset[0]
        print(f"Image shape: {image.shape}, dtype: {image.dtype}")
        print(f"Mask shape: {mask.shape if mask is not None else None}, dtype: {mask.dtype if mask is not None else None}")
    except Exception as e:
        print(f"Error initializing dataset: {e}")
        sys.exit(1)