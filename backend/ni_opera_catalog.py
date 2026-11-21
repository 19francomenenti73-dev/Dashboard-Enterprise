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
            # Inspect latest observations and expose only non-sensitive metadata.
            try:
                items_url=urljoin(URL,"/api/collections/observations/items?bbox=-12,34,37,72&standard-name=RATE&format=GeoTIFF&method=comp")
                with urllib.request.urlopen(urllib.request.Request(items_url,headers={
                    "Accept":"application/geo+json, application/json",
                    "User-Agent":"Nowcasting-Italia-OPERA-catalog-check/1.0"}),timeout=18) as response:
                    raw=response.read(500001)
                    if len(raw)>500000:raise ValueError("Items response too large")
                    listing=json.loads(raw)
                result["items_count"]=len(listing.get("features",[]))
                result["items"]=[]
                for feature in listing.get("features",[])[:5]:
                    props=feature.get("properties",{})
                    assets=feature.get("assets",{})
                    result["items"].append({
                        "id":str(feature.get("id",""))[:120],
                        "datetime":props.get("datetime"),
                        "product_keys":[k for k in props if any(t in k.lower() for t in ("product","quantity","format","type"))][:20],
                        "product_values":{k:str(v)[:120] for k,v in props.items()
                            if k.lower() in ("product","product_type","quantity","data_type")},
                        "asset_keys":list(assets)[:30],
                        "asset_types":{k:v.get("type") for k,v in assets.items() if isinstance(v,dict)}
                    })
                # Compare availability without restrictive filters; do not infer missing data.
                for label,query in [
                    ("all_europe","bbox=-12,34,37,72"),
                    ("rate_europe","bbox=-12,34,37,72&standard-name=RATE"),
                    ("dbzh_europe","bbox=-12,34,37,72&standard-name=DBZH")]:
                    try:
                        endpoint=urljoin(URL,"/api/collections/observations/items?"+query)
                        with urllib.request.urlopen(urllib.request.Request(endpoint,headers={
                            "Accept":"application/json",
                            "User-Agent":"Nowcasting-Italia-OPERA-catalog-check/1.0"
                        }),timeout=18) as response:
                            payload=response.read(400001)
                            if len(payload)>400000:raise ValueError("Response too large")
                            data=json.loads(payload)
                        features=data.get("features",[])
                        result[label]={
                            "count":len(features),
                            "numberMatched":data.get("numberMatched"),
                            "sample":[{"id":str(f.get("id",""))[:100],
                                       "properties":{k:str(v)[:90] for k,v in f.get("properties",{}).items()
                                         if k.lower() in ("datetime","standard_name","standard-name","format","method","product")},
                                       "assets":list(f.get("assets",{}))[:10]}
                                      for f in features[:3] if isinstance(f,dict)]}
                    except Exception as error:
                    result[label]={"error":f"{type(error).__name__}: {str(error)[:120]}"}
            except Exception as error:
                result["items_error"]=f"{type(error).__name__}: {str(error)[:160]}"
                if hasattr(error,"read"):
                    result["items_error_detail"]=error.read(1800).decode("utf-8","replace")[:1800]
                # A 400 may indicate required parameters or unsupported endpoint.
                # Fetch the published OpenAPI schema and collection metadata instead of guessing.
                for label,route in [
                    ("observations_collection","/api/collections/observations"),
                    ("openapi","/api/openapi.json")]:
                    try:
                        with urllib.request.urlopen(urllib.request.Request(
                            urljoin(URL,route),headers={"Accept":"application/json",
                            "User-Agent":"Nowcasting-Italia-OPERA-catalog-check/1.0"}
                        ),timeout=18) as resp:
                            body=resp.read(900001)
                            if len(body)>900000:raise ValueError("Response too large")
                            obj=json.loads(body)
                        if label=="openapi":
                            result["openapi_paths"]=[p for p in obj.get("paths",{})
                                if "collection" in p or "observation" in p][:60]
                            result["openapi_items_get"]=describe(
                                obj.get("paths",{}).get("/collections/observations/items",{}),0)
                            result["api_parameters"]={}
                            for endpoint in ["/collections/observations/items",
                                             "/collections/observations/area",
                                             "/collections/observations/position"]:
                                spec=obj.get("paths",{}).get(endpoint,{})
                                params=spec.get("get",{}).get("parameters",[])
                                result["api_parameters"][endpoint]=[
                                    {"name":v.get("name"),"required":v.get("required"),
                                     "schema":describe(v.get("schema",{}))}
                                    for v in params if isinstance(v,dict)][:30]
                        else:
                            result["collection_parameters"]=[
                                {"id":v.get("id"),"values":v.get("values",[])[:30] if isinstance(v.get("values"),list) else None,
                                 "interval":v.get("interval")} for v in obj.get("extent",{}).get("custom",[])
                                 if isinstance(v,dict)][:12]
                            result["collection_detail"]={
                                "id":obj.get("id"),
                                "itemType":obj.get("itemType"),
                                "extent":describe(obj.get("extent")),
                                "links":[{"rel":v.get("rel"),"path":urlsplit(
                                    urljoin(URL,v.get("href",""))).path}
                                    for v in obj.get("links",[]) if isinstance(v,dict)][:25]}
                    except Exception as detail_error:
                        result[label+"_error"]=f"{type(detail_error).__name__}: {str(detail_error)[:140]}"
    except Exception as exc:
        result["error"]=f"{type(exc).__name__}: {str(exc)[:180]}"
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
