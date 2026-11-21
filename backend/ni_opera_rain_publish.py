#!/usr/bin/env python3
"""Publish only verified, recent, observed OPERA rain-rate pixels."""
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform_bounds
from rasterio.transform import from_bounds

BASE = "https://radar-backup.meteogate.eu"
ITEM = BASE + "/api/collections/observations/items/cfd52a3d56b8e627f6b00511fce80ddb"
OUT = Path("data/opera_nimbus")
MAX_BYTES = 45_000_000

def fetch(url, accept="application/json"):
    u = urlsplit(url)
    if u.scheme != "https" or u.hostname != "radar-backup.meteogate.eu":
        raise ValueError("Only the official MeteoGate HTTPS host is permitted")
    with urlopen(Request(url, headers={"Accept": accept,
                    "User-Agent": "Nowcasting-Italia-Sinottica/1.0"}), timeout=35) as r:
        content_type = r.headers.get("Content-Type", "")
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("Radar response exceeds size limit")
        return data, content_type

def utc_time(value):
    if not isinstance(value, str):
        raise ValueError("Observation timestamp missing")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp without timezone")
    now = datetime.now(timezone.utc)
    age = (now - dt.astimezone(timezone.utc)).total_seconds()
    if not -300 <= age <= 2700:
        raise ValueError("Radar observation outside 45-minute freshness window")
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def main():
    item = json.loads(fetch(ITEM)[0])
    p = item["properties"]
    if p.get("standard_name") != "RATE" or p.get("format") != "GeoTIFF":
        raise ValueError("Unexpected OPERA product")
    # Only depict observed wet/dry coverage; never claim precipitation intensity.
    observed = utc_time(p.get("datetime") or p.get("end_datetime"))
    url = p.get("data")
    if not isinstance(url, str):
        raise ValueError("No official data URL")
    payload, kind = fetch(url, "image/tiff, application/octet-stream")
    if payload[:4] not in (b"II*\x00", b"MM\x00*"):
        raise ValueError("Data endpoint did not return a GeoTIFF")
    with rasterio.MemoryFile(payload) as memory:
        with memory.open() as ds:
            if ds.count < 1 or ds.crs is None or ds.nodata is None:
                raise ValueError("GeoTIFF lacks required raster metadata")
            # Reproject to geographic bounds for Leaflet imageOverlay.
            left, bottom, right, top = transform_bounds(ds.crs, "EPSG:4326", *ds.bounds, densify_pts=40)
            if not (-180 <= left < right <= 180 and -90 <= bottom < top <= 90):
                raise ValueError("Invalid geographic extent")
            w, h = min(ds.width, 2200), min(ds.height, 2200)
            values = np.full((h, w), np.nan, dtype=np.float32)
            reproject(
                source=rasterio.band(ds, 1), destination=values,
                src_transform=ds.transform, src_crs=ds.crs,
                src_nodata=ds.nodata,
                dst_transform=from_bounds(left, bottom, right, top, w, h),
                dst_crs="EPSG:4326", dst_nodata=np.nan,
                resampling=Resampling.nearest,
            )
    wet = np.isfinite(values) & (values > 0)
    # A valid dry scene is still an observation: publish a transparent PNG.
    # Transparent everywhere without rain; categorical palette, no dry backdrop.
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    levels = [(0, (82, 177, 239)), (1, (45, 182, 118)),
              (5, (247, 209, 72)), (15, (244, 117, 47)),
              (30, (204, 58, 150))]
    for low, color in levels:
        mask = wet & (values >= low)
        rgba[mask, :3] = color
        rgba[mask, 3] = 190
    OUT.mkdir(parents=True, exist_ok=True)
    name = "observed_rain.png"
    buffer = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buffer, format="PNG", optimize=True)
    # Write image first, manifest last: the frontend never sees a new manifest without its image.
    (OUT / name).write_bytes(buffer.getvalue())
    manifest = {
        "product": "OPERA_NIMBUS_RRATE", "units": "presence", "license": "CC BY 4.0",
        "observed_utc": observed, "bounds": [[bottom, left], [top, right]],
        "image": name, "rain_only": True, "transparent_no_rain": True,
        "attribution": "EUMETNET OPERA / MeteoGate",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Published observed wet-area mask", observed, int(wet.sum()))

if __name__ == "__main__":
    main()
