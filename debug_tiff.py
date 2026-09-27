import numpy as np
import tifffile
import rasterio
from pathlib import Path

# Create a test image with known dimensions
print("Creating test image...")
# CHW format: (channels, height, width)
image_chw = np.random.rand(14, 128, 128).astype(np.float32)
print(f"Original image shape (CHW): {image_chw.shape}")

# Save as TIFF
test_path = Path("test_image.tif")
tifffile.imwrite(test_path, image_chw)
print(f"Saved image to {test_path}")

# Load with tifffile to verify what we saved
loaded_with_tifffile = tifffile.imread(test_path)
print(f"Loaded with tifffile shape: {loaded_with_tifffile.shape}")
print(f"Loaded with tifffile dtype: {loaded_with_tifffile.dtype}")

# Load with rasterio to see what the dataset loader sees
try:
    with rasterio.open(test_path) as src:
        print(f"Rasterio driver: {src.driver}")
        print(f"Rasterio width: {src.width}")
        print(f"Rasterio height: {src.height}")
        print(f"Rasterio count: {src.count}")  # This is the number of bands/channels
        print(f"Rasterio dtypes: {src.dtypes}")

        # Read all bands
        image_rasterio = src.read()  # Should be (count, height, width)
        print(f"Loaded with rasterio shape: {image_rasterio.shape}")
        print(f"Loaded with rasterio dtype: {image_rasterio.dtype}")
except Exception as e:
    print(f"Error loading with rasterio: {e}")

# Try saving in HWC format
print("\n--- Testing HWC format ---")
image_hwc = np.transpose(image_chw, (1, 2, 0))  # Convert to HWC: (height, width, channels)
print(f"HWC image shape: {image_hwc.shape}")

test_path_hwc = Path("test_image_hwc.tif")
tifffile.imwrite(test_path_hwc, image_hwc)
print(f"Saved HWC image to {test_path_hwc}")

# Load with rasterio
try:
    with rasterio.open(test_path_hwc) as src:
        print(f"Rasterio driver: {src.driver}")
        print(f"Rasterio width: {src.width}")
        print(f"Rasterio height: {src.height}")
        print(f"Rasterio count: {src.count}")  # This is the number of bands/channels

        # Read all bands
        image_rasterio_hwc = src.read()  # Should be (count, height, width)
        print(f"Loaded with rasterio shape: {image_rasterio_hwc.shape}")
        print(f"Loaded with rasterio dtype: {image_rasterio_hwc.dtype}")
except Exception as e:
    print(f"Error loading HWC with rasterio: {e}")

# Try saving as uint8
print("\n--- Testing uint8 format ---")
image_uint8 = (image_chw * 255).astype(np.uint8)
print(f"Uint8 image shape: {image_uint8.shape}")

test_path_uint8 = Path("test_image_uint8.tif")
tifffile.imwrite(test_path_uint8, image_uint8)
print(f"Saved uint8 image to {test_path_uint8}")

# Load with rasterio
try:
    with rasterio.open(test_path_uint8) as src:
        print(f"Rasterio driver: {src.driver}")
        print(f"Rasterio width: {src.width}")
        print(f"Rasterio height: {src.height}")
        print(f"Rasterio count: {src.count}")  # This is the number of bands/channels

        # Read all bands
        image_rasterio_uint8 = src.read()  # Should be (count, height, width)
        print(f"Loaded with rasterio shape: {image_rasterio_uint8.shape}")
        print(f"Loaded with rasterio dtype: {image_rasterio_uint8.dtype}")
except Exception as e:
    print(f"Error loading uint8 with rasterio: {e}")

# Clean up
test_path.unlink(missing_ok=True)
test_path_hwc.unlink(missing_ok=True)
test_path_uint8.unlink(missing_ok=True)