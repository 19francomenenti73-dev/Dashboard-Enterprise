#!/usr/bin/env python3
"""N.I. SINOTTICA: GFS analysis/forecast contours from NOAA NOMADS.
Source: https://nomads.ncep.noaa.gov/ (NOAA/NCEP GFS 0.25°).
No scraping, authentication bypass, or third-party tiles. Fail closed.
Produces only scientifically derived contours; frontal boundaries require
additional validated diagnostics and are deliberately NOT fabricated.
"""
import datetime as dt
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlencode
import numpy as np
import requests
import xarray as xr
import contourpy
from scipy.ndimage import maximum_filter, minimum_filter
from ni_front_candidates import frontal_candidates

OUT = Path("data/sinottica.json")
BASE = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl"
# longitude -35..55 => 325..360 and 0..55; download 0..360 would be huge.
# Fetch two independent subsets, then merge by longitude.
PARTS = [(325,359.75),(0,55)]
LEVELS = list(range(0, 61, 3))
EMPTY = {"type":"FeatureCollection","features":[]}

def fetch_piece(cycle, hour, west, east):
    day, run = cycle
    params = {
        "file": f"gfs.t{run:02d}z.pgrb2.0p25.f{hour:03d}",
        "lev_mean_sea_level": "on", "lev_250_mb": "on", "lev_850_mb": "on", "lev_10_m_above_ground": "on",
        "var_PRMSL": "on", "var_UGRD": "on", "var_VGRD": "on", "var_TMP": "on", "var_RH": "on",
        "subregion": "", "leftlon":str(west), "rightlon":str(east),
        "toplat":"78", "bottomlat":"-12",
        "dir": f"/gfs.{day}/{run:02d}/atmos"
    }
    r = requests.get(BASE,params=params,timeout=110,headers={"User-Agent":"NowcastingItalia-Sinottica/1.0 (scientific visualization)"})
    r.raise_for_status()
    if not r.content.startswith(b"GRIB"):
        raise ValueError("NOMADS did not return GRIB2 data")
    return r.content

def open_grib(raw, short_name, level=None):
    with tempfile.NamedTemporaryFile(suffix=".grib2") as t:
        t.write(raw);t.flush()
        ds=xr.open_dataset(t.name,engine="cfgrib",
          backend_kwargs={"filter_by_keys":dict({"shortName":short_name}, **({"typeOfLevel":"isobaricInhPa","level":level} if level in (250,850) else ({"typeOfLevel":"heightAboveGround","level":10} if level==10 else {"typeOfLevel":"meanSea"}))),"indexpath":""})
        ds.load()
        return ds

def field(ds):
    v=list(ds.data_vars.values())[0]
    arr=np.asarray(v.values).squeeze()
    lat=np.asarray(ds.latitude.values)
    lon=np.asarray(ds.longitude.values)
    if arr.ndim!=2: raise ValueError("Expected 2D meteorological grid")
    return lat,lon,arr

def combine(a,b):
    lat,lon1,z1=field(a);lat2,lon2,z2=field(b)
    if len(lat)!=len(lat2) or not np.allclose(lat,lat2):raise ValueError("Latitude mismatch")
    lon=np.concatenate((lon1-360,lon2))
    z=np.concatenate((z1,z2),axis=1)
    if not np.all(np.diff(lon)>0):raise ValueError("Longitude mismatch")
    return lat,lon,z

def contours(lat,lon,z,values,kind,minimum_length=6):
    gen=contourpy.contour_generator(x=lon,y=lat,z=z, name="serial")
    feats=[]
    for value in values:
        for line in gen.lines(float(value)):
            if len(line)<minimum_length:continue
            xy=np.round(line,3).tolist()
            feats.append({"type":"Feature","properties":{"type":kind,"value":float(value)},
              "geometry":{"type":"LineString","coordinates":xy}})
    return {"type":"FeatureCollection","features":feats}

