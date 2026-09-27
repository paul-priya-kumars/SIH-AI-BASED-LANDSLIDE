import numpy as np
import tifffile
import rasterio
from pathlib import Path

print("=== Testing 14-channel data with correct tifffile parameters ===")

# Create 14-channel test data
test_image = np.random.rand(14, 128, 128).astype(np.float32)
print(f"Test image shape: {test_image.shape}")

test_dir = Path("ch14_test")
test_dir.mkdir(exist_ok=True)

# Test the key findings from our 4-channel experiment:
# For multi-channel data that works with both tifffile and rasterio:
# - No special options OR
# - planarconfig='separate' OR
# - photometric='minisblack' + planarconfig='separate'

test_configs = [
    ("No options", {}),
    ("PlanarConfig=separate", {"planarconfig": "separate"}),
    ("Photometric=minisblack", {"photometric": "minisblack"}),
    ("Both minisblack + separate", {"photometric": "minisblack", "planarconfig": "separate"}),
]

for i, (name, options) in enumerate(test_configs):
    print(f"\n--- {name}: {options} ---")
    test_path = test_dir / f"test_{i}.tif"
    tifffile.imwrite(test_path, test_image, **options)

    # Check with tifffile
    data_tifffile = tifffile.imread(test_path)
    print(f"  Tifffile reads: {data_tifffile.shape}")

    # Check with rasterio
    with rasterio.open(test_path) as src:
        data_rasterio = src.read()
        print(f"  Rasterio reads: {data_rasterio.shape} (count={src.count})")

    # Check if they match
    shape_match = data_tifffile.shape == data_rasterio.shape
    data_match = np.allclose(data_tifffile, data_rasterio) if shape_match else False
    print(f"  Shape match: {shape_match}")
    if shape_match:
        print(f"  Data match: {data_match}")

# Also test what happens if we explicitly set the tags that rasterio uses
print(f"\n=== Testing explicit tag setting to match rasterio ===")
# From our earlier analysis, rasterio sets:
# - PhotometricInterpretation: 1 (MinIsBlack)
# - SamplesPerPixel: 14 (for our 14-channel data)
# - PlanarConfiguration: 1 (Chunky)

test_path_explicit = test_dir / "explicit_tags.tif"
tifffile.imwrite(
    test_path_explicit,
    test_image,
    photometric='minisblack',      # This corresponds to PhotometricInterpretation=1
    planarconfig='contig'          # This corresponds to PlanarConfiguration=1 (Chunky)
    # Note: SamplesPerPixel is derived from the shape, we can't set it directly
)

print(f"Explicit tags test:")
# Check with tifffile
data_tifffile = tifffile.imread(test_path_explicit)
print(f"  Tifffile reads: {data_tifffile.shape}")

# Check with rasterio
with rasterio.open(test_path_explicit) as src:
    data_rasterio = src.read()
    print(f"  Rasterio reads: {data_rasterio.shape} (count={src.count})")

shape_match = data_tifffile.shape == data_rasterio.shape
data_match = np.allclose(data_tifffile, data_rasterio) if shape_match else False
print(f"  Shape match: {shape_match}")
if shape_match:
    print(f"  Data match: {data_match}")

# Let's also check the actual tags written
print(f"\nChecking TIFF tags of explicit file:")
try:
    with tifffile.TiffFile(test_path_explicit) as tif:
        if len(tif.pages) > 0:
            page = tif.pages[0]
            print(f"  Page shape: {page.shape}")
            for tag in page.tags.values():
                if tag.name in ['PhotometricInterpretation', 'SamplesPerPixel', 'PlanarConfiguration']:
                    print(f"  Tag {tag.name}: {tag.value}")
except Exception as e:
    print(f"  Error reading tags: {e}")

# Clean up
import shutil
shutil.rmtree(test_dir)