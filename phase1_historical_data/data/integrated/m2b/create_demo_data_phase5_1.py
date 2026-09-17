import rasterio
import numpy as np
from rasterio.transform import from_origin
import pandas as pd

# Calculate historical points extent with buffer
# Based on analysis of historical_landslides.geojson
min_lon = 77.0322  # 78.0322 - 1.0 buffer
max_lon = 89.3639  # 88.3639 + 1.0 buffer
min_lat = 21.5726  # 22.5726 - 1.0 buffer
max_lat = 31.3165  # 30.3165 + 1.0 buffer

# Create a reasonable sized raster (e.g., 50x50 pixels)
width, height = 50, 50
pixel_size = (max_lon - min_lon) / width  # This will make pixels cover the extent exactly

# Create DEM array (elevation in meters)
# Using a gradient pattern for deterministic synthetic values
dem_array = np.zeros((height, width), dtype=np.float32)
for i in range(height):
    for j in range(width):
        # Elevation pattern: varies from 500m to 4000m
        dem_array[i, j] = 500 + (i * j * 10) % 3500  # Values between 500 and 4000m

# Create slope array (degrees)
# Using a gradient pattern
slope_array = np.zeros((height, width), dtype=np.float32)
for i in range(height):
    for j in range(width):
        # Slope pattern: varies from 0 to 45 degrees
        slope_array[i, j] = (i * j * 0.5) % 45  # Values between 0 and 45 degrees

# Create aspect array (degrees from north)
# Using a gradient pattern
aspect_array = np.zeros((height, width), dtype=np.float32)
for i in range(height):
    for j in range(width):
        # Aspect pattern: varies from 0 to 360 degrees
        aspect_array[i, j] = (i * j * 5) % 360  # Values between 0 and 360 degrees

# Define the geotransform: origin at upper left
transform = from_origin(min_lon, max_lat, pixel_size, pixel_size)  # x_size, y_size

# Write the DEM GeoTIFF
with rasterio.open(
    'dem_demo_phase5_1.tif',
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=dem_array.dtype,
    crs='EPSG:4326',
    transform=transform,
    nodata=-9999.0
) as dst:
    dst.write(dem_array, 1)

# Write the slope GeoTIFF
with rasterio.open(
    'slope_demo_phase5_1.tif',
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=slope_array.dtype,
    crs='EPSG:4326',
    transform=transform,
    nodata=-9999.0
) as dst:
    dst.write(slope_array.astype(np.float32), 1)

# Write the aspect GeoTIFF
with rasterio.open(
    'aspect_demo_phase5_1.tif',
    'w',
    driver='GTiff',
    height=height,
    width=width,
    count=1,
    dtype=aspect_array.dtype,
    crs='EPSG:4326',
    transform=transform,
    nodata=-9999.0
) as dst:
    dst.write(aspect_array.astype(np.float32), 1)

# Create a synthetic rainfall CSV (keeping it non-spatial as before)
rainfall_data = {
    'location_id': ['LOC001', 'LOC002', 'LOC003', 'LOC004', 'LOC005'],
    'date': ['2020-05-15', '2020-05-15', '2020-05-15', '2020-05-15', '2020-05-15'],
    'rainfall_24h': [10.5, 0.0, 25.3, 5.0, 0.0],
    'rainfall_3d': [45.2, 2.1, 80.0, 15.0, 0.0],
    'rainfall_7d': [80.0, 5.0, 120.0, 30.0, 2.0]
}
rainfall_df = pd.DataFrame(rainfall_data)
rainfall_df.to_csv('rainfall_demo.csv', index=False)

# Create metadata for the M2-B datasets
metadata = {
    "dataset_id": "M2B_DEMO_DATA_PHASE5_1",
    "module": "M2-B",
    "purpose": "Synthetic rainfall, DEM, slope, and aspect data for testing integration (Phase 5.1)",
    "description": "Demo data including a 50x50 DEM GeoTIFF, derived slope and aspect, and a CSV with synthetic rainfall measurements. All raster data covers the extent of historical landslide demo points. NOT REAL DATA.",
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
        "extent": {
            "min_longitude": min_lon,
            "max_longitude": max_lon,
            "min_latitude": min_lat,
            "max_latitude": max_lat
        }
    },
    "rainfall_csv_info": {
        "rows": len(rainfall_df),
        "columns": list(rainfall_df.columns),
        "date_range": {
            "min": rainfall_df['date'].min(),
            "max": rainfall_df['date'].max()
        }
    },
    "status": "SYNTHETIC_DEMO_DATA",
    "warning": "THIS IS SYNTHETIC DEMO DATA AND MUST NOT BE USED AS REAL OBSERVATIONS."
}

import json
with open('m2b_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("Created dem_demo_phase5_1.tif, slope_demo_phase5_1.tif, aspect_demo_phase5_1.tif, rainfall_demo.csv, and m2b_metadata.json")