def thermal_isobars(lat,lon,msl,temp850):
    """Color isobar segments by local 850 hPa temperature anomaly, not pressure."""
    if temp850.shape!=msl.shape or not np.isfinite(temp850).all():
        raise ValueError("850 hPa thermal grid missing or invalid")
    # Broad regional median: a relative warm/cold classification, not a front.
    reference=float(np.median(temp850))
    base=contours(lat,lon,msl,np.arange(960,1053,4),"isobar")
    feats=[]
    for feature in base["features"]:
        coords=feature["geometry"]["coordinates"]
        if len(coords)<2:continue
        # Split at thermal transitions, retaining exact original contour vertices.
        segment=[coords[0]]
        previous=None
        for point in coords[1:]:
            x=int(np.clip(np.searchsorted(lon,point[0]),0,len(lon)-1))
            # latitude in NOAA grids descends north to south
            y=int(np.argmin(np.abs(lat-point[1])))
            anomaly=float(temp850[y,x]-reference)
            band="warm" if anomaly>=1.5 else "cold" if anomaly<=-1.5 else "neutral"
            if previous is not None and band!=previous and len(segment)>=2:
                feats.append({"type":"Feature","properties":dict(feature["properties"],thermal_band=previous),
                  "geometry":{"type":"LineString","coordinates":segment}})
                segment=[segment[-1]]
            segment.append(point)
            previous=band
        if len(segment)>=2:
            feats.append({"type":"Feature","properties":dict(feature["properties"],thermal_band=previous or "neutral"),
              "geometry":{"type":"LineString","coordinates":segment}})
    return {"type":"FeatureCollection","features":feats}

def wind_vectors(lat,lon,u,v,step=7,level=250):
    """Compact real 250 hPa U/V grid in m/s, never interpolated synthetic flow."""
    return {"lat":np.round(lat[::step],3).tolist(),"lon":np.round(lon[::step],3).tolist(),
      "u":np.round(u[::step,::step],2).tolist(),"v":np.round(v[::step,::step],2).tolist(),"units":"m/s","level_hpa":250} if level==250 else {"lat":np.round(lat[::step],3).tolist(),"lon":np.round(lon[::step],3).tolist(),"u":np.round(u[::step,::step],2).tolist(),"v":np.round(v[::step,::step],2).tolist(),"units":"m/s","height_m":10}

def pressure_centers(lat,lon,z):
    # Avoid duplicate pressure centers by comparing in a broad local neighborhood.
    sm=np.asarray(z)
    maxima=(sm==maximum_filter(sm,size=41,mode="nearest")) & (sm>=1020)
    minima=(sm==minimum_filter(sm,size=41,mode="nearest")) & (sm<=1005)
    feats=[]
    for mask,typ in [(maxima,"high"),(minima,"low")]:
        for y,x in np.argwhere(mask):
            if y<20 or x<20 or y>=len(lat)-20 or x>=len(lon)-20:continue
            feats.append({"type":"Feature","properties":{"type":typ,"pressure_hpa":round(float(sm[y,x]),1)},
              "geometry":{"type":"Point","coordinates":[round(float(lon[x]),3),round(float(lat[y]),3)]}})
    return {"type":"FeatureCollection","features":feats[:60]}

def cycle_candidates():
    now=dt.datetime.now(dt.timezone.utc)
    for days in range(2):
        day=now-dt.timedelta(days=days)
        for run in (18,12,6,0):
            stamp=day.replace(hour=run,minute=0,second=0,microsecond=0)
            if stamp<=now-dt.timedelta(hours=5):
                yield (stamp.strftime("%Y%m%d"),run),stamp

