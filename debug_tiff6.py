import numpy as np
import tifffile
import rasterio
from pathlib import Path

print("=== Final verification: PlanarConfiguration explanation ===")

# Create test data
test_image = np.random.rand(3, 64, 64).astype(np.float32)  # 3-channel for easy visualization
print(f"Test image shape (CHW): {test_image.shape}")

test_dir = Path("final_test")
test_dir.mkdir(exist_ok=True)

# Test PlanarConfiguration values
configs = [
    ("CHUNKY (1)", 1),    # All samples for pixel together -> HWC interpretation by some readers?
    ("SEPARATE (2)", 2),  # Separate planes -> CHW format
]

for name, config_value in configs:
    print(f"\n--- PlanarConfiguration = {config_value} ({name}) ---")
    test_path = test_dir / f"pc{config_value}.tif"

    # Save with explicit PlanarConfiguration
    tifffile.imwrite(test_path, test_image, planarconfig=config_value)

    # Check with tifffile
    data_tifffile = tifffile.imread(test_path)
    print(f"  Tifffile reads: {data_tifffile.shape}")

    # Check with rasterio
    with rasterio.open(test_path) as src:
        data_rasterio = src.read()
        print(f"  Rasterio reads: {data_rasterio.shape} (count={src.count})")

    match = data_tifffile.shape == data_rasterio.shape
    print(f"  Shapes match: {match}")

# Now test with our actual 14-channel data
print(f"\n\n=== Testing 14-channel data ===")
image_14ch = np.random.rand(14, 128, 128).astype(np.float32)
print(f"14-channel image shape (CHW): {image_14ch.shape}")

# The correct approach based on our findings:
test_path_14ch = test_dir / "14ch_correct.tif"
tifffile.imwrite(test_path_14ch, image_14ch, planarconfig='separate')

# Verify
data_tifffile = tifffile.imread(test_path_14ch)
print(f"Tifffile reads: {data_tifffile.shape}")

with rasterio.open(test_path_14ch) as src:
    data_rasterio = src.read()
    print(f"Rasterio reads: {data_rasterio.shape} (count={src.count})")

print(f"Perfect match: {data_tifffile.shape == data_rasterio.shape and np.allclose(data_tifffile, data_rasterio)}")

# Clean up
import shutil
shutil.rmtree(test_dir)