"""Front gate tests: reject unverified, out-of-domain, and unlabeled lines."""
from ni_front_validation import validate_fronts
f={"type":"FeatureCollection","features":[{"type":"Feature","properties":{
"type":"cold","diagnostic":"thermal-gradient-test","valid_utc":"2026-11-21T12:00:00Z"},
"geometry":{"type":"LineString","coordinates":[[8,42],[9,43]]}}]}
assert validate_fronts(f)[1]=="not_validated"
assert validate_fronts(f,diagnostic_validated=True,evidence=None)[1]=="not_validated"
assert validate_fronts(f,diagnostic_validated=True,evidence="case-study")[1]=="validated"
f["features"][0]["geometry"]["coordinates"][0]=[120,42]
assert validate_fronts(f,diagnostic_validated=True,evidence="case-study")[1]=="out_of_domain"
print("Front validation gate: PASS")
