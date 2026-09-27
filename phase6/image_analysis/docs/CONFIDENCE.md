# Confidence in Landslide4Sense Segmentation Model

## Overview

This document describes how confidence is handled in the Landslide4Sense segmentation model (U-Net with ResNet34 encoder) for landslide detection.

## Model Output

The model outputs a per-pixel landslide probability map, where each pixel value is in the range [0.0, 1.0], representing the model's estimated probability that the pixel belongs to a landslide.

The output is passed through a sigmoid activation function, ensuring valid probabilities.

## Confidence Measures

### Per-Pixel Confidence
The per-pixel probability itself can be interpreted as a confidence measure:
- A probability close to 1.0 indicates high confidence that the pixel is a landslide.
- A probability close to 0.0 indicates high confidence that the pixel is not a landslide.
- A probability near 0.5 indicates low confidence (the model is uncertain).

However, note that the model is not calibrated; probabilities may not represent true frequencies.

### Image-Level Confidence
For image-level applications (e.g., risk engine integration), we derive an image-level landslide probability as the proportion of pixels above a threshold (see [Risk Engine Integration](#risk-engine-integration) in the README). Confidence in this image-level measure can be assessed in several ways:

1. **Average Probability**: The mean of all pixel probabilities. Higher average probability indicates stronger evidence of landslide presence in the image.
2. **Probability Standard Deviation**: Low standard deviation indicates consensus among pixels (either all high or all low), while high standard deviation indicates mixed predictions.
3. **Entropy**: The entropy of the probability distribution across the image measures uncertainty. Lower entropy indicates higher confidence.
4. **Maximum Probability**: The highest probability value in the image indicates the model's strongest belief in any pixel being a landslide.

### Threshold-Based Confidence
When using a threshold to binarize predictions (e.g., for computing image-level probability), confidence can be related to how far the probabilities are from the threshold:
- Pixels with probabilities far from the threshold (close to 0 or 1) contribute to confident predictions.
- Pixels with probabilities near the threshold contribute to uncertainty.

## Recommendations

### Do Not Fabricate Confidence
We do not claim to have a scientifically validated confidence measure. Instead, we provide the raw probabilities and derived statistics so that users can apply their own confidence assessment based on their application's needs.

### Use with Caution
If confidence is required for decision-making, consider:
- Using an ensemble of models to estimate variance.
- Calibrating the model's probabilities using a validation set (e.g., with Platt scaling or isotonic regression).
- Applying post-processing techniques such as conditional random fields (CRFs) to refine predictions and estimate uncertainty.

## Implementation

In the provided evaluation script (`phase6/image_analysis/training/evaluate.py`), we compute per-pixel probabilities and provide the raw outputs. Users can compute any of the above confidence measures from the probability matrix.

Example (pseudo-code):
```python
probabilities = model_output  # Shape: (N, H, W)
# Per-pixel confidence: probabilities themselves
# Image-level average confidence: np.mean(probabilities)
# Image-level standard deviation: np.std(probabilities)
# Image-level entropy: -np.mean(probabilities * np.log(probabilities + 1e-8) + (1 - probabilities) * np.log(1 - probabilities + 1e-8))
# Maximum probability: np.max(probabilities)
```

## References

- [On Calibration of Modern Neural Networks](https://arxiv.org/abs/1706.04599) (Guo et al., 2015)
- [A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks](https://arxiv.org/abs/1807.03888) (Lee et al., 2018)

---
*Document created by Claude Code (Fable 5) for the SIH AI-Based Landslide Early Warning System (GeoShield AI).*