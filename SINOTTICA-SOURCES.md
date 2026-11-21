# N.I. SINOTTICA — provenance and publication gate

## Verified in this branch
- Natural Earth vector GeoJSON from https://github.com/nvkelso/natural-earth-vector
- Natural Earth datasets are public domain: https://www.naturalearthdata.com/about/terms-of-use/
- Leaflet 1.9.4 is open-source (BSD-2-Clause), https://github.com/Leaflet/Leaflet/blob/main/LICENSE
- Map vector geometries are NOT a digital elevation model.
- Elevation points are sparse annotations, not continuous terrain.
- No CARTO tiles or commercial basemap providers.

## Before publishing shaded relief or bathymetry
1. Download authoritative raster GeoTIFF elevation and bathymetry datasets.
2. Record original URL, provider, edition, retrieval date, license, redistribution rights, attribution requirements and checksum in this document.
3. Ensure explicit permission to redistribute derived raster images publicly.
4. Run: pip install rasterio numpy pillow
5. Run: python backend/build_terrain.py --land path/to/land.tif --sea path/to/sea.tif
6. Check coastline masks, geographic registration, sample values and output PNGs.
7. Commit generated PNGs and terrain.json ONLY on development branch.
8. Review visual alignment and licensing before merging.

Suggested data sources to investigate (NOT yet approved for redistribution):
NOAA ETOPO 2022 and GEBCO. Their current terms, versions and derived-image permissions must be verified before use.

## Meteorological data
No meteorological layer may be described as live until source, run time, valid time, coverage, age, attribution and retrieval license have been verified. Fronts must be diagnosed and labeled as algorithm-derived, not official observations.

## Deployment
The current page uses Leaflet's open-source library via CDN; a fully independent deployment should vendor the Leaflet JS/CSS and its attribution/license. No changes to main without explicit approval.
