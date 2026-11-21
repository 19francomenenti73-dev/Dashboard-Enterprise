"""Validation gate regression tests: explicit independent evidence is mandatory."""
from ni_front_validation import validate_fronts
import copy
evidence={"independent_source":"independent synoptic reference","reference_valid_utc":"2026-11-21T12:00:00Z","verification_method":"manual review","reviewer":"test reviewer"}
base={"type":"FeatureCollection","features":[{"type":"Feature","properties":{
"type":"cold","diagnostic":"thermal-gradient-test","valid_utc":"2026-11-21T12:00:00Z","validated":True},
"geometry":{"type":"LineString","coordinates":[[8,42],[9,43]]}}]}
def status(obj,**kwargs):return validate_fronts(obj,**kwargs)[1]
assert status(base)=="not_validated"
assert status(base,diagnostic_validated=True,evidence="case-study")=="not_validated"
assert status(base,diagnostic_validated=True,evidence=evidence)=="validated"
x=copy.deepcopy(base);x["features"][0]["geometry"]["coordinates"][0]=[120,42]
assert status(x,diagnostic_validated=True,evidence=evidence)=="out_of_domain"
x=copy.deepcopy(base);x["features"][0]["properties"]["validated"]=False
assert status(x,diagnostic_validated=True,evidence=evidence)=="unverified_feature"
x=copy.deepcopy(base);x["features"][0]["properties"]["valid_utc"]="2026-11-22T12:00:00Z"
assert status(x,diagnostic_validated=True,evidence=evidence)=="unverified_feature"
for key in evidence:
 e=copy.deepcopy(evidence);e.pop(key)
 assert status(base,diagnostic_validated=True,evidence=e)=="not_validated"
print("Front validation gate: PASS")
