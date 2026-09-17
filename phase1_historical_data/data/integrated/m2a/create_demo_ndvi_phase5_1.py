import rasterio
import numpy as np
from rasterio.transform import from_origin

# Calculate historical points extent with buffer
# Based on analysis of historical_landslides.geojson
min_lon = 77.0322  # 78.0322 - 1.0 buffer
max_lon = 89.3639  # 88.3639 + 1.0 buffer
min_lat = 21.5726  # 22.5726 - 1.0 buffer
max_lat = 31.3165  # 30.3165 + 1.0 buffer

# Create a reasonable sized raster (e.g., 50x50 pixels)
width, height = 50, 50
pixel_size = (max_lon - min_lon) / width  # This will make pixels cover the extent exactly

# Create a simple NDVI array with values in realistic range [-1, 1]
# Using a gradient pattern for deterministic synthetic values
ndvi_array = np.zeros((height, width), dtype=np.float32)
for i in range(height):
    for j in range(width):
        # Create a pattern that varies across the raster
        ndvi_array[i, j] = -0.5 + (i * j * 0.01) % 1.5  # Values roughly between -0.5 and 1.0
        # Keep within valid NDVI range
        ndvi_array[i, j] = max(-1.0, min(1.0, ndvi_array[i, j]))

# Define the geotransform: origin at upper left
transform = from_origin(min_lon, max_lat, pixel_size, pixel_size)  # x_size, y_size

# Write the GeoTIFF
with rasterio.open(
    'ndvi_demo_phase5_1.tif',
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=ndvi_array.dtype,
    crs='EPSG:4326',
    transform=transform,
    nodata=-9999.0
) as dst:
    dst.write(ndvi_array, 1)

# Create metadata
metadata = {
    "dataset_id": "M2A_NDVI_DEMO_PHASE5_1",
    "module": "M2-A",
    "purpose": "Normalized Difference Vegetation Index (NDVI) - Synthetic Demo Data for Phase 5.1",
    "description": "A 50x50 pixel NDVI GeoTIFF covering the extent of historical landslide demo points. Values are synthetic gradients for testing extraction. NOT REAL DATA.",
    "source": "Synthetic data generated for testing",
    "date_generated": "2026-09-16",
    "crs": "EPSG:4326",
    "integration_crs": "EPSG:4326",
    "raster_info": {
        "width": width,
        "height": height,
        "pixel_size_x": pixel_size,
        "pixel_size_y": pixel_size,
        "bands": 1,
        "nodata": -9999.0,
        "data_type": "float32",
        "value_range": {
            "min": float(np.min(ndvi_array)),
            "max": float(np.max(ndvi_array)),
            "mean": float(np.mean(ndvi_array))
        }
    },
    "spatial_extent": {
        "min_longitude": min_lon,
        "max_longitude": max_lon,
        "min_latitude": min_lat,
        "max_latitude": max_lat
    },
    "status": "SYNTHETIC_DEMO_DATA",
    "warning": "THIS IS SYNTHETIC DEMO DATA AND MUST NOT BE USED AS REAL OBSERVATIONS."
}

import json
with open('ndvi_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("Created ndvi_demo_phase5_1.tif and ndvi_metadata.json")