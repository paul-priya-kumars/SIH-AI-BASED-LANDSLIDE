"""
Training pipeline for Landslide4Sense segmentation model.

Implements a reproducible training loop with validation, checkpointing,
and early stopping.
"""

import os
import sys
import json
import logging
import random
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingLR

# Import our custom modules
from .landslide4sense_dataset import Landslide4SenseDataset
from .unet_resnet34 import UNetResNet34
from .loss import get_loss_function, DiceLoss
from .augmentation import horizontal_flip, vertical_flip, rotate_90, random_flip_rotate
from ..preprocessing.landslide4sense import Landslide4SensePreprocessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def set_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    # For reproducibility in CUDA operations (may slow down)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


class SegmentationTransformer:
    """
    Combined transformation for image and mask pairs.
    Applies the same augmentation to both image and mask.
    """

    def __init__(self, p_flip: float = 0.5, p_rotate: float = 0.5):
        self.p_flip = p_flip
        self.p_rotate = p_rotate

    def __call__(self, image: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # Apply random flip and rotation
        image, mask = random_flip_rotate(image, mask, p_flip=self.p_flip, p_rotate=self.p_rotate)
        return image, mask


def get_dataloaders(
    dataset_path: str,
    batch_size: int = 8,
    num_workers: int = 4,
    augment: bool = True,
    validation_split: float = 0.1,
) -> Tuple[DataLoader, DataLoader, Landslide4SensePreprocessor]:
    """
    Create training and validation data loaders.

    Args:
        dataset_path: Path to the dataset root directory
        batch_size: Batch size for training and validation
        num_workers: Number of worker processes for data loading
        augment: Whether to apply data augmentation to training set
        validation_split: Fraction of training data to use for validation (if no explicit val split)

    Returns:
        Tuple of (train_loader, val_loader, preprocessor)
    """
    dataset_path = Path(dataset_path)

    # Check if explicit validation split exists
    val_images_dir = dataset_path / "val" / "images"
    if val_images_dir.is_dir():
        # Use explicit train and val splits
        train_dataset = Landslide4SenseDataset(
            root_dir=dataset_path,
            split="train",
            transform=None,  # We'll apply augmentation separately
        )
        val_dataset = Landslide4SenseDataset(
            root_dir=dataset_path,
            split="val",
            transform=None,
        )
    else:
        # Use train split and create a validation split from it
        full_train_dataset = Landslide4SenseDataset(
            root_dir=dataset_path,
            split="train",
            transform=None,
        )
        # Split the dataset
        total_size = len(full_train_dataset)
        val_size = int(validation_split * total_size)
        train_size = total_size - val_size
        train_dataset, val_dataset = torch.utils.data.random_split(
            full_train_dataset, [train_size, val_size],
            generator=torch.Generator().manual_seed(42)
        )

    # Define preprocessing
    preprocessor = Landslide4SensePreprocessor(normalize_bands=True)

    # We'll fit the preprocessor on a subset of the training data
    # For efficiency, we'll sample a few batches to compute statistics
    logger.info("Fitting preprocessor on training data...")
    temp_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers
    )
    # Collect a few batches to compute mean and std
    means = []
    stds = []
    samples_processed = 0
    max_samples = 500  # Limit the number of samples for fitting
    for batch_idx, (images, masks) in enumerate(temp_loader):
        # images: (B, C, H, W)
        # Convert to numpy and compute per-band mean and std
        images_np = images.numpy()  # (B, C, H, W)
        # Transpose to (B, H, W, C) for easier computation
        images_np = np.transpose(images_np, (0, 2, 3, 1))  # (B, H, W, C)
        # Reshape to (B*H*W, C)
        pixels = images_np.reshape(-1, images_np.shape[-1])
        means.append(np.mean(pixels, axis=0))
        stds.append(np.std(pixels, axis=0))
        samples_processed += pixels.shape[0]
        if samples_processed >= max_samples:
            break

    if means:
        band_means = np.mean(means, axis=0)
        band_stds = np.mean(stds, axis=0)
        # Avoid zero std
        band_stds = np.where(band_stds < 1e-8, 1.0, band_stds)
        preprocessor = Landslide4SensePreprocessor(
            normalize_bands=True,
            band_means=band_means,
            band_stds=band_stds
        )
        logger.info(f"Preprocessor fitted with mean={band_means}, std={band_stds}")
    else:
        logger.warning("Could not fit preprocessor; using unnormalized data")
        preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Define augmentation transform
    if augment:
        aug_transform = SegmentationTransformer(p_flip=0.5, p_rotate=0.5)
    else:
        aug_transform = None

    # Wrap datasets to apply preprocessing and augmentation
    class TransformedDataset(torch.utils.data.Dataset):
        def __init__(self, dataset, preprocessor, augment_transform=None):
            self.dataset = dataset
            self.preprocessor = preprocessor
            self.augment_transform = augment_transform

        def __len__(self):
            return len(self.dataset)

        def __getitem__(self, idx):
            # Load raw sample and mask
            image, mask = self.dataset[idx]  # From Landslide4SenseDataset: image tensor (C, H, W), mask tensor (H, W)
            # Convert to numpy for augmentation and preprocessing
            image_np = image.numpy()
            mask_np = mask.numpy()

            # Apply augmentation if specified
            if self.augment_transform is not None:
                image_np, mask_np = self.augment_transform(image_np, mask_np)
                # Ensure arrays are contiguous (no negative strides) for torch.from_numpy
                image_np = image_np.copy()
                mask_np = mask_np.copy()

            # Apply preprocessing (validation, conversion, normalization)
            try:
                image_np = self.preprocessor.preprocess_sample(image_np)
                mask_np = self.preprocessor.preprocess_label(mask_np)
            except Exception as e:
                logger.error(f"Preprocessing failed for sample {idx}: {e}")
                # Return a zero tensor or skip? We'll raise for now
                raise

            # Convert back to tensor
            image = torch.from_numpy(image_np)
            mask = torch.from_numpy(mask_np)

            return image, mask

    train_dataset_transformed = TransformedDataset(
        train_dataset, preprocessor, aug_transform if augment else None
    )
    val_dataset_transformed = TransformedDataset(
        val_dataset, preprocessor, None  # No augmentation for validation
    )

    # Create data loaders
    train_loader = DataLoader(
        train_dataset_transformed,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
    )
    val_loader = DataLoader(
        val_dataset_transformed,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    logger.info(
        f"Created data loaders: {len(train_dataset)} train samples, "
        f"{len(val_dataset)} val samples"
    )

    return train_loader, val_loader, preprocessor


def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    epoch: int,
) -> float:
    """
    Train for one epoch.

    Returns:
        Average loss over the epoch
    """
    model.train()
    running_loss = 0.0
    num_batches = 0

    for batch_idx, (images, masks) in enumerate(loader):
        images = images.to(device)
        masks = masks.to(device)

        # Forward pass
        optimizer.zero_grad()
        outputs = model(images)
        loss = loss_fn(outputs, masks)

        # Backward pass
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        num_batches += 1

        if batch_idx % 50 == 0:
            logger.info(
                f"Epoch {epoch}, Batch {batch_idx}/{len(loader)}, "
                f"Loss: {loss.item():.4f}"
            )

    epoch_loss = running_loss / num_batches if num_batches > 0 else 0.0
    return epoch_loss


