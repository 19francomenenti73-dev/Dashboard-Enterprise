#!/usr/bin/env python3
"""Inspect official MeteoGate backup catalog without downloading radar data."""
import json
from urllib.parse import urljoin, urlsplit
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
            catalog=json.loads(content)
            result["catalog_shape"]=describe(catalog)
            result["navigation"]=[]
            for item in catalog.get("links",[]):
                if not isinstance(item,dict):continue
                href=item.get("href","")
                absolute=urljoin(URL,href)
                parsed=urlsplit(absolute)
                if parsed.scheme!="https" or parsed.hostname!="radar-backup.meteogate.eu":continue
                result["navigation"].append({"path":parsed.path,"rel":item.get("rel"),"type":item.get("type")})
            for path in ["/api/collections","/api/conformance"]:
                endpoint=urljoin(URL,path)
                try:
                    with urllib.request.urlopen(urllib.request.Request(endpoint,headers={"Accept":"application/json","User-Agent":"Nowcasting-Italia-OPERA-catalog-check/1.0"}),timeout=12) as sub:
                        body=sub.read(250001)
                        if len(body)>250000:raise ValueError("Response too large")
                        obj=json.loads(body)
                        if path=="/api/collections":
                            result["collections"]=[{"id":v.get("id"),"title":v.get("title")} for v in obj.get("collections",[]) if isinstance(v,dict)][:80]
                        else:
                            result["conformance_count"]=len(obj.get("conformsTo",[]))
                except Exception as error:
                    result[path.strip("/")+"_error"]=f"{type(error).__name__}: {str(error)[:100]}"
    except Exception as exc:
        result["error"]=f"{type(exc).__name__}: {str(exc)[:180]}"
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
