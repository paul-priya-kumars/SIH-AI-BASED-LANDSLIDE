import numpy as np
import tifffile
import rasterio
from pathlib import Path

print("=== Debugging the exact issue in dataset loader ===")

# Create test image in HWC format (what we're saving in test_pipeline.py)
image_hwc = np.random.rand(128, 128, 14).astype(np.float32)
print(f"Our saved image format (HWC): {image_hwc.shape}")

test_dir = Path("debug_hwc")
test_dir.mkdir(exist_ok=True)

# Save with planarconfig='separate' (our fix)
test_path = test_dir / "test_hwc_separate.tif"
tifffile.imwrite(test_path, image_hwc, planarconfig='separate')
print(f"Saved image to {test_path}")

# Check what tifffile reads
data_tifffile = tifffile.imread(test_path)
print(f"Tifffile reads: {data_tifffile.shape}")

# Check what rasterio reads (this is what the dataset loader does)
with rasterio.open(test_path) as src:
    print(f"Rasterio info:")
    print(f"  Width: {src.width}")
    print(f"  Height: {src.height}")
    print(f"  Count: {src.count}")  # This is the number of bands
    print(f"  Dtypes: {src.dtypes}")

    # This is what _load_image does: src.read()
    data_rasterio = src.read()  # Should be (count, height, width) = (C, H, W)
    print(f"Rasterio reads (src.read()): {data_rasterio.shape}")

    # Check if it has the expected number of channels
    expected_channels = 14
    if data_rasterio.shape[0] == expected_channels:
        print(f"CORRECT: Got {data_rasterio.shape[0]} channels as expected")
    else:
        print(f"ERROR: Expected {expected_channels} channels, got {data_rasterio.shape[0]}")

# Let's also test what happens WITHOUT planarconfig='separate'
print(f"\n--- Testing WITHOUT planarconfig='separate' ---")
test_path2 = test_dir / "test_hwc_default.tif"
tifffile.imwrite(test_path2, image_hwc)  # Default settings

# Check what rasterio reads
with rasterio.open(test_path2) as src:
    print(f"Rasterio info (default):")
    print(f"  Width: {src.width}")
    print(f"  Height: {src.height}")
    print(f"  Count: {src.count}")

    data_rasterio2 = src.read()
    print(f"Rasterio reads (src.read()): {data_rasterio2.shape}")

    if data_rasterio2.shape[0] == expected_channels:
        print(f"CORRECT: Got {data_rasterio2.shape[0]} channels as expected")
    else:
        print(f"ERROR: Expected {expected_channels} channels, got {data_rasterio2.shape[0]}")

# Clean up
import shutil
shutil.rmtree(test_dir)