def validate(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    """
    Validate the model.

    Returns:
        Tuple of (average loss, dice coefficient)
    """
    model.eval()
    running_loss = 0.0
    dice_scores = []
    num_batches = 0

    with torch.no_grad():
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)

            outputs = model(images)
            loss = loss_fn(outputs, masks)
            running_loss += loss.item()

            # Compute Dice coefficient
            probs = torch.sigmoid(outputs)
            preds = (probs > 0.5).float()
            intersection = (preds * masks).sum()
            union = preds.sum() + masks.sum()
            dice = (2.0 * intersection) / (union + 1e-8)
            dice_scores.append(dice.item())

            num_batches += 1

    avg_loss = running_loss / num_batches if num_batches > 0 else 0.0
    avg_dice = np.mean(dice_scores) if dice_scores else 0.0
    return avg_loss, avg_dice


def save_checkpoint(
    state: Dict[str, Any],
    checkpoint_dir: str,
    filename: str = "checkpoint.pth",
    is_best: bool = False,
):
    """
    Save model checkpoint.

    Args:
        state: Dictionary containing model state_dict, optimizer state_dict, epoch, etc.
        checkpoint_dir: Directory to save checkpoints
        filename: Name of the checkpoint file
        is_best: If True, also copy to 'best_model.pth'
    """
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = checkpoint_dir / filename
    torch.save(state, checkpoint_path)
    logger.info(f"Saved checkpoint: {checkpoint_path}")

    if is_best:
        best_path = checkpoint_dir / "best_model.pth"
        torch.save(state, best_path)
        logger.info(f"Saved best model: {best_path}")


