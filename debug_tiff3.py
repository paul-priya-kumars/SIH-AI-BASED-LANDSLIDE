import numpy as np
import tifffile
import rasterio
from pathlib import Path

print("=== Understanding the correct way to save/load multi-band TIFFs ===")

# Create test data in CHW format (what our loader expects)
chwan_image = np.random.rand(14, 128, 128).astype(np.float32)
print(f"Our expected format (CHW): {chwan_image.shape}")

test_dir = Path("test_tiffs_correct")
test_dir.mkdir(exist_ok=True)

# Approach 1: Save as CHW with tifffile, load with rasterio
print("\n--- Approach 1: CHW format with tifffile -> rasterio ---")
test_path1 = test_dir / "chwan_tifffile.tif"
tifffile.imwrite(test_path1, chwan_image)
with rasterio.open(test_path1) as src:
    print(f"Saved with tifffile (CHW): Count={src.count}, Shape={src.read().shape}")
    print(f"  Width: {src.width}, Height: {src.height}")

# Approach 2: What if we transpose to HWC before saving?
print("\n--- Approach 2: HWC format with tifffile -> rasterio ---")
chwan_image_hwc = np.transpose(chwan_image, (1, 2, 0))  # HWC
print(f"HWC format: {chwan_image_hwc.shape}")
test_path2 = test_dir / "chwan_hwc_tifffile.tif"
tifffile.imwrite(test_path2, chwan_image_hwc)
with rasterio.open(test_path2) as src:
    print(f"Saved as HWC with tifffile: Count={src.count}, Shape={src.read().shape}")
    print(f"  Width: {src.width}, Height: {src.height}")

# Approach 3: Let's see what happens if we save with rasterio directly
print("\n--- Approach 3: Save with rasterio directly ---")
test_path3 = test_dir / "chwan_rasterio.tif"
with rasterio.open(
    test_path3,
    'w',
    driver='GTiff',
    width=chwan_image.shape[2],
    height=chwan_image.shape[1],
    count=chwan_image.shape[0],
    dtype=chwan_image.dtype
) as dst:
    dst.write(chwan_image)

# Now read it back
with rasterio.open(test_path3) as src:
    print(f"Saved with rasterio: Count={src.count}, Shape={src.read().shape}")
    print(f"  Width: {src.width}, Height: {src.height}")

# Approach 4: Save with tifffile but specify it's multi-band correctly
print("\n--- Approach 4: Try tifffile with photometric options for multi-band ---")
# Based on research, for multi-spectral data we might need to avoid RGB-specific options
test_path4 = test_dir / "chwan_no_photometric.tif"
tifffile.imwrite(test_path4, chwan_image)  # No special options
with rasterio.open(test_path4) as src:
    print(f"Saved with tifffile (no options): Count={src.count}, Shape={src.read().shape}")

# Let's also check what tifffile actually saves by reading it back with tifffile
print("\n--- Verifying what tifffile actually saved ---")
with rasterio.open(test_path1) as src:
    data_rasterio = src.read()
    print(f"Rasterio read shape: {data_rasterio.shape}")

data_tifffile = tifffile.imread(test_path1)
print(f"Tifffile read shape: {data_tifffile.shape}")
print(f"Arrays equal: {np.allclose(data_rasterio, data_tifffile)}")

# Clean up
import shutil
shutil.rmtree(test_dir)