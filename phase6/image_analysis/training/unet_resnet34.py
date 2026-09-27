"""
U-Net with ResNet34 encoder for Landslide4Sense segmentation.

Adapted to accept 14-channel input (Sentinel-2 bands + slope + DEM).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.models import resnet34
from typing import Tuple


class UNetResNet34Encoder(nn.Module):
    """
    ResNet34 encoder adapted for U-Net.
    Outputs feature maps at different scales for skip connections.
    """

    def __init__(self, in_channels: int = 14, pretrained: bool = False):
        """
        Args:
            in_channels: Number of input channels (default: 14 for Landslide4Sense)
            pretrained: Whether to use ImageNet pretrained weights (not recommended for 14 channels)
        """
        super(UNetResNet34Encoder, self).__init__()

        # Load pretrained ResNet34
        self.resnet = resnet34(pretrained=pretrained)
        # Modify the first convolutional layer to accept in_channels
        if in_channels != 3:
            # Create a new conv layer with the desired in_channels
            # We keep the same kernel size, stride, padding, and bias
            old_conv = self.resnet.conv1
            new_conv = nn.Conv2d(
                in_channels,
                old_conv.out_channels,
                kernel_size=old_conv.kernel_size,
                stride=old_conv.stride,
                padding=old_conv.padding,
                bias=old_conv.bias is not None,
            )
            # If we are not using pretrained, we can initialize randomly (default)
            # If we want to pretrain, we could average the RGB weights for extra channels, but we skip.
            self.resnet.conv1 = new_conv

        # We'll use the following layers as encoders
        self.conv1 = self.resnet.conv1
        self.bn1 = self.resnet.bn1
        self.relu = self.resnet.relu
        self.maxpool = self.resnet.maxpool

        self.layer1 = self.resnet.layer1  # 64 channels
        self.layer2 = self.resnet.layer2  # 128 channels
        self.layer3 = self.resnet.layer3  # 256 channels
        self.layer4 = self.resnet.layer4  # 512 channels

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Returns:
            Tuple of feature maps at different scales:
            - f1: after conv1 (64 channels, 1/2 resolution)
            - f2: after layer1 (64 channels, 1/4 resolution)
            - f3: after layer2 (128 channels, 1/8 resolution)
            - f4: after layer3 (256 channels, 1/16 resolution)
            - f5: after layer4 (512 channels, 1/32 resolution)
        """
        x = self.conv1(x)      # (64, H/2, W/2)
        x = self.bn1(x)
        x = self.relu(x)
        f1 = x                 # 64 channels
        x = self.maxpool(x)    # (64, H/4, W/4)

        x = self.layer1(x)     # (64, H/4, W/4)
        f2 = x                 # 64 channels
        x = self.layer2(x)     # (128, H/8, W/8)
        f3 = x                 # 128 channels
        x = self.layer3(x)     # (256, H/16, W/16)
        f4 = x                 # 256 channels
        x = self.layer4(x)     # (512, H/32, W/32)
        f5 = x                 # 512 channels

        return f1, f2, f3, f4, f5


class UNetDecoder(nn.Module):
    """
    U-Net decoder with skip connections.
    """

    def __init__(self, num_classes: int = 1):
        """
        Args:
            num_classes: Number of output classes (1 for binary segmentation)
        """
        super(UNetDecoder, self).__init__()

        # Define upsampling layers
        self.upconv4 = nn.ConvTranspose2d(512, 256, kernel_size=2, stride=2)
        self.upconv3 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.upconv2 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.upconv1 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)

        # Define convolution blocks after concatenation
        self.conv4 = self._conv_block(512, 256)  # 256 + 256 from encoder
        self.conv3 = self._conv_block(256, 128)  # 128 + 128
        self.conv2 = self._conv_block(128, 64)   # 64 + 64
        self.conv1 = self._conv_block(96, 32)    # 32 + 64

        # Final output layer
        self.output_conv = nn.Conv2d(32, num_classes, kernel_size=1)

    def _conv_block(self, in_channels: int, out_channels: int) -> nn.Sequential:
        """Helper to create a double convolution block."""
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(
        self,
        f1: torch.Tensor,
        f2: torch.Tensor,
        f3: torch.Tensor,
        f4: torch.Tensor,
        f5: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            f1, f2, f3, f4, f5: Feature maps from encoder

        Returns:
            Output logits of shape (N, num_classes, H, W)
        """
        # Upsample f5 and concatenate with f4
        x = self.upconv4(f5)                   # (256, H/16, W/16)
        x = torch.cat([x, f4], dim=1)          # (256+256=512, H/16, W/16)
        x = self.conv4(x)                      # (256, H/16, W/16)

        # Upsample and concatenate with f3
        x = self.upconv3(x)                    # (128, H/8, W/8)
        x = torch.cat([x, f3], dim=1)          # (128+128=256, H/8, W/8)
        x = self.conv3(x)                      # (128, H/8, W/8)

        # Upsample and concatenate with f2
        x = self.upconv2(x)                    # (64, H/4, W/4)
        x = torch.cat([x, f2], dim=1)          # (64+64=128, H/4, W/4)
        x = self.conv2(x)                      # (64, H/4, W/4)

        # Upsample and concatenate with f1
        x = self.upconv1(x)                    # (32, H/2, W/2)
        x = torch.cat([x, f1], dim=1)          # (32+32=64, H/2, W/2)
        x = self.conv1(x)                      # (32, H/2, W/2)

        # Upsample to original resolution
        x = F.interpolate(x, scale_factor=2, mode='bilinear', align_corners=False)  # (32, H, W)
        logits = self.output_conv(x)           # (num_classes, H, W)

        return logits


class UNetResNet34(nn.Module):
    """
    U-Net with ResNet34 encoder for binary segmentation.
    """

    def __init__(self, in_channels: int = 14, num_classes: int = 1, pretrained: bool = False):
        """
        Args:
            in_channels: Number of input channels (default: 14)
            num_classes: Number of output classes (1 for binary segmentation)
            pretrained: Whether to use ImageNet pretrained weights for encoder (not recommended for 14 channels)
        """
        super(UNetResNet34, self).__init__()
        self.encoder = UNetResNet34Encoder(in_channels=in_channels, pretrained=pretrained)
        self.decoder = UNetDecoder(num_classes=num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (N, C, H, W)

        Returns:
            Output logits of shape (N, num_classes, H, W)
        """
        f1, f2, f3, f4, f5 = self.encoder(x)
        logits = self.decoder(f1, f2, f3, f4, f5)
        return logits


# Example usage (for debugging)
if __name__ == "__main__":
    import torch

    # Dummy input: batch size 2, 14 channels, 128x128
    x = torch.randn(2, 14, 128, 128)
    model = UNetResNet34(in_channels=14, num_classes=1, pretrained=False)
    print(model)

    # Forward pass
    with torch.no_grad():
        logits = model(x)
    print(f"Input shape: {x.shape}")
    print(f"Output logits shape: {logits.shape}")
    print(f"Output range: {logits.min().item():.3f} to {logits.max().item():.3f}")

    # Apply sigmoid to get probabilities
    probs = torch.sigmoid(logits)
    print(f"Probabilities shape: {probs.shape}")
    print(f"Probabilities range: {probs.min().item():.3f} to {probs.max().item():.3f}")