"""
Evaluation script for Landslide4Sense segmentation model.

Computes metrics (IoU, Dice, precision, recall, etc.) on validation or test set,
performs threshold analysis, and saves results.
"""

import os
import sys
import json
import logging
import numpy as np
import random
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Import our custom modules
from .landslide4sense_dataset import Landslide4SenseDataset
from .unet_resnet34 import UNetResNet34
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


def load_model_from_checkpoint(
    checkpoint_path: str,
    device: torch.device,
) -> Tuple[torch.nn.Module, Landslide4SensePreprocessor, dict]:
    """
    Load model and preprocessor from a checkpoint.

    Args:
        checkpoint_path: Path to the checkpoint file (.pth)
        device: Device to load the model on

    Returns:
        Tuple of (model, preprocessor, config)
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint.get("config", {})

    # Initialize model
    model = UNetResNet34(
        in_channels=config.get("in_channels", 14),
        num_classes=config.get("num_classes", 1),
        pretrained=False,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    # Reconstruct preprocessor
    preprocessor_state = checkpoint.get("preprocessor_state", {})
    preprocessor = Landslide4SensePreprocessor(
        normalize_bands=preprocessor_state.get("normalize_bands", True),
        band_means=np.array(preprocessor_state["band_means"]) if preprocessor_state.get("band_means") is not None else None,
        band_stds=np.array(preprocessor_state["band_stds"]) if preprocessor_state.get("band_stds") is not None else None,
    )
    # Note: is_fitted is set by the preprocessor based on whether means/stds are provided

    logger.info(f"Loaded model from checkpoint: {checkpoint_path}")
    logger.info(f"Model epoch: {checkpoint.get('epoch', 'unknown')}")
    logger.info(f"Best validation Dice: {checkpoint.get('best_val_dice', 'unknown')}")

    return model, preprocessor, config


def get_dataloader(
    dataset_path: str,
    split: str = "test",
    batch_size: int = 8,
    num_workers: int = 4,
) -> DataLoader:
    """
    Create a data loader for the specified split.

    Args:
        dataset_path: Path to the dataset root directory
        split: One of 'train', 'val', 'test'
        batch_size: Batch size
        num_workers: Number of worker processes

    Returns:
        DataLoader for the specified split
    """
    dataset = Landslide4SenseDataset(
        root_dir=dataset_path,
        split=split,
        transform=None,  # We'll apply preprocessing separately
    )

    # We need to fit the preprocessor on the training set to get normalization statistics
    # For evaluation, we should use the same preprocessing as used during training
    # For simplicity, we'll load the preprocessor from the checkpoint (already done in load_model_from_checkpoint)
    # However, this function is standalone; we'll assume the preprocessor is passed in.
    # We'll modify the caller to pass the preprocessor.

    # For now, we'll create a dummy preprocessor and let the caller replace it.
    preprocessor = Landslide4SensePreprocessor(normalize_bands=False)

    # Define a transformed dataset that applies preprocessing
    class PreprocessedDataset(torch.utils.data.Dataset):
        def __init__(self, dataset, preprocessor):
            self.dataset = dataset
            self.preprocessor = preprocessor

        def __len__(self):
            return len(self.dataset)

        def __getitem__(self, idx):
            image, mask = self.dataset[idx]
            # Preprocess
            try:
                image = self.preprocessor.preprocess_sample(image)
                mask = self.preprocessor.preprocess_label(mask)
            except Exception as e:
                logger.error(f"Preprocessing failed for sample {idx}: {e}")
                raise
            return image, mask

    preprocessed_dataset = PreprocessedDataset(dataset, preprocessor)

    loader = DataLoader(
        preprocessed_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    return loader, preprocessor


def compute_metrics(
    probs: np.ndarray,
    targets: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, float]:
    """
    Compute metrics for binary segmentation.

    Args:
        probs: Predicted probabilities of shape (N, H, W) or (N, 1, H, W)
        targets: Ground truth labels of shape (N, H, W) or (N, 1, H, W) with values 0 or 1
        threshold: Threshold for binarizing probabilities

    Returns:
        Dictionary of metrics
    """
    # Ensure same shape
    if probs.shape != targets.shape:
        if probs.shape[1] == 1 and targets.ndim == 3:
            probs = probs.squeeze(1)
        elif probs.ndim == 3 and targets.shape[1] == 1:
            targets = targets.squeeze(1)
        else:
            raise ValueError(f"Shape mismatch: probs {probs.shape}, targets {targets.shape}")

    # Flatten
    probs_flat = probs.flatten()
    targets_flat = targets.flatten()

    # Binarize predictions
    preds = (probs_flat >= threshold).astype(np.uint8)
    targets_flat = targets_flat.astype(np.uint8)

    # Compute confusion matrix elements
    tp = np.sum((preds == 1) & (targets_flat == 1))
    tn = np.sum((preds == 0) & (targets_flat == 0))
    fp = np.sum((preds == 1) & (targets_flat == 0))
    fn = np.sum((preds == 0) & (targets_flat == 1))

    # Compute metrics
    epsilon = 1e-8
    precision = tp / (tp + fp + epsilon)
    recall = tp / (tp + fn + epsilon)
    specificity = tn / (tn + fp + epsilon)
    f1_score = 2 * precision * recall / (precision + recall + epsilon)
    iou = tp / (tp + fp + fn + epsilon)
    dice = 2 * tp / (2 * tp + fp + fn + epsilon)
    accuracy = (tp + tn) / (tp + tn + fp + fn + epsilon)

    return {
        "threshold": threshold,
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(specificity),
        "f1_score": float(f1_score),
        "iou": float(iou),
        "dice": float(dice),
        "accuracy": float(accuracy),
    }


def threshold_analysis(
    probs: np.ndarray,
    targets: np.ndarray,
    thresholds: Optional[List[float]] = None,
) -> List[Dict[str, float]]:
    """
    Perform threshold analysis by computing metrics at various thresholds.

    Args:
        probs: Predicted probabilities of shape (N, H, W) or (N, 1, H, W)
        targets: Ground truth labels of shape (N, H, W) or (N, 1, H, W)
        thresholds: List of thresholds to evaluate (default: 0.0 to 1.0 step 0.01)

    Returns:
        List of dictionaries, each containing metrics for a threshold
    """
    if thresholds is None:
        thresholds = [t / 100.0 for t in range(0, 101, 1)]  # 0.00 to 1.00 step 0.01

    results = []
    for thresh in thresholds:
        metrics = compute_metrics(probs, targets, threshold=thresh)
        results.append(metrics)

    return results


def save_predictions(
    images: np.ndarray,
    probs: np.ndarray,
    targets: np.ndarray,
    output_dir: str,
    num_samples: int = 5,
    threshold: float = 0.5,
):
    """
    Save a few prediction examples as images.

    Args:
        images: Input images of shape (N, C, H, W) or (N, H, W, C)
        probs: Predicted probabilities of shape (N, H, W)
        targets: Ground truth labels of shape (N, H, W)
        output_dir: Directory to save images
        num_samples: Number of samples to save
        threshold: Threshold for binarizing predictions
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # We'll save the first num_samples
    for i in range(min(num_samples, len(images))):
        # Create a figure with subplots: input image (showing RGB bands if available), ground truth, prediction
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))

        # Determine how to display the input image
        img = images[i]
        if img.ndim == 3:
            # Assume CHW or HWC
            if img.shape[0] == 3 or img.shape[0] == 4:
                # CHW with 3 or 4 channels (RGB or RGBA)
                img_display = np.transpose(img, (1, 2, 0))  # HWC
                # If we have more than 3 bands (e.g., 14), we can't display all; show first 3 as RGB
                if img.shape[0] > 3:
                    img_display = img_display[:, :, :3]  # Take first 3 bands
                # Normalize for display
                img_display = (img_display - img_display.min()) / (img_display.max() - img_display.min() + 1e-8)
            else:
                # Assume HWC with multiple bands
                # Show first 3 bands as RGB
                if img.shape[2] >= 3:
                    img_display = img[:, :, :3]
                else:
                    # If less than 3 bands, repeat the single band
                    img_display = np.repeat(img, 3, axis=2)
                img_display = (img_display - img_display.min()) / (img_display.max() - img_display.min() + 1e-8)
        else:
            # Grayscale
            img_display = img
            img_display = np.stack([img_display] * 3, axis=-1)
            img_display = (img_display - img_display.min()) / (img_display.max() - img_display.min() + 1e-8)

        axes[0].imshow(img_display)
        axes[0].set_title("Input Image (RGB bands)")
        axes[0].axis("off")

        # Ground truth
        axes[1].imshow(targets[i], cmap="gray", vmin=0, vmax=1)
        axes[1].set_title("Ground Truth")
        axes[1].axis("off")

        # Prediction
        pred = (probs[i] >= threshold).astype(np.uint8)
        axes[2].imshow(pred, cmap="gray", vmin=0, vmax=1)
        axes[2].set_title(f"Prediction (threshold={threshold:.2f})")
        axes[2].axis("off")

        plt.tight_layout()
        save_path = output_dir / f"sample_{i:03d}.png"
        plt.savefig(save_path, dpi=150)
        plt.close(fig)

    logger.info(f"Saved {min(num_samples, len(images))} prediction examples to {output_dir}")