def build():
    last_error=None
    for cycle,initial in cycle_candidates():
        try:
            frames=[]
            for h in LEVELS:
                pieces=[fetch_piece(cycle,h,*part) for part in PARTS]
                fields={}
                for var in ("prmsl","u","v"):
                    # cfgrib shortName varies by GFS edition: verify explicitly.
                    names={"prmsl":"prmsl","u":"u","v":"v"}
                    try:
                        a=open_grib(pieces[0],names[var],250 if var in ("u","v") else None);b=open_grib(pieces[1],names[var],250 if var in ("u","v") else None)
                        fields[var]=combine(a,b)
                    except Exception as exc:
                        raise RuntimeError(f"Cannot decode {var}: {exc}")
                lat,lon,msl=fields["prmsl"]
                _,_,u=fields["u"];_,_,v=fields["v"]
                msl=msl/100.0
                wind=np.hypot(u,v)*3.6
                if msl.shape!=wind.shape or not np.allclose(lat,fields["u"][0]) or not np.allclose(lon,fields["u"][1]) or not np.allclose(lat,fields["v"][0]) or not np.allclose(lon,fields["v"][1]):
                    raise ValueError("Pressure and jet grids do not align")
                if not np.isfinite(msl).all() or not np.isfinite(wind).all():
                    raise ValueError("Non-finite weather grid")
                candidates=EMPTY
                thermal_lines=None
                try:
                    low={}
                    for name,short in (("temp","t"),("rh","r"),("u","u"),("v","v")):
                        a=open_grib(pieces[0],short,850)
                        b=open_grib(pieces[1],short,850)
                        low[name]=combine(a,b)
                        if not np.array_equal(lat,low[name][0]) or not np.array_equal(lon,low[name][1]):
                            raise ValueError("850 hPa grid mismatch")
                    candidates=frontal_candidates(lat,lon,*[low[k][2] for k in ("temp","rh","u","v")])
                    thermal_lines=thermal_isobars(lat,lon,msl,low['temp'][2])
                except Exception as e:
                    print("Frontal diagnostic unavailable, preserving other fields:",e)
                surface=None
                try:
                    a10=open_grib(pieces[0],"10u",10);b10=open_grib(pieces[1],"10u",10)
                    c10=open_grib(pieces[0],"10v",10);d10=open_grib(pieces[1],"10v",10)
                    la10,lo10,u10=combine(a10,b10)
                    lv10,lov10,v10=combine(c10,d10)
                    if not (np.array_equal(la10,lv10) and np.array_equal(lo10,lov10) and np.isfinite(u10).all() and np.isfinite(v10).all()):raise ValueError("10m grid invalid")
                    surface=wind_vectors(la10,lo10,u10,v10,step=7,level=10)
                except Exception as e:
                    print("10m wind unavailable:",e)
                frames.append({
                  "source":"NOAA/NCEP GFS 0.25° (model forecast)",
                  "run_utc":initial.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "valid_utc":(initial+dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "forecast_hour":h,
                  "isobars":thermal_lines if thermal_lines is not None else contours(lat,lon,msl,np.arange(960,1053,4),"isobar"),
                  "pressure":pressure_centers(lat,lon,msl),
                  "pressure_grid":{"lat":np.round(lat[::4],3).tolist(),"lon":np.round(lon[::4],3).tolist(),"values":np.round(msl[::4,::4],2).tolist(),"units":"hPa","level":"mean_sea_level"},
                  "jet":contours(lat,lon,wind,[100,140,180,220,260],"jet_speed_kmh"),
                  "wind_vectors":wind_vectors(lat,lon,u,v),
                  "surface_wind_vectors":surface,
                  "fronts":EMPTY,
                  "fronts_status":"not_validated",
                  "frontal_candidates":candidates
                })
            if len(frames)!=len(LEVELS):raise ValueError("Incomplete forecast")
            OUT.parent.mkdir(parents=True,exist_ok=True)
            tmp=OUT.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
              "source_url":"https://nomads.ncep.noaa.gov/","frames":frames},separators=(",",":")),encoding="utf-8")
            tmp.replace(OUT)
            print("Produced",len(frames),"verified forecast frames")
            return
        except Exception as exc:
            last_error=exc
            print("Cycle unavailable:",cycle,str(exc))
    raise RuntimeError(f"No valid NOAA cycle; retaining last valid output: {last_error}")

if __name__=="__main__":
    build()
