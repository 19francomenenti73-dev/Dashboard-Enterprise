#!/usr/bin/env python3
"""Generate local Natural Earth GeoJSON. No commercial tile provider."""
import json
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
SOURCES = {
    "land.geojson": "ne_110m_land.geojson",
    "lakes.geojson": "ne_110m_lakes.geojson",
    "boundaries.geojson": "ne_110m_admin_0_boundary_lines_land.geojson",
}
dest = Path("data/cartografia")
dest.mkdir(parents=True, exist_ok=True)
for target, source in SOURCES.items():
    req = Request(BASE + source, headers={"User-Agent": "NowcastingItalia/1.0"})
    with urlopen(req, timeout=60) as response:
        geojson = json.load(response)
    if geojson.get("type") != "FeatureCollection" or not isinstance(geojson.get("features"), list):
        raise ValueError("Invalid GeoJSON: " + source)
    (dest / target).write_text(json.dumps(geojson, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(target, len(geojson["features"]), "features")
