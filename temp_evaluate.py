#!/usr/bin/env python3
"""
Temporary evaluation script to compute metrics from the best model checkpoint.
This script does not modify any existing project files.
"""

import os
import sys
import json
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Add the project root to sys.path so we can import the modules
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our custom modules
from phase6.image_analysis.training.landslide4sense_dataset import Landslide4SenseDataset
from phase6.image_analysis.training.unet_resnet34 import UNetResNet34
from phase6.image_analysis.preprocessing.landslide4sense import Landslide4SensePreprocessor

def set_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def load_model_and_preprocessor(checkpoint_path: str, device: torch.device):
    """Load model and preprocessor from checkpoint."""
    # Handle PyTorch 2.6+ weights_only security feature
    try:
        # First try with weights_only=True (secure default)
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=True)
    except Exception:
        # If that fails, use weights_only=False since we trust our own checkpoint files
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)

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

    print(f"Loaded model from checkpoint: {checkpoint_path}")
    print(f"Model epoch: {checkpoint.get('epoch', 'unknown')}")
    print(f"Best validation Dice: {checkpoint.get('best_val_dice', 'unknown')}")

    return model, preprocessor, config

def get_test_loader(dataset_path: str, batch_size: int = 8, num_workers: int = 0):
    """Create a data loader for the test set."""
    dataset = Landslide4SenseDataset(
        root_dir=dataset_path,
        split="test",
        transform=None,  # We'll apply preprocessing separately
    )

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
                print(f"Preprocessing failed for sample {idx}: {e}")
                raise
            return image, mask

    # We need to create a preprocessor, but we'll do it after loading the checkpoint
    # For now, we'll return the dataset and create the preprocessed loader later
    return dataset

def compute_metrics(probs: np.ndarray, targets: np.ndarray, threshold: float = 0.5) -> dict:
    """Compute metrics for binary segmentation."""
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

def threshold_analysis(probs: np.ndarray, targets: np.ndarray, thresholds: list = None) -> list:
    """Perform threshold analysis by computing metrics at various thresholds."""
    if thresholds is None:
        thresholds = [t / 100.0 for t in range(0, 101, 5)]  # Every 5% from 0 to 100

    results = []
    for thresh in thresholds:
        metrics = compute_metrics(probs, targets, threshold=thresh)
        results.append(metrics)

    return results

def main():
    """Main evaluation function."""
    print("=== Landslide4sense Model Evaluation ===")

    # Set seed for reproducibility
    set_seed(42)

    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Paths
    checkpoint_path = os.path.join(project_root, "checkpoints", "best_model.pth")
    dataset_path = os.path.join(project_root, "datasets", "landslide4sense")

    # Validate paths
    if not os.path.exists(checkpoint_path):
        print(f"ERROR: Model checkpoint not found: {checkpoint_path}")
        return

    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found: {dataset_path}")
        return

    # Load model and preprocessor from checkpoint
    try:
        model, preprocessor, config = load_model_and_preprocessor(checkpoint_path, device)
    except Exception as e:
        print(f"ERROR: Failed to load model from checkpoint: {e}")
        return

    print(f"Model configuration: {json.dumps(config, indent=2)}")

    # Get test dataset
    try:
        test_dataset = Landslide4SenseDataset(
            root_dir=dataset_path,
            split="test",
            transform=None,
        )
        print(f"Test dataset size: {len(test_dataset)} samples")
    except Exception as e:
        print(f"ERROR: Failed to load test dataset: {e}")
        return

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
                print(f"Preprocessing failed for sample {idx}: {e}")
                raise
            # Convert back to tensor
            image = torch.from_numpy(image_np)
            mask = torch.from_numpy(mask_np)
            return image, mask

    preprocessed_dataset = PreprocessedDataset(test_dataset, preprocessor)

    # Create data loader
    test_loader = DataLoader(
        preprocessed_dataset,
        batch_size=config.get("batch_size", 8),
        shuffle=False,
        num_workers=config.get("num_workers", 0),
        pin_memory=True,
    )

    print(f"Evaluating on test set: {len(test_dataset)} samples")

    # Initialize lists to collect results
    all_probs = []
    all_targets = []
    total_loss = 0.0
    loss_fn = nn.BCEWithLogitsLoss()  # We'll use BCE for loss calculation

    # Evaluation loop
    model.eval()
    with torch.no_grad():
        for batch_idx, (images, masks) in enumerate(test_loader):
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

            # Store for metric calculation
            all_probs.append(probs_np)
            all_targets.append(masks_np)

            if batch_idx % 50 == 0:
                print(f"Processed batch {batch_idx}/{len(test_loader)}")

    # Concatenate batches
    all_probs = np.concatenate(all_probs, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)

    # Compute average loss
    avg_loss = total_loss / len(test_loader) if len(test_loader) > 0 else 0.0

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

    print(f"Best threshold based on Dice: {best_threshold:.2f} (Dice = {best_dice:.4f})")

    # Print results
    print("\n=== Evaluation Results ===")
    print(f"Dataset: {dataset_path}")
    print(f"Split: test")
    print(f"Number of samples: {len(all_targets)}")
    print(f"Average loss: {avg_loss:.4f}")
    print(f"Metrics at threshold {default_threshold}:")
    for key, value in metrics_default.items():
        if key != "threshold":
            print(f"  {key}: {value:.4f}")
    print(f"Best threshold: {best_threshold:.2f}")
    print(f"Best Dice: {best_dice:.4f}")

    # Return results for potential further use
    return {
        "dataset_path": dataset_path,
        "model_path": checkpoint_path,
        "split": "test",
        "num_samples": len(all_targets),
        "average_loss": float(avg_loss),
        "metrics_at_threshold_0.5": metrics_default,
        "best_threshold": float(best_threshold),
        "best_dice": float(best_dice),
        "threshold_analysis": threshold_results,
    }

if __name__ == "__main__":
    main()