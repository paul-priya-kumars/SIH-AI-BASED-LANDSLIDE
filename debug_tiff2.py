import numpy as np
import tifffile
import rasterio
from pathlib import Path

# Create a test image with known dimensions (uint8 format)
print("Creating test image...")
# CHW format: (channels, height, width)
image_chw = (np.random.rand(3, 128, 128) * 255).astype(np.uint8)  # Start with 3 channels (RGB) to test
print(f"Original image shape (CHW): {image_chw.shape}")

# Save as TIFF with different parameters and see what works
test_dir = Path("test_tiffs")
test_dir.mkdir(exist_ok=True)

# Approach 1: Basic save
print("\n--- Approach 1: Basic save ---")
test_path1 = test_dir / "basic.tif"
tifffile.imwrite(test_path1, image_chw)
with rasterio.open(test_path1) as src:
    print(f"Basic - Count: {src.count}, Shape: {src.read().shape}")

# Approach 2: Specify photometric='rgb' (for 3 channels)
print("\n--- Approach 2: Photometric=rgb ---")
test_path2 = test_dir / "photometric_rgb.tif"
tifffile.imwrite(test_path2, image_chw, photometric='rgb')
with rasterio.open(test_path2) as src:
    print(f"Photometric=rgb - Count: {src.count}, Shape: {src.read().shape}")

# Approach 3: Try with planarconfig='separate'
print("\n--- Approach 3: PlanarConfig=separate ---")
test_path3 = test_dir / "planar_separate.tif"
tifffile.imwrite(test_path3, image_chw, planarconfig='separate')
with rasterio.open(test_path3) as src:
    print(f"PlanarConfig=separate - Count: {src.count}, Shape: {src.read().shape}")

# Approach 4: Try with photometric='minisblack' (for grayscale/multi-band)
print("\n--- Approach 4: Photometric=minisblack ---")
test_path4 = test_dir / "photometric_minisblack.tif"
tifffile.imwrite(test_path4, image_chw, photometric='minisblack')
with rasterio.open(test_path4) as src:
    print(f"Photometric=minisblack - Count: {src.count}, Shape: {src.read().shape}")

# Approach 5: Try with description or other metadata
print("\n--- Approach 5: With description ---")
test_path5 = test_dir / "with_description.tif"
tifffile.imwrite(test_path5, image_chw, description="Multi-band image")
with rasterio.open(test_path5) as src:
    print(f"With description - Count: {src.count}, Shape: {src.read().shape}")

# Now test with actual 14-channel data
print("\n\n=== Testing with 14-channel data ===")
image_14ch = (np.random.rand(14, 128, 128) * 255).astype(np.uint8)
print(f"14-channel image shape (CHW): {image_14ch.shape}")

# Approach 1: Basic save
print("\n--- 14-channel: Basic save ---")
test_path6 = test_dir / "14ch_basic.tif"
tifffile.imwrite(test_path6, image_14ch)
with rasterio.open(test_path6) as src:
    print(f"14ch Basic - Count: {src.count}, Shape: {src.read().shape}")

# Approach 2: Try with photometric='minisblack'
print("\n--- 14-channel: Photometric=minisblack ---")
test_path7 = test_dir / "14ch_minisblack.tif"
tifffile.imwrite(test_path7, image_14ch, photometric='minisblack')
with rasterio.open(test_path7) as src:
    print(f"14ch MinisBlack - Count: {src.count}, Shape: {src.read().shape}")

# Approach 3: Try to save as HWC and see
print("\n--- 14-channel: HWC format ---")
image_14ch_hwc = np.transpose(image_14ch, (1, 2, 0))  # HWC format
print(f"14-channel image shape (HWC): {image_14ch_hwc.shape}")
test_path8 = test_dir / "14ch_hwc.tif"
tifffile.imwrite(test_path8, image_14ch_hwc)
with rasterio.open(test_path8) as src:
    print(f"14ch HWC - Count: {src.count}, Shape: {src.read().shape}")

# Clean up
import shutil
shutil.rmtree(test_dir)