"""Experimental frontal-zone diagnostic from real NOAA GFS 850 hPa fields.
NOT an operational frontal analysis. All output is tagged unvalidated.
Uses horizontal thermal gradients, low-level convergence and humidity.
"""
import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.ndimage import maximum_filter
from scipy.spatial import cKDTree

def frontal_candidates(lat,lon,temp_k,rh,u,v):
    """GeoJSON tentative frontal zones, never official cold/warm fronts."""
    empty={"type":"FeatureCollection","features":[]}
    t=np.asarray(temp_k,dtype=float);humid=np.asarray(rh,dtype=float)
    u=np.asarray(u,dtype=float);v=np.asarray(v,dtype=float)
    if any(x.shape!=t.shape for x in (humid,u,v)) or t.ndim!=2:
        raise ValueError("850 hPa grid mismatch")
    if not all(np.isfinite(x).all() for x in (t,humid,u,v)):
        raise ValueError("Nonfinite 850 hPa fields")
    if t.shape[0]<25 or t.shape[1]<25:return empty
    # Physical distance in km: longitude spacing contracts with latitude.
    lat=np.asarray(lat);lon=np.asarray(lon)
    dy=max(abs(np.median(np.diff(lat)))*111.2,1)
    dx=np.maximum(np.cos(np.deg2rad(lat))[:,None]*abs(np.median(np.diff(lon)))*111.2,5)
    smooth=gaussian_filter(t,2.0)
    gy=np.gradient(smooth,axis=0)/dy
    gx=np.gradient(smooth,axis=1)/dx
    thermal=np.hypot(gx,gy)*100 # Kelvin / 100 km
    du=np.gradient(gaussian_filter(u,2),axis=1)/(dx*1000)
    dv=np.gradient(gaussian_filter(v,2),axis=0)/(dy*1000)
    convergence=-(du+dv)
    # Restrict to a thermal-gradient ridge with humid air and convergence.
    ridge=(thermal>=3.5)&(thermal>=maximum_filter(thermal,size=9)*.86)
    mask=ridge&(humid>=55)&(convergence>=-1e-5)
    labels,n=label(mask)
    features=[]
    for component in range(1,n+1):
        yy,xx=np.where(labels==component)
        if len(xx)<8:continue
        # Geographic polyline along dominant axis of the contiguous ridge.
        xy=np.column_stack((lon[xx],lat[yy]))
        centered=xy-xy.mean(axis=0)
        _,_,vh=np.linalg.svd(centered,full_matrices=False)
        order=np.argsort(centered@vh[0])
        xy=xy[order]
        # Require geographic extent > 100 km; suppress tiny noisy fragments.
        extent=np.hypot((xy[-1,0]-xy[0,0])*111*np.cos(np.deg2rad(xy[:,1].mean())),
                        (xy[-1,1]-xy[0,1])*111)
        if extent<100:continue
        stride=max(1,len(xy)//80)
        coords=np.round(xy[::stride],3).tolist()
        if len(coords)<2:continue
        features.append({"type":"Feature","properties":{
          "type":"frontal_candidate","diagnostic":"GFS850_thermal_gradient_humidity_convergence",
          "validated":False,"max_gradient_k_per_100km":round(float(thermal[yy,xx].max()),1),
          "status":"experimental_not_analyzed_front"},
          "geometry":{"type":"LineString","coordinates":coords}})
    return {"type":"FeatureCollection","features":features[:35]}
