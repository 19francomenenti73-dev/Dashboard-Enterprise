"""Deterministic physical consistency checks for experimental GFS frontal zones.
These tests do NOT constitute validation against independent observations.
"""
import numpy as np
from ni_front_candidates import frontal_candidates
lat=np.linspace(60,20,121)
lon=np.linspace(-20,30,151)
shape=(len(lat),len(lon))
t=np.full(shape,285.0)
rh=np.full(shape,80.0)
u=np.zeros(shape)
v=np.zeros(shape)
def check(fc):
 assert fc["type"]=="FeatureCollection"
 for f in fc["features"]:
  assert f["properties"]["validated"] is False
  assert f["properties"]["type"]=="frontal_candidate"
  assert len(f["geometry"]["coordinates"])>=2
  for x,y in f["geometry"]["coordinates"]:
   assert lon.min()<=x<=lon.max() and lat.min()<=y<=lat.max()
check(frontal_candidates(lat,lon,t,rh,u,v))
assert frontal_candidates(lat,lon,t,rh,u,v)["features"]==[], "Uniform temperature must not create fronts"
for field in (t,rh,u,v):
 assert field.shape==shape
try:
 bad=t.copy();bad[2,2]=np.nan
 frontal_candidates(lat,lon,bad,rh,u,v)
 raise AssertionError("Non-finite grid was accepted")
except ValueError:pass
try:
 frontal_candidates(lat,lon,t,rh[:,:-1],u,v)
 raise AssertionError("Mismatched grid was accepted")
except ValueError:pass
# Smooth meridional thermal boundary; candidate count is diagnostic only.
x=np.broadcast_to(lon[None,:],shape)
boundary=278+12/(1+np.exp(-np.clip(x*1.5,-50,50)))
result=frontal_candidates(lat,lon,boundary,rh,u,v)
check(result)
print("Frontal candidate physics/schema regression: PASS; candidate count:",len(result["features"]))
