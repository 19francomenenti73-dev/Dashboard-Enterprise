#!/usr/bin/env python3
"""Create transparent hillshade PNGs from properly licensed local GeoTIFFs.
Usage: python backend/build_terrain.py --land path/to/land_dem.tif --sea path/to/bathymetry.tif
Does not download datasets. Document source, license, attribution before publishing.
Dependencies: rasterio numpy pillow
"""
import argparse
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform_bounds
from rasterio.transform import from_bounds
from PIL import Image

OUT = Path("data/cartografia")
# Explicit geographic bounds: W S E N, encompassing Europe and eastern Atlantic.
BBOX = (-35.0, -12.0, 55.0, 78.0)
W, H = 1800, 1800

def make(path, filename, sea=False):
    with rasterio.open(path) as src:
        if src.crs is None:
            raise ValueError(f"{path}: missing CRS")
        # Read and reproject to a fixed EPSG:4326 grid. Never treat missing data as zero elevation.
        dst = np.full((H, W), np.nan, dtype="float32")
        reproject(
            source=rasterio.band(src, 1), destination=dst,
            src_transform=src.transform, src_crs=src.crs,
            src_nodata=src.nodata, dst_transform=from_bounds(*BBOX, W, H),
            dst_crs="EPSG:4326", dst_nodata=np.nan, resampling=Resampling.bilinear,
        )
    valid = np.isfinite(dst) & ((dst < 0) if sea else (dst >= 0))
    if not valid.any():
        raise ValueError(f"{path}: no valid {'bathymetry' if sea else 'land elevation'} pixels")
    # Derivatives of real heights; alpha masks invalid pixels.
    z = np.where(valid, dst, 0)
    gy, gx = np.gradient(z)
    # Latitude-aware meters/pixel approximation, avoids severe E-W distortion.
    lat = np.linspace(BBOX[3], BBOX[1], H)[:, None]
    dx = np.maximum(100.0, 111320.0 * np.cos(np.radians(lat)) * (BBOX[2]-BBOX[0])/W)
    dy = 111320.0 * (BBOX[3]-BBOX[1])/H
    slope_x, slope_y = gx/dx, gy/dy
    # 315-degree NW light, 45-degree altitude.
    az, alt = np.deg2rad(315), np.deg2rad(45)
    slope = np.arctan(np.hypot(slope_x, slope_y))
    aspect = np.arctan2(slope_y, -slope_x)
    shade = np.sin(alt)*np.cos(slope) + np.cos(alt)*np.sin(slope)*np.cos(az-aspect)
    shade = np.clip((shade + 1)/2, 0, 1)
    # Neutral land relief and muted blue-grey seabed; transparent elsewhere.
    lo, hi = ((103, 131, 147), (174, 196, 206)) if sea else ((145, 148, 143), (235, 233, 223))
    color = np.empty((H, W, 4), dtype=np.uint8)
    for c in range(3):
        color[:, :, c] = np.clip(lo[c] + shade*(hi[c]-lo[c]), 0, 255).astype(np.uint8)
    color[:, :, 3] = np.where(valid, 190 if sea else 215, 0).astype(np.uint8)
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(color, "RGBA").save(OUT/filename, optimize=True)
    print(filename, int(valid.sum()), "valid pixels")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--land", required=True, help="Licensed elevation GeoTIFF")
    p.add_argument("--sea", required=True, help="Licensed bathymetry GeoTIFF")
    args = p.parse_args()
    make(args.sea, "bathymetry.png", True)
    make(args.land, "hillshade.png", False)
    (OUT/"terrain.json").write_text(json.dumps({
        "bounds": [[BBOX[1], BBOX[0]], [BBOX[3], BBOX[2]]],
        "land": "data/cartografia/hillshade.png",
        "sea": "data/cartografia/bathymetry.png",
        "status": "derived from supplied licensed raster data; see provenance"
    }, indent=2), encoding="utf-8")
