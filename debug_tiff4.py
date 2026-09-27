import numpy as np
import tifffile
import rasterio
from pathlib import Path

print("=== Investigating TIFF tag differences ===")

# Create test data
test_image = np.random.rand(4, 64, 64).astype(np.float32)  # Smaller for easier inspection
print(f"Test image shape: {test_image.shape}")

test_dir = Path("tag_test")
test_dir.mkdir(exist_ok=True)

# Save with tifffile using various options
save_options = [
    {},
    {"photometric": "minisblack"},
    {"planarconfig": "separate"},
    {"photometric": "minisblack", "planarconfig": "separate"},
]

for i, options in enumerate(save_options):
    print(f"\n--- Option set {i+1}: {options} ---")
    test_path = test_dir / f"test_{i}.tif"
    tifffile.imwrite(test_path, test_image, **options)

    # Check with tifffile
    data_tifffile = tifffile.imread(test_path)
    print(f"  Tifffile reads: {data_tifffile.shape}")

    # Check with rasterio
    with rasterio.open(test_path) as src:
        data_rasterio = src.read()
        print(f"  Rasterio reads: {data_rasterio.shape} (count={src.count})")

    # Are they the same?
    print(f"  Same shape: {data_tifffile.shape == data_rasterio.shape}")
    if data_tifffile.shape == data_rasterio.shape:
        print(f"  Same data: {np.allclose(data_tifffile, data_rasterio)}")

# Let's also check what happens if we insist on writing with rasterio but then
# see if we can make tifffile match its approach
print("\n\n=== Checking if we can make tifffile write like rasterio ===")

# Save reference file with rasterio
ref_path = test_dir / "reference.tif"
with rasterio.open(
    ref_path,
    'w',
    driver='GTiff',
    width=test_image.shape[2],
    height=test_image.shape[1],
    count=test_image.shape[0],
    dtype=test_image.dtype
) as dst:
    dst.write(test_image)

print(f"Reference file (rasterio-written):")
with rasterio.open(ref_path) as src:
    ref_data = src.read()
    print(f"  Shape: {ref_data.shape}")
    print(f"  Count: {src.count}")

# Now try to mimic this with tifffile by looking at what tags rasterio sets
# Let's check the TIFF tags of the reference file
print(f"\nReference file TIFF info:")
with rasterio.open(ref_path) as src:
    print(f"  Driver: {src.driver}")
    print(f"  Width: {src.width}")
    print(f"  Height: {src.height}")
    print(f"  Count: {src.count}")
    print(f"  Dtypes: {src.dtypes}")
    print(f"  Nodata: {src.nodata}")
    print(f"  Indexes: {src.indexes}")
    print(f"  CRs: {src.crs}")
    print(f"  Transform: {src.transform}")
    print(f"  Bounds: {src.bounds}")

# Check tifffile version
print(f"\nTifffile version info:")
try:
    with tifffile.TiffFile(ref_path) as tif:
        print(f"  Number of pages: {len(tif.pages)}")
        if len(tif.pages) > 0:
            page = tif.pages[0]
            print(f"  Page shape: {page.shape}")
            print(f"  Page dtype: {page.dtype}")
            # Print some tags
            for tag in page.tags.values():
                if tag.name in ['ImageWidth', 'ImageLength', 'PhotometricInterpretation',
                              'SamplesPerPixel', 'PlanarConfiguration', 'BitsPerSample']:
                    print(f"  Tag {tag.name}: {tag.value}")
except Exception as e:
    print(f"  Error reading with tifffile: {e}")

# Clean up
import shutil
shutil.rmtree(test_dir)