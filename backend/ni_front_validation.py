"""Conservative validation gate for algorithm-derived synoptic fronts.
No automatic classification until meteorological diagnostics are independently verified.
"""
import math

ALLOWED={"cold","warm","occluded","stationary"}

def validate_fronts(collection, *, diagnostic_validated=False, evidence=None):
    """Return validated GeoJSON. Fail closed unless diagnostic is independently approved."""
    empty={"type":"FeatureCollection","features":[]}
    if not diagnostic_validated or not isinstance(evidence,dict) or not evidence.get("independent_source") or not evidence.get("reference_valid_utc") or not evidence.get("verification_method") or not evidence.get("reviewer"):
        return empty, "not_validated"
    if not isinstance(collection,dict) or collection.get("type")!="FeatureCollection":
        return empty,"invalid_geometry"
    features=[]
    for f in collection.get("features",[]):
        if not isinstance(f,dict):return empty,"invalid_feature"
        p=f.get("properties") or {}
        g=f.get("geometry") or {}
        if p.get("type") not in ALLOWED or g.get("type")!="LineString":
            return empty,"invalid_classification"
        xy=g.get("coordinates")
        if not isinstance(xy,list) or len(xy)<2:return empty,"invalid_geometry"
        for pt in xy:
            if not isinstance(pt,list) or len(pt)<2:return empty,"invalid_geometry"
            lon,lat=pt[:2]
            if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (lon,lat)):
                return empty,"invalid_coordinates"
            if not (-35<=lon<=55 and -12<=lat<=78):return empty,"out_of_domain"
        if not p.get("diagnostic") or not p.get("valid_utc"):
            return empty,"missing_provenance"
        if p.get("validated") is not True or p.get("valid_utc")!=evidence["reference_valid_utc"]:
            return empty,"unverified_feature"
        features.append(f)
    return {"type":"FeatureCollection","features":features},"validated"
