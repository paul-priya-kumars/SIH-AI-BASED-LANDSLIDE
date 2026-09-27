"""
Script to create a dummy Landslide4Sense dataset for testing the pipeline.
Creates fake images and masks with the correct structure.
"""

import os
import numpy as np
from pathlib import Path
import tifffile


def create_dummy_dataset(root_dir, num_train=10, num_val=5, num_test=5):
    """
    Create a dummy Landslide4Sense dataset.

    Args:
        root_dir: Root directory for the dataset
        num_train: Number of training samples
        num_val: Number of validation samples
        num_test: Number of test samples
    """
    root_path = Path(root_dir)
    root_path.mkdir(parents=True, exist_ok=True)

    # Create directory structure
    for split in ['train', 'val', 'test']:
        (root_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (root_path / split / 'masks').mkdir(parents=True, exist_ok=True)

    # Create dummy data
    splits = [('train', num_train), ('val', num_val), ('test', num_test)]

    for split_name, num_samples in splits:
        print(f"Creating {num_samples} {split_name} samples...")

        for i in range(num_samples):
            # Create a fake 14-channel image (128x128x14)
            # Using random values for demonstration
            image = np.random.rand(128, 128, 14).astype(np.float32)

            # Create a fake binary mask (128x128)
            # Randomly assign some pixels as landslide (1)
            mask = np.random.choice([0, 1], size=(128, 128), p=[0.9, 0.1]).astype(np.uint8)

            # Save as TIFF files
            image_path = root_path / split_name / 'images' / f'{i:04d}.tif'
            mask_path = root_path / split_name / 'masks' / f'{i:04d}.tif'

            tifffile.imwrite(image_path, image)
            tifffile.imwrite(mask_path, mask)

    print(f"Dummy dataset created at {root_path}")
    print(f"Structure:")
    for split in ['train', 'val', 'test']:
        img_count = len(list((root_path / split / 'images').glob('*.tif')))
        mask_count = len(list((root_path / split / 'masks').glob('*.tif')))
        print(f"  {split}: {img_count} images, {mask_count} masks")


if __name__ == "__main__":
    # Create dummy dataset in a temporary location
    dataset_path = "./datasets/landslide4sense_dummy"
    create_dummy_dataset(dataset_path, num_train=10, num_val=5, num_test=5)