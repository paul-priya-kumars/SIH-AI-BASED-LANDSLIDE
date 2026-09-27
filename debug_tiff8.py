import numpy as np
import tifffile
import rasterio
from pathlib import Path

print("=== Testing the correct approach: Save CHW with planarconfig='separate' ===")

# Create test image in CHW format (what the dataset loader ultimately wants from rasterio)
image_chw = np.random.rand(14, 128, 128).astype(np.float32)
print(f"Our image format (CHW): {image_chw.shape}")

test_dir = Path("debug_chw")
test_dir.mkdir(exist_ok=True)

# Save CHW format with planarconfig='separate'
test_path = test_dir / "test_chw_separate.tif"
tifffile.imwrite(test_path, image_chw, planarconfig='separate')
print(f"Saved image to {test_path}")

# Check what tifffile reads
data_tifffile = tifffile.imread(test_path)
print(f"Tifffile reads: {data_tifffile.shape}")

# Check what rasterio reads (this is what the dataset loader does)
with rasterio.open(test_path) as src:
    print(f"Rasterio info:")
    print(f"  Width: {src.width}")
    print(f"  Height: {src.height}")
    print(f"  Count: {src.count}")  # This should be the number of bands/channels

    # This is what _load_image does: src.read()
    data_rasterio = src.read()  # Should be (count, height, width) = (C, H, W)
    print(f"Rasterio reads (src.read()): {data_rasterio.shape}")

    # Check if it has the expected number of channels
    expected_channels = 14
    expected_height = 128
    expected_width = 128

    if (data_rasterio.shape[0] == expected_channels and
        data_rasterio.shape[1] == expected_height and
        data_rasterio.shape[2] == expected_width):
        print(f"CORRECT: Got shape {data_rasterio.shape} as expected (C,H,W)")
    else:
        print(f"ERROR: Expected ({expected_channels},{expected_height},{expected_width}), got {data_rasterio.shape}")

# Let's also verify that tifffile can read its own file correctly
if np.allclose(data_tifffile, data_rasterio):
    print("PERFECT: tifffile and rasterio read identical data")
else:
    print("WARNING: tifffile and rasterio read different data")

# Clean up
import shutil
shutil.rmtree(test_dir)