#!/usr/bin/env python3
"""EUMETView WMS advertised time coverage; never infer imagery from tile success."""
import datetime as dt
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import requests

URL="https://view.eumetsat.int/geoserver/wms"
LAYERS={"rgb":"mtg_fd:rgb_geocolour","water_vapour":"msg_fes:rgb_airmass"}
OUT=Path("data/satellite_status.json")

def parse_times(value):
    out=[]
    for part in (value or "").split(","):
        part=part.strip()
        if not part:continue
        if "/" in part:
            pieces=part.split("/")
            if len(pieces)<2:continue
            part=pieces[1]  # latest advertised endpoint; interval is NOT a list of available images
        try:
            stamp=dt.datetime.fromisoformat(part.replace("Z","+00:00"))
            if stamp.tzinfo:out.append(stamp.astimezone(dt.timezone.utc))
        except ValueError:continue
    return out

def probe():
    now=dt.datetime.now(dt.timezone.utc)
    result={"checked_utc":now.isoformat(),"source":URL,"products":{}}
    try:
        r=requests.get(URL,params={"service":"WMS","request":"GetCapabilities","version":"1.3.0"},timeout=35,
                       headers={"User-Agent":"NowcastingItalia-Sinottica/1.0"})
        r.raise_for_status()
        root=ET.fromstring(r.content)
        for kind,name in LAYERS.items():
            item={"layer":name,"state":"red","latest_utc":None,"age_minutes":None,
                  "reason":"Layer or advertised time unavailable"}
            for layer in root.iter():
                if layer.tag.rsplit("}",1)[-1]!="Layer":continue
                names=[x.text for x in layer if x.tag.rsplit("}",1)[-1]=="Name"]
                if name not in names:continue
                values=[]
                for x in layer:
                    tag=x.tag.rsplit("}",1)[-1]
                    if tag in ("Dimension","Extent") and x.attrib.get("name","").lower()=="time":
                        values+=parse_times(x.text)
                if values:
                    latest=max(values)
                    age=(now-latest).total_seconds()/60
                    item.update(latest_utc=latest.isoformat(),age_minutes=round(age))
                    if -10<=age<=60:item.update(state="green",reason="Latest advertised imagery within 60 min")
                    elif -10<=age<=180:item.update(state="yellow",reason="Imagery delayed 1–3 h")
                    else:item["reason"]="No current imagery advertised"
                else:item["reason"]="No time dimension on layer"
                break
            result["products"][kind]=item
    except Exception as exc:
        for kind,name in LAYERS.items():
            result["products"][kind]={"layer":name,"state":"red","latest_utc":None,
                                     "reason":"WMS capabilities not verifiable: "+str(exc)[:160]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))
if __name__=="__main__":probe()
