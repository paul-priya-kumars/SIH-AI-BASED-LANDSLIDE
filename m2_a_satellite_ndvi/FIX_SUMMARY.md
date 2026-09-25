# Fix Summary: Sentinel-2 Resolution Mismatch in Phase 2 NDVI Processing

## Problem
The Phase 3 real-data validation was failing with the error:
```
SCL shape (5490, 5490) does not match NDVI shape (10980, 10980)
```

This occurred because:
- Sentinel-2 RED (B04) and NIR (B08) bands are at 10m resolution
- Sentinel-2 SCL (Scene Classification) band is at 20m resolution  
- In the Phase 3 temporal mosaic processing pipeline, bands were being downloaded at their native resolutions
- The `compute_ndvi_array` function in `phase2_sentinel_ndvi/ndvi_processor.py` was raising a ValueError when SCL shape didn't match RED/NIR shape
- This prevented NDVI computation, temporal compositing, and all downstream Phase 3 products

## Solution
Modified `phase2_sentinel_ndvi/ndvi_processor.py` to:

1. **Added necessary imports** for rasterio resampling capabilities
2. **Enhanced `compute_ndvi_array` function** to automatically resample SCL bands when shape mismatch occurs:
   - Instead of raising ValueError, the function now resamples SCL to match RED/NIR dimensions
   - Uses nearest-neighbor resampling to preserve discrete SCL classification values
   - Maintains all existing NDVI calculation and masking logic
3. **Added `_resample_scl_to_match` helper function** that performs nearest-neighbor resampling:
   - Handles both upsampling and downscaling scenarios
   - Uses edge-padding to maintain exact output dimensions
   - Preserves input data type (important for SCL integer classification values)
4. **Added comprehensive regression test** in `tests/test_phase2_ndvi.py`:
   - `test_sentinel2_resolution_mismatch()` - Tests 20m SCL → 10m nearest-neighbor resampling → SCL masking → NDVI workflow
   - Verifies shape alignment, correct SCL class preservation after resampling, and proper masking

## Key Features of the Fix
- **Minimal and focused**: Only touches the specific function causing the issue
- **Backward compatible**: All existing functionality preserved (40/40 tests pass)
- **Production correct**: Uses nearest-neighbor resampling as specified for discrete classification data
- **No synthetic data introduction**: Only processes actual input data
- **Preserves existing behavior**: No changes to NDVI formula, masking logic, or output characteristics
- **Handles edge cases**: Works with various resolution ratios, not just 2:1

## Verification
- ✅ All existing Phase 1, 2, and 3 tests pass (40/40)
- ✅ New regression test passes and validates the fix
- ✅ No changes to unrelated M2-B/M2-C code (as instructed)
- ✅ Maintains strict separation between mock and real data
- ✅ Preserves CRS/transform/resolution handling in calling code

## Files Modified
1. `phase2_sentinel_ndvi/ndvi_processor.py` - Added SCL resampling logic
2. `tests/test_phase2_ndvi.py` - Added regression test for Sentinel-2 resolution mismatch

## Next Steps
As requested by the user, after this fix passes tests, the next step is to rerun the actual Phase 3 real-data validation using real Sentinel-2 assets (NO mock data) to validate the complete end-to-end pipeline.