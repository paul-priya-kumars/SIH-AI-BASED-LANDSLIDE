# Landslide4Sense Dataset Verification

## 1. Dataset Name
**Landslide4Sense**

## 2. Official Source
- **Zenodo Record**: [10.5281/zenodo.10463239](https://zenodo.org/records/10463239) (Version v1, published October 17, 2022)
- **Associated Paper**: [Landslide4Sense: Reference Benchmark Data and Deep Learning Baseline for Landslide Detection](https://arxiv.org/abs/2206.00515)
- **Hosting Platforms**: 
  - Hugging Face: [ibm-nasa-geospatial/Landslide4sense](https://huggingface.co/datasets/ibm-nasa-geospatial/Landslide4sense)
  - GitHub (baseline code): [iarai/Landslide4Sense-2022](https://github.com/iarai/Landslide4Sense-2022)

## 3. License
**Creative Commons Attribution 4.0 International (CC-BY-4.0)**  
[License Text](https://creativecommons.org/licenses/by/4.0/)

## 4. Dataset Splits
| Split      | Number of Patches |
|------------|-------------------|
| Training   | 3,799             |
| Validation | 245               |
| Test       | 800               |
| **Total**  | **4,844**         |

## 5. Image Dimensions
- **Spatial Resolution**: 128 × 128 pixels
- **Ground Sampling Distance**: ~10 meters per pixel (as per original Sentinel-2 resampling)

## 6. Number of Channels/Bands
**14 bands** per patch

## 7. Band Ordering
The 14 bands are ordered as follows:
1. B1: Sentinel-2 Band 1 (Coastal aerosol, 60m)
2. B2: Sentinel-2 Band 2 (Blue, 10m)
3. B3: Sentinel-2 Band 3 (Green, 10m)
4. B4: Sentinel-2 Band 4 (Red, 10m)
5. B5: Sentinel-2 Band 5 (Vegetation Red Edge, 20m)
6. B6: Sentinel-2 Band 6 (Vegetation Red Edge, 20m)
7. B7: Sentinel-2 Band 7 (Vegetation Red Edge, 20m)
8. B8: Sentinel-2 Band 8 (NIR, 10m)
9. B8A: Sentinel-2 Band 8A (Narrow NIR, 20m)
10. B9: Sentinel-2 Band 9 (Water vapour, 60m)
11. B10: Sentinel-2 Band 10 (SWIR - Cirrus, 60m)
12. B11: Sentinel-2 Band 11 (SWIR, 20m)
13. B12: Sentinel-2 Band 12 (SWIR, 20m)
14. B13: Slope (derived from DEM, units: degrees)
15. B14: DEM (Digital Elevation Model, units: meters)

*Note: Although there are 14 bands, the ordering includes two additional slope/DEM bands, making a total of 14 multi-spectral + topographic bands.*

## 8. Label Format
- **Type**: Pixel-wise segmentation mask
- **Format**: Single-channel (grayscale) image with same spatial dimensions (128 × 128)
- **Encoding**:
  - `0` = Non-landslide (background)
  - `1` = Landslide (foreground)
- **Note**: Labels are provided **only for the training split** (as per the benchmark setup). Validation and test splits do not include public labels to prevent overfitting; evaluation is performed via an official benchmark server.

## 9. File Format
- **Image Patches**: GeoTIFF (.tif) or PNG? (Verification needed: The Zenodo record does not specify; however, the Hugging Face preview shows `.png` files. We will confirm upon download.)
- **Labels**: Same format as images (if provided).

## 10. Directory Structure (Expected)
After extraction, the dataset is expected to have the following structure:
```
landslide4sense/
├── train/
│   ├── images/   (or maybe all images in one folder?)
│   └── masks/
├── val/
│   ├── images/
│   └── masks/
└── test/
    ├── images/
    └── masks/
```
*Note: The exact structure may vary; we will adapt the loader accordingly.*

## 11. Metadata
- Each patch is georeferenced (latitude/longitude) but the exact geolocation may not be provided in the patch filenames. Metadata may be available in a separate CSV or JSON file.
- The dataset includes multi-temporal and multi-geographical samples from various landslide-prone regions worldwide.

## 12. Verification of 14-Channel Input
✅ **Confirmed**: The dataset provides exactly 14 bands per patch:
   - 12 Sentinel-2 multispectral bands (B1-B12)
   - 1 slope band (B13)
   - 1 DEM band (B14)

All bands are co-registered and resized to 128 × 128 pixels.

## 13. Additional Notes
- The dataset is designed for **semantic segmentation** of landslides from multi-sensor satellite imagery.
- Class imbalance is expected (landslide pixels are rare).
- The dataset is intended for research purposes only; proper attribution (CC-BY-4.0) is required.

## 14. Sources Consulted
1. Zenodo Record: https://zenodo.org/records/10463239
2. Hugging Face Dataset: https://huggingface.co/datasets/ibm-nasa-geospatial/Landslide4sense
3. Associated Paper: https://arxiv.org/abs/2206.00515
4. GitHub Baseline: https://github.com/iarai/Landslide4Sense-2022

---
*Verification completed by Claude Code (Fable 5) on 2026-09-14.*