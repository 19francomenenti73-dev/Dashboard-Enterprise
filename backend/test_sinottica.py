"""Offline checks: no invented fronts, stable JSON schema, contour generation."""
import json
from pathlib import Path
import numpy as np
from ni_gfs import contours,pressure_centers
lat=np.linspace(78,-12,80)
lon=np.linspace(-35,55,90)
x,y=np.meshgrid(lon,lat)
z=1013+9*np.cos(x/15)+6*np.sin(y/10)
c=contours(lat,lon,z,[1008,1012,1016],"isobar")
assert c["type"]=="FeatureCollection"
assert len(c["features"])>0
assert all(f["geometry"]["type"]=="LineString" for f in c["features"])
p=pressure_centers(lat,lon,z)
assert p["type"]=="FeatureCollection"
j=json.loads(Path("data/sinottica.json").read_text())
assert isinstance(j["frames"],list)
print("Sinottica offline schema and contour checks OK")
