# M2-B Synthetic/Demo Data

This directory contains synthetic/demo data for testing the M2-C Phase 4 integration pipeline.
All data here is clearly marked as synthetic and must not be used as real observations.

Files:
- rainfall_demo.csv: Synthetic rainfall data for a few locations and dates
- dem_demo.tif: A simple 3x3 pixel elevation GeoTIFF (in meters)
- slope_demo.tif: Slope derived from the DEM (in degrees)
- aspect_demo.tif: Aspect derived from the DEM (in degrees, 0=N, 90=E, etc.)

CRS: EPSG:4326 (WGS 84)
Bounding box: approximately [85.0, 27.0, 85.01, 27.01] (small area near Kathmandu for demo)