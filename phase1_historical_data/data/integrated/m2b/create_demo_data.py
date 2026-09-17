import rasterio
import numpy as np
from rasterio.transform import from_origin
import pandas as pd

# Define the geotransform: origin at upper left, pixel size 0.005 degrees
# We'll place it near Kathmandu: longitude 85.3, latitude 27.7
transform = from_origin(85.3, 27.7, 0.005, 0.005)  # x_size, y_size (negative y_size for north-up)
width, height = 3, 3

# Create a simple DEM array (elevation in meters)
dem_array = np.array([[1300, 1310, 1320],
                      [1290, 1300, 1310],
                      [1280, 1290, 1300]], dtype=np.float32)

# Write the DEM GeoTIFF
with rasterio.open(
    'dem_demo.tif',
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
print("Created dem_demo.tif")

# Calculate slope and aspect using rasterio's dataset methods?
# For simplicity, we'll use basic numpy gradient (not geographically accurate but okay for demo)
# Convert pixel size to degrees, but we'll approximate 1 degree ~ 111 km at equator, so 0.005 deg ~ 555m
pixel_size_deg = 0.005
# Approximate meters per degree at this latitude (27.7):
# 1 degree latitude = 111 km, 1 degree longitude = 111 * cos(latitude) km
lat_rad = np.radians(27.7)
m_per_deg_lat = 111000
m_per_deg_lon = 111000 * np.cos(lat_rad)
# Pixel size in meters
pixel_size_lat_m = pixel_size_deg * m_per_deg_lat
pixel_size_lon_m = pixel_size_deg * m_per_deg_lon

# Compute gradient in meters
dz_dy, dz_dx = np.gradient(dem_array, pixel_size_lat_m, pixel_size_lon_m)
# Slope in degrees
slope_array = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)) * 180 / np.pi
# Aspect in degrees (0=N, 90=E, 180=S, 270=W)
aspect_array = np.arctan2(-dz_dx, dz_dy) * 180 / np.pi
aspect_array = (aspect_array + 360) % 360  # Convert to 0-360

# Write slope GeoTIFF
with rasterio.open(
    'slope_demo.tif',
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
print("Created slope_demo.tif")

# Write aspect GeoTIFF
with rasterio.open(
    'aspect_demo.tif',
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
print("Created aspect_demo.tif")

# Create a synthetic rainfall CSV
# We'll create a DataFrame with columns: location_id, date, rainfall_24h, rainfall_3d, rainfall_7d
rainfall_data = {
    'location_id': ['LOC001', 'LOC002', 'LOC003', 'LOC004', 'LOC005'],
    'date': ['2020-05-15', '2020-05-15', '2020-05-15', '2020-05-15', '2020-05-15'],
    'rainfall_24h': [10.5, 0.0, 25.3, 5.0, 0.0],
    'rainfall_3d': [45.2, 2.1, 80.0, 15.0, 0.0],
    'rainfall_7d': [80.0, 5.0, 120.0, 30.0, 2.0]
}
rainfall_df = pd.DataFrame(rainfall_data)
rainfall_df.to_csv('rainfall_demo.csv', index=False)
print("Created rainfall_demo.csv")

# Create metadata for the M2-B datasets
metadata = {
    "dataset_id": "M2B_DEMO_DATA",
    "module": "M2-B",
    "purpose": "Synthetic rainfall, DEM, slope, and aspect data for testing integration",
    "description": "Demo data including a 3x3 DEM GeoTIFF, derived slope and aspect, and a CSV with synthetic rainfall measurements. NOT REAL DATA.",
    "source": "Synthetic data generated for testing",
    "date_generated": "2026-09-16",
    "crs": "EPSG:4326",
    "integration_crs": "EPSG:4326",
    "raster_info": {
        "width": width,
        "height": height,
        "pixel_size_x": 0.005,
        "pixel_size_y": 0.005,
        "bands": 1,
        "nodata": -9999.0,
        "data_type": "float32",
        "extent": {
            "min_longitude": 85.3,
            "max_longitude": 85.315,
            "min_latitude": 27.685,
            "max_latitude": 27.7
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
print("Created m2b_metadata.json")