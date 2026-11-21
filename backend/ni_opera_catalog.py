#!/usr/bin/env python3
"""Inspect official MeteoGate backup catalog without downloading radar data."""
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://radar-backup.meteogate.eu/"
OUT = Path("data/opera_nimbus/catalog_diagnostic.json")
def describe(value, depth=0):
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {str(k)[:90]: describe(v, depth+1) for k,v in list(value.items())[:35]}
    if isinstance(value, list):
        return {"count":len(value),"first":describe(value[0],depth+1) if value else None}
    if isinstance(value,str):
        # Avoid copying tokens, credentials, or full download URLs into public repo
        return {"type":"string","length":len(value)}
    return value if isinstance(value,(bool,int,float)) else type(value).__name__
def main():
    result={"checked_utc":datetime.now(timezone.utc).isoformat(),"source":URL,
            "purpose":"catalog structure only","product_verified":False}
    try:
        request=urllib.request.Request(URL,headers={"Accept":"application/json",
            "User-Agent":"Nowcasting-Italia-OPERA-catalog-check/1.0"})
        with urllib.request.urlopen(request,timeout=20) as response:
            content=response.read(300_001)
            if len(content)>300_000:raise ValueError("Catalog response too large")
            result["http_status"]=response.status
            result["catalog_shape"]=describe(json.loads(content))
    except Exception as exc:
        result["error"]=f"{type(exc).__name__}: {str(exc)[:180]}"
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