def evaluate(
    model_path: str,
    dataset_path: str,
    split: str = "test",
    batch_size: int = 8,
    num_workers: int = 4,
    output_dir: str = "./evaluation_results",
    save_viz: bool = True,
    num_viz_samples: int = 5,
):
    """
    Main evaluation function.

    Args:
        model_path: Path to the model checkpoint (.pth)
        dataset_path: Path to the dataset root directory
        split: Which split to evaluate ('val' or 'test')
        batch_size: Batch size for evaluation
        num_workers: Number of worker processes
        output_dir: Directory to save results
        save_viz: Whether to save visualization examples
        num_viz_samples: Number of visualization examples to save
    """
    # Set seed for reproducibility
    set_seed(42)

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Validate paths
    model_path = Path(model_path)
    dataset_path = Path(dataset_path)
    if not model_path.exists():
        logger.error(f"Model checkpoint not found: {model_path}")
        sys.exit(1)
    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        sys.exit(1)

    # Load model and preprocessor from checkpoint
    model, preprocessor, config = load_model_from_checkpoint(str(model_path), device)
    logger.info(f"Model configuration: {json.dumps(config, indent=2)}")

    # Get data loader for the specified split
    # We'll reuse the preprocessor from the checkpoint
    dataset = Landslide4SenseDataset(
        root_dir=dataset_path,
        split=split,
        transform=None,
    )

    # Create a transformed dataset that uses the loaded preprocessor
    class PreprocessedDataset(torch.utils.data.Dataset):
        def __init__(self, dataset, preprocessor):
            self.dataset = dataset
            self.preprocessor = preprocessor

        def __len__(self):
            return len(self.dataset)

        def __getitem__(self, idx):
            image, mask = self.dataset[idx]
            # Convert to numpy for preprocessing
            image_np = image.numpy()
            mask_np = mask.numpy()
            try:
                image_np = self.preprocessor.preprocess_sample(image_np)
                mask_np = self.preprocessor.preprocess_label(mask_np)
            except Exception as e:
                logger.error(f"Preprocessing failed for sample {idx}: {e}")
                raise
            # Convert back to tensor
            image = torch.from_numpy(image_np)
            mask = torch.from_numpy(mask_np)
            return image, mask

    preprocessed_dataset = PreprocessedDataset(dataset, preprocessor)

    loader = DataLoader(
        preprocessed_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    logger.info(f"Evaluating on {split} set: {len(dataset)} samples")

    # Initialize lists to collect results
    all_probs = []
    all_targets = []
    all_images = []  # For visualization (we'll store a few)
    total_loss = 0.0
    loss_fn = nn.BCEWithLogitsLoss()  # We'll use BCE for loss calculation

    # Evaluation loop
    model.eval()
    with torch.no_grad():
        for batch_idx, (images, masks) in enumerate(loader):
            images = images.to(device)
            masks = masks.to(device)

            # Forward pass
            logits = model(images)
            # Ensure mask has channel dimension and float type for BCE loss
            masks = masks.unsqueeze(1).float()
            loss = loss_fn(logits, masks)
            total_loss += loss.item()

            # Get probabilities
            probs = torch.sigmoid(logits)
            probs_np = probs.cpu().numpy()
            masks_np = masks.cpu().numpy()
            images_np = images.cpu().numpy()

            # Store for metric calculation
            all_probs.append(probs_np)
            all_targets.append(masks_np)
            # Store a few images for visualization
            if len(all_images) < num_viz_samples:
                all_images.append(images_np)

            if batch_idx % 50 == 0:
                logger.info(
                    f"Processed batch {batch_idx}/{len(loader)}"
                )

    # Concatenate batches
    all_probs = np.concatenate(all_probs, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)
    all_images = np.concatenate(all_images, axis=0) if all_images else np.array([])

    # Compute average loss
    avg_loss = total_loss / len(loader) if len(loader) > 0 else 0.0

    # Compute metrics at default threshold (0.5)
    default_threshold = 0.5
    metrics_default = compute_metrics(all_probs, all_targets, threshold=default_threshold)

    # Perform threshold analysis
    thresholds = [t / 100.0 for t in range(0, 101, 5)]  # Every 5% from 0 to 100
    threshold_results = threshold_analysis(all_probs, all_targets, thresholds=thresholds)

    # Find best threshold based on Dice score
    best_threshold = None
    best_dice = -1.0
    for result in threshold_results:
        if result["dice"] > best_dice:
            best_dice = result["dice"]
            best_threshold = result["threshold"]

    logger.info(f"Best threshold based on Dice: {best_threshold:.2f} (Dice = {best_dice:.4f})")

    # Prepare results dictionary
    results = {
        "dataset_path": str(dataset_path),
        "model_path": str(model_path),
        "split": split,
        "num_samples": len(all_targets),
        "average_loss": float(avg_loss),
        "metrics_at_threshold_0.5": metrics_default,
        "best_threshold": float(best_threshold),
        "best_dice": float(best_dice),
        "threshold_analysis": threshold_results,
    }

    # Save results to JSON file
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / f"evaluation_{split}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Evaluation results saved to: {results_file}")

    # Save visualization examples
    if save_viz and len(all_images) > 0:
        viz_dir = output_dir / "visualizations"
        save_predictions(
            images=all_images,
            probs=all_probs,
            targets=all_targets,
            output_dir=str(viz_dir),
            num_samples=num_viz_samples,
            threshold=default_threshold,
        )
        # Also save visualizations for best threshold
        viz_dir_best = output_dir / "visualizations_best_threshold"
        save_predictions(
            images=all_images,
            probs=all_probs,
            targets=all_targets,
            output_dir=str(viz_dir_best),
            num_samples=num_viz_samples,
            threshold=best_threshold,
        )

    # Print summary
    logger.info("\n=== Evaluation Summary ===")
    logger.info(f"Dataset: {dataset_path}")
    logger.info(f"Split: {split}")
    logger.info(f"Number of samples: {len(all_targets)}")
    logger.info(f"Average loss: {avg_loss:.4f}")
    logger.info(f"Metrics at threshold 0.5:")
    for key, value in metrics_default.items():
        if key != "threshold":
            logger.info(f"  {key}: {value:.4f}")
    logger.info(f"Best threshold: {best_threshold:.2f}")
    logger.info(f"Best Dice: {best_dice:.4f}")
    logger.info(f"Results saved to: {results_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate Landslide4Sense segmentation model")
    parser.add_argument("--model_path", type=str, required=True, help="Path to model checkpoint (.pth)")
    parser.add_argument("--dataset_path", type=str, required=True, help="Path to dataset root directory")
    parser.add_argument("--split", type=str, default="test", choices=["val", "test"], help="Dataset split to evaluate")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size for evaluation")
    parser.add_argument("--num_workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("--output_dir", type=str, default="./evaluation_results", help="Directory to save results")
    parser.add_argument("--save_viz", action="store_true", help="Save visualization examples")
    parser.add_argument("--num_viz_samples", type=int, default=5, help="Number of visualization samples to save")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    # Set seed
    set_seed(args.seed)

    # Run evaluation
    evaluate(
        model_path=args.model_path,
        dataset_path=args.dataset_path,
        split=args.split,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        output_dir=args.output_dir,
        save_viz=args.save_viz,
        num_viz_samples=args.num_viz_samples,
    )