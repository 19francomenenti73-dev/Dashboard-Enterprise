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
        # Extract a ridge centreline instead of joining every grid point.
        # Work in local kilometres so PCA does not distort longitude at latitude.
        latitude0=float(np.mean(lat[yy]))
        lon_scale=max(0.2,float(np.cos(np.deg2rad(latitude0))))
        xy=np.column_stack((lon[xx],lat[yy]))
        km=xy*np.array([111.2*lon_scale,111.2])
        origin=km.mean(axis=0)
        centered=km-origin
        _,_,vh=np.linalg.svd(centered,full_matrices=False)
        along=centered@vh[0]
        across=centered@vh[1]
        extent=float(np.ptp(along))
        if extent<100:continue
        # Use medians of observed ridge cells in along-axis bins. This
        # suppresses the zigzag from linking multiple cells in each cross-section.
        spacing=max(18.0,extent/65.0)
        edges=np.linspace(along.min(),along.max(),max(3,int(np.ceil(extent/spacing))+1))
        centerline=[]
        for left,right in zip(edges[:-1],edges[1:]):
            selected=(along>=left)&(along<right if right!=edges[-1] else along<=right)
            if not np.any(selected):continue
            a=float(np.median(along[selected]))
            b=float(np.median(across[selected]))
            centerline.append(origin+a*vh[0]+b*vh[1])
        if len(centerline)<3:continue
        centerline=np.asarray(centerline)
        # Reject disjoint line jumps: never bridge a gap unsupported by ridge cells.
        gaps=np.linalg.norm(np.diff(centerline,axis=0),axis=1)
        if np.any(gaps>max(65.0,3.0*spacing)):
            breaks=np.r_[0,np.flatnonzero(gaps>max(65.0,3.0*spacing))+1,len(centerline)]
            segments=[centerline[a:b] for a,b in zip(breaks[:-1],breaks[1:]) if b-a>=3]
            if not segments:continue
            centerline=max(segments,key=lambda z:np.sum(np.linalg.norm(np.diff(z,axis=0),axis=1)))
        if np.sum(np.linalg.norm(np.diff(centerline,axis=0),axis=1))<100:continue
        coords=np.round(centerline/np.array([111.2*lon_scale,111.2]),3).tolist()
        if len(coords)<3:continue
        features.append({"type":"Feature","properties":{
          "type":"frontal_candidate","diagnostic":"GFS850_thermal_gradient_humidity_convergence",
          "validated":False,"max_gradient_k_per_100km":round(float(thermal[yy,xx].max()),1),
          "status":"experimental_not_analyzed_front"},
          "geometry":{"type":"LineString","coordinates":coords}})
    return {"type":"FeatureCollection","features":features[:35]}
