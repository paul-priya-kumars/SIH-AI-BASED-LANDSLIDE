\# M2-A Integration Handoff



\## Owner

M2-A — Satellite \& NDVI



\## Phase Status

Phase 1 — AOI: Complete

Phase 2 — Sentinel-2 + NDVI: Complete

Phase 3 — Temporal NDVI: Complete



\## Main Outputs



\- data/ndvi/phase3/latest\_mosaic\_epsg4326.tif

\- data/ndvi/phase3/feature\_table.csv

\- data/ndvi/phase3/feature\_table.parquet



\## CRS



EPSG:4326



\## GeoTIFF Bands



1\. Current NDVI

2\. Baseline NDVI

3\. Delta NDVI

4\. QA



\## NoData



\-9999



\## M1 Inputs



M1 should consume the feature table containing:

\- coordinates

\- current NDVI

\- baseline NDVI

\- delta NDVI

\- quality indicators

\- composite metadata



\## M2-C Inputs



M2-C should consume:

\- Phase 3 GeoTIFF

\- feature table

\- QA information

\- temporal metadata



\## Important



Real Sentinel-2 data must be identified as real data.



Synthetic test fixtures must remain explicitly marked:

is\_mock=True



\## Do Not



\- modify M2-A processing logic without coordination

\- treat NoData as NDVI = 0

\- mix synthetic and real data

