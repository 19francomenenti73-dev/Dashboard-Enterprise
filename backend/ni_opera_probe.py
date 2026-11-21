#!/usr/bin/env python3
"""Diagnostica non distruttiva per l'accesso OPERA/MeteoGate.
Non pubblica dati radar e non modifica i prodotti esistenti.
"""
import json
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

TARGETS = [
    "https://radar.meteogate.eu/",
    "https://radar-backup.meteogate.eu/",
    "https://s3.waw3-1.cloudferro.com/openradar-24h/?list-type=2&max-keys=1",
]
OUT = Path("data/opera_nimbus/diagnostics.json")
def check(url):
    host = urlsplit(url).hostname
    result = {"host": host, "dns": False, "http_status": None, "error": None}
    try:
        socket.getaddrinfo(host, 443)
        result["dns"] = True
        request = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "Nowcasting-Italia-Sinottica-OPERA-diagnostic/1.0",
            "Accept": "application/json, application/xml, */*",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            result["http_status"] = response.status
            result["content_type"] = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        result["http_status"] = error.code
        result["error"] = "HTTP response; API route may require adjustment"
    except Exception as error:
        result["error"] = f"{type(error).__name__}: {str(error)[:160]}"
    return result
def main():
    data = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Endpoint reachability only; not product or license validation",
        "endpoints": [check(url) for url in TARGETS],
        "nimbus_verified": False,
        "radar_published": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps(data, indent=2))
if __name__ == "__main__":
    main()
