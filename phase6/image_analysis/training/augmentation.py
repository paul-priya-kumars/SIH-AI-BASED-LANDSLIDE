"""
Data augmentation for Landslide4Sense segmentation.

Provides augmentation functions that are spatially aligned for image and mask pairs.
All augmentations preserve the spatial correspondence between image pixels and mask pixels.
"""

import numpy as np
from typing import Tuple, Optional
import random


def horizontal_flip(image: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply horizontal flip to image and mask.

    Args:
        image: Image array of shape (C, H, W) or (H, W, C)
        mask: Mask array of shape (H, W)

    Returns:
        Tuple of (flipped_image, flipped_mask)
    """
    # Flip along width axis (axis -1 for CHW, axis -1 for HWC if channel last)
    # We'll assume CHW format for consistency with PyTorch
    if image.ndim == 3:
        # Assume CHW
        flipped_image = np.flip(image, axis=-1)
        flipped_mask = np.flip(mask, axis=-1)
    elif image.ndim == 2:
        # Grayscale image (H, W)
        flipped_image = np.flip(image, axis=-1)
        flipped_mask = np.flip(mask, axis=-1)
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")

    return flipped_image, flipped_mask


def vertical_flip(image: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply vertical flip to image and mask.

    Args:
        image: Image array of shape (C, H, W) or (H, W, C)
        mask: Mask array of shape (H, W)

    Returns:
        Tuple of (flipped_image, flipped_mask)
    """
    # Flip along height axis (axis -2 for CHW, axis -2 for HWC)
    if image.ndim == 3:
        flipped_image = np.flip(image, axis=-2)
        flipped_mask = np.flip(mask, axis=-2)
    elif image.ndim == 2:
        flipped_image = np.flip(image, axis=-2)
        flipped_mask = np.flip(mask, axis=-2)
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")

    return flipped_image, flipped_mask


def rotate_90(image: np.ndarray, mask: np.ndarray, k: int = 1) -> Tuple[np.ndarray, np.ndarray]:
    """
    Rotate image and mask by 90 degrees clockwise (k times).

    Args:
        image: Image array of shape (C, H, W) or (H, W, C)
        mask: Mask array of shape (H, W)
        k: Number of times to rotate by 90 degrees (1, 2, or 3)

    Returns:
        Tuple of (rotated_image, rotated_mask)
    """
    if k < 0 or k > 3:
        raise ValueError("k must be 0, 1, 2, or 3")

    if k == 0:
        return image, mask

    # Determine rotation axes based on image format
    # Assume CHW: axes (1, 2) for H, W
    if image.ndim == 3:
        rotated_image = np.rot90(image, k, axes=(1, 2))
        rotated_mask = np.rot90(mask, k, axes=(0, 1))
    elif image.ndim == 2:
        rotated_image = np.rot90(image, k, axes=(0, 1))
        rotated_mask = np.rot90(mask, k, axes=(0, 1))
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")

    return rotated_image, rotated_mask


def random_flip_rotate(
    image: np.ndarray,
    mask: np.ndarray,
    p_flip: float = 0.5,
    p_rotate: float = 0.5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply random horizontal flip, vertical flip, and/or rotation.

    Args:
        image: Image array of shape (C, H, W) or (H, W, C)
        mask: Mask array of shape (H, W)
        p_flip: Probability of applying any flip (horizontal or vertical)
        p_rotate: Probability of applying rotation (90, 180, or 270 degrees)

    Returns:
        Tuple of (augmented_image, augmented_mask)
    """
    # We'll apply flip and rotation independently
    if random.random() < p_flip:
        # Choose randomly between horizontal and vertical flip
        if random.random() < 0.5:
            image, mask = horizontal_flip(image, mask)
        else:
            image, mask = vertical_flip(image, mask)

    if random.random() < p_rotate:
        # Choose random k in {1, 2, 3}
        k = random.choice([1, 2, 3])
        image, mask = rotate_90(image, mask, k)

    return image, mask


def augmentations_list() -> list:
    """
    Return a list of available augmentation functions.

    Returns:
        List of function names as strings
    """
    return [
        "horizontal_flip",
        "vertical_flip",
        "rotate_90",
        "random_flip_rotate",
    ]


# Example usage (for debugging)
if __name__ == "__main__":
    import numpy as np

    # Dummy data
    image = np.random.rand(3, 128, 128).astype(np.float32)  # CHW
    mask = np.random.randint(0, 2, size=(128, 128)).astype(np.int64)

    print("Original image shape:", image.shape)
    print("Original mask shape:", mask.shape)

    # Test horizontal flip
    flip_img, flip_mask = horizontal_flip(image, mask)
    print("\nAfter horizontal flip:")
    print("Image shape:", flip_img.shape)
    print("Mask shape:", flip_mask.shape)

    # Test vertical flip
    vflip_img, vflip_mask = vertical_flip(image, mask)
    print("\nAfter vertical flip:")
    print("Image shape:", vflip_img.shape)
    print("Mask shape:", vflip_mask.shape)

    # Test rotation
    rot_img, rot_mask = rotate_90(image, mask, k=1)
    print("\nAfter rotation 90:")
    print("Image shape:", rot_img.shape)
    print("Mask shape:", rot_mask.shape)

    # Test random flip rotate
    aug_img, aug_mask = random_flip_rotate(image, mask, p_flip=0.8, p_rotate=0.8)
    print("\nAfter random flip/rotate:")
    print("Image shape:", aug_img.shape)
    print("Mask shape:", aug_mask.shape)