import rasterio
import numpy as np
from rasterio.transform import from_origin

# Create a simple 3x3 NDVI array
ndvi_array = np.array([[-0.1, 0.0, 0.2],
                       [0.3, 0.5, 0.4],
                       [0.2, 0.1, 0.3]], dtype=np.float32)

# Define the geotransform: origin at upper left, pixel size 0.005 degrees (~550m at equator)
# We'll place it near Kathmandu: longitude 85.3, latitude 27.7
transform = from_origin(85.3, 27.7, 0.005, 0.005)  # x_size, y_size (negative y_size for north-up)

# Write the GeoTIFF
with rasterio.open(
    'ndvi_demo.tif',
    'w',
    driver='GTiff',
    height=ndvi_array.shape[0],
    width=ndvi_array.shape[1],
    count=1,
    dtype=ndvi_array.dtype,
    crs='EPSG:4326',
    transform=transform,
    nodata=-9999.0
) as dst:
    dst.write(ndvi_array, 1)

print("Created ndvi_demo.tif")