def train():
    """
    Main training function.
    """
    # Configuration from environment variables with defaults
    config = {
        "dataset_path": os.getenv("DATASET_PATH", "./datasets/landslide4sense"),
        "batch_size": int(os.getenv("BATCH_SIZE", "8")),
        "num_epochs": int(os.getenv("NUM_EPOCHS", "50")),
        "learning_rate": float(os.getenv("LEARNING_RATE", "0.001")),
        "weight_decay": float(os.getenv("WEIGHT_DECAY", "1e-4")),
        "optimizer": os.getenv("OPTIMIZER", "adam").lower(),
        "scheduler": os.getenv("SCHEDULER", "reduce_on_plateau").lower(),
        "patience": int(os.getenv("PATIENCE", "10")),
        "seed": int(os.getenv("SEED", "42")),
        "augment": os.getenv("AUGMENT", "true").lower() == "true",
        "loss_function": os.getenv("LOSS_FUNCTION", "bcedice").lower(),
        "num_workers": int(os.getenv("NUM_WORKERS", "4")),
        "checkpoint_dir": os.getenv("CHECKPOINT_DIR", "./checkpoints"),
        "early_stopping": os.getenv("EARLY_STOPPING", "true").lower() == "true",
    }

    # Set random seed
    set_seed(config["seed"])

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Log configuration
    logger.info("Training configuration:")
    for key, value in config.items():
        logger.info(f"  {key}: {value}")

    # Validate dataset path
    dataset_path = Path(config["dataset_path"])
    if not dataset_path.exists():
        logger.error(f"Dataset not found at {dataset_path}")
        logger.error("Please download the Landslide4Sense dataset and set DATASET_PATH accordingly.")
        sys.exit(1)

    # Get data loaders and preprocessor
    try:
        train_loader, val_loader, preprocessor = get_dataloaders(
            dataset_path=str(dataset_path),
            batch_size=config["batch_size"],
            num_workers=config["num_workers"],
            augment=config["augment"],
        )
    except Exception as e:
        logger.error(f"Failed to create data loaders: {e}")
        sys.exit(1)

    # Initialize model
    model = UNetResNet34(
        in_channels=14,
        num_classes=1,
        pretrained=False,  # Not using pretrained weights for 14-channel input
    )
    model = model.to(device)
    logger.info(f"Model initialized: {model.__class__.__name__}")

    # Define loss function
    loss_fn = get_loss_function(config["loss_function"])
    logger.info(f"Loss function: {config['loss_function']}")

    # Define optimizer
    if config["optimizer"] == "adam":
        optimizer = optim.Adam(
            model.parameters(),
            lr=config["learning_rate"],
            weight_decay=config["weight_decay"],
        )
    elif config["optimizer"] == "sgd":
        optimizer = optim.SGD(
            model.parameters(),
            lr=config["learning_rate"],
            momentum=0.9,
            weight_decay=config["weight_decay"],
        )
    else:
        logger.error(f"Unsupported optimizer: {config['optimizer']}")
        sys.exit(1)

    # Define learning rate scheduler
    if config["scheduler"] == "reduce_on_plateau":
        scheduler = ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=5
        )
    elif config["scheduler"] == "cosine":
        scheduler = CosineAnnealingLR(
            optimizer, T_max=config["num_epochs"], eta_min=1e-6
        )
    elif config["scheduler"] == "none":
        scheduler = None
    else:
        logger.error(f"Unsupported scheduler: {config['scheduler']}")
        sys.exit(1)

    # Training loop
    best_val_dice = 0.0
    epochs_no_improve = 0
    start_epoch = 0

    # Optionally resume from checkpoint
    resume_checkpoint = os.getenv("RESUME_CHECKPOINT")
    if resume_checkpoint and Path(resume_checkpoint).exists():
        logger.info(f"Resuming from checkpoint: {resume_checkpoint}")
        checkpoint = torch.load(resume_checkpoint, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
        best_val_dice = checkpoint.get("best_val_dice", 0.0)
        epochs_no_improve = checkpoint.get("epochs_no_improve", 0)
        logger.info(f"Resumed from epoch {start_epoch}")

    for epoch in range(start_epoch, config["num_epochs"]):
        logger.info(f"\n=== Epoch {epoch+1}/{config['num_epochs']} ===")

        # Train
        train_loss = train_one_epoch(
            model, train_loader, loss_fn, optimizer, device, epoch+1
        )
        logger.info(f"Training loss: {train_loss:.4f}")

        # Validate
        val_loss, val_dice = validate(
            model, val_loader, loss_fn, device
        )
        logger.info(f"Validation loss: {val_loss:.4f}, Validation Dice: {val_dice:.4f}")

        # Update learning rate scheduler
        if scheduler is not None:
            if isinstance(scheduler, ReduceLROnPlateau):
                scheduler.step(val_dice)  # Step based on validation Dice (maximize)
            else:
                scheduler.step()

        # Prepare checkpoint state
        state = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
            "loss_fn": config["loss_function"],
            "best_val_dice": best_val_dice,
            "epochs_no_improve": epochs_no_improve,
            "config": config,
            "preprocessor_state": {
                "band_means": preprocessor.band_means.tolist() if preprocessor.band_means is not None else None,
                "band_stds": preprocessor.band_stds.tolist() if preprocessor.band_stds is not None else None,
                "normalize_bands": preprocessor.normalize_bands,
                "is_fitted": preprocessor.is_fitted(),
            },
        }

        # Check if this is the best model so far
        is_best = val_dice > best_val_dice
        if is_best:
            best_val_dice = val_dice
            epochs_no_improve = 0
            logger.info(f"New best validation Dice: {best_val_dice:.4f}")
        else:
            epochs_no_improve += 1
            logger.info(
                f"No improvement for {epochs_no_improve} epoch(s). "
                f"Best Dice: {best_val_dice:.4f}"
            )

        # Save checkpoint
        save_checkpoint(
            state,
            checkpoint_dir=config["checkpoint_dir"],
            filename=f"checkpoint_epoch_{epoch+1}.pth",
            is_best=is_best,
        )

        # Early stopping
        if config["early_stopping"] and epochs_no_improve >= config["patience"]:
            logger.info(
                f"Early stopping triggered after {epochs_no_improve} epochs without improvement."
            )
            break

    logger.info("Training completed.")
    logger.info(f"Best validation Dice: {best_val_dice:.4f}")

    # Save final model (last epoch)
    final_state = {
        "epoch": config["num_epochs"] - 1,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "config": config,
    }
    save_checkpoint(
        final_state,
        checkpoint_dir=config["checkpoint_dir"],
        filename="final_model.pth",
        is_best=False,
    )


if __name__ == "__main__":
    train()