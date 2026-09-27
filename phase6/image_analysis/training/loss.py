"""
Loss functions for Landslide4Sense segmentation.

Implements Dice loss, Binary Cross Entropy loss, and combinations,
with handling for class imbalance.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class DiceLoss(nn.Module):
    """
    Dice loss for binary segmentation.
    """

    def __init__(self, smooth: float = 1.0, reduction: str = "mean"):
        """
        Args:
            smooth: Smoothing factor to avoid division by zero
            reduction: Reduction method ('mean', 'sum', 'none')
        """
        super(DiceLoss, self).__init__()
        self.smooth = smooth
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute Dice loss.

        Args:
            logits: Predicted logits of shape (N, 1, H, W) or (N, H, W)
            targets: Ground truth labels of shape (N, 1, H, W) or (N, H, W) with values 0 or 1

        Returns:
            Dice loss tensor
        """
        # Ensure logits and targets have the same shape
        if logits.shape != targets.shape:
            # If logits have channel dimension and targets don't, squeeze or expand
            if logits.shape[1] == 1 and targets.ndim == 3:
                logits = logits.squeeze(1)
            elif logits.ndim == 3 and targets.shape[1] == 1:
                targets = targets.squeeze(1)
            else:
                raise ValueError(
                    f"Shape mismatch: logits {logits.shape}, targets {targets.shape}"
                )

        # Apply sigmoid to get probabilities
        probs = torch.sigmoid(logits)

        # Flatten the tensors
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)

        # Compute intersection and union
        intersection = (probs_flat * targets_flat).sum()
        union = probs_flat.sum() + targets_flat.sum()

        # Compute Dice coefficient
        dice_coeff = (2.0 * intersection + self.smooth) / (union + self.smooth)

        # Dice loss = 1 - Dice coefficient
        loss = 1.0 - dice_coeff

        if self.reduction == "mean":
            return loss
        elif self.reduction == "sum":
            return loss * len(probs_flat)  # Not exactly sum, but we return scalar
        elif self.reduction == "none":
            return loss
        else:
            raise ValueError(f"Unsupported reduction: {self.reduction}")


class BCEDiceLoss(nn.Module):
    """
    Combination of Binary Cross Entropy and Dice loss.
    """

    def __init__(
        self,
        bce_weight: float = 0.5,
        dice_weight: float = 0.5,
        bce_pos_weight: Optional[torch.Tensor] = None,
        dice_smooth: float = 1.0,
        reduction: str = "mean",
    ):
        """
        Args:
            bce_weight: Weight for BCE component
            dice_weight: Weight for Dice component
            bce_pos_weight: Weight for positive class in BCE (for imbalance)
            dice_smooth: Smoothing factor for Dice loss
            reduction: Reduction method
        """
        super(BCEDiceLoss, self).__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        self.reduction = reduction

        self.bce_loss = nn.BCEWithLogitsLoss(pos_weight=bce_pos_weight, reduction=reduction)
        self.dice_loss = DiceLoss(smooth=dice_smooth, reduction=reduction)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute combined BCE and Dice loss.

        Args:
            logits: Predicted logits of shape (N, 1, H, W) or (N, H, W)
            targets: Ground truth labels of shape (N, 1, H, W) or (N, H, W)

        Returns:
            Combined loss tensor
        """
        # Ensure logits and targets have the same shape for BCE loss
        if logits.shape != targets.shape:
            # If logits have channel dimension and targets don't, squeeze or expand
            if logits.shape[1] == 1 and targets.ndim == 3:
                logits_for_bce = logits.squeeze(1)
                targets_for_bce = targets
            elif logits.ndim == 3 and targets.shape[1] == 1:
                logits_for_bce = logits
                targets_for_bce = targets.squeeze(1)
            else:
                raise ValueError(
                    f"Shape mismatch: logits {logits.shape}, targets {targets.shape}"
                )
        else:
            logits_for_bce = logits
            targets_for_bce = targets

        # Convert targets to float for BCE loss (expects float targets)
        targets_for_bce = targets_for_bce.float()

        bce = self.bce_loss(logits_for_bce, targets_for_bce)
        dice = self.dice_loss(logits, targets)
        return self.bce_weight * bce + self.dice_weight * dice


class FocalLoss(nn.Module):
    """
    Focal loss for binary segmentation.
    Useful for class imbalance.
    """

    def __init__(
        self,
        alpha: float = 0.25,
        gamma: float = 2.0,
        reduction: str = "mean",
    ):
        """
        Args:
            alpha: Weighting factor for rare class (default: 0.25)
            gamma: Focusing parameter (default: 2.0)
            reduction: Reduction method
        """
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Compute focal loss.

        Args:
            logits: Predicted logits of shape (N, 1, H, W) or (N, H, W)
            targets: Ground truth labels of shape (N, 1, H, W) or (N, H, W)

        Returns:
            Focal loss tensor
        """
        # Ensure same shape
        if logits.shape != targets.shape:
            if logits.shape[1] == 1 and targets.ndim == 3:
                logits = logits.squeeze(1)
            elif logits.ndim == 3 and targets.shape[1] == 1:
                targets = targets.squeeze(1)
            else:
                raise ValueError(
                    f"Shape mismatch: logits {logits.shape}, targets {targets.shape}"
                )

        # Apply sigmoid
        probs = torch.sigmoid(logits)
        probs = probs.clamp(min=1e-6, max=1 - 1e-6)  # Avoid log(0)

        # Compute BCE term
        bce_loss = -(targets * torch.log(probs) + (1 - targets) * torch.log(1 - probs))

        # Compute modulating factor
        p_t = targets * probs + (1 - targets) * (1 - probs)
        modulating_factor = (1.0 - p_t) ** self.gamma

        # Compute alpha weight
        alpha_weight = targets * self.alpha + (1 - targets) * (1 - self.alpha)

        # Compute focal loss
        focal_loss = alpha_weight * modulating_factor * bce_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        elif self.reduction == "none":
            return focal_loss
        else:
            raise ValueError(f"Unsupported reduction: {self.reduction}")


def get_loss_function(loss_name: str, **kwargs) -> nn.Module:
    """
    Factory function to get a loss function by name.

    Args:
        loss_name: Name of the loss ('dice', 'bce', 'bcedice', 'focal')
        **kwargs: Additional arguments for the loss constructor

    Returns:
        An instance of a loss function
    """
    loss_name = loss_name.lower()
    if loss_name == "dice":
        return DiceLoss(**kwargs)
    elif loss_name == "bce":
        return nn.BCEWithLogitsLoss(**kwargs)
    elif loss_name == "bcedice":
        return BCEDiceLoss(**kwargs)
    elif loss_name == "focal":
        return FocalLoss(**kwargs)
    else:
        raise ValueError(
            f"Unsupported loss function: {loss_name}. "
            f"Choose from 'dice', 'bce', 'bcedice', 'focal'."
        )


# Example usage (for debugging)
if __name__ == "__main__":
    import torch

    # Dummy logits and targets
    logits = torch.randn(2, 1, 128, 128, requires_grad=True)
    targets = torch.randint(0, 2, (2, 1, 128, 128)).float()

    # Test Dice loss
    dice_loss = DiceLoss()
    loss_dice = dice_loss(logits, targets)
    print(f"Dice loss: {loss_dice.item():.4f}")

    # Test BCE loss
    bce_loss = nn.BCEWithLogitsLoss()
    loss_bce = bce_loss(logits, targets)
    print(f"BCE loss: {loss_bce.item():.4f}")

    # Test combined loss
    bce_dice_loss = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
    loss_bd = bce_dice_loss(logits, targets)
    print(f"BCE-Dice loss: {loss_bd.item():.4f}")

    # Test Focal loss
    focal_loss = FocalLoss()
    loss_focal = focal_loss(logits, targets)
    print(f"Focal loss: {loss_focal.item():.4f}")

    # Test backward pass
    loss_dice.backward()
    print(f"Logits grad norm: {logits.grad.norm().item():.4f}")