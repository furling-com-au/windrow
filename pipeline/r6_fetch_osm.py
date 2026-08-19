"""R6/R1: OpenStreetMap extracts for the Eyre Peninsula (ODbL; attribution required).

1. Drivable classified road network for the EP + far west bounding box, via Overpass.
2. Silo / grain-storage features (facility-precision coordinates for receival sites).

Raw JSON cached under data/raw/osm/. Overpass etiquette: one query at a time,
generous timeout, 10 s pause between queries.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, UA, update_manifest

OVERPASS = "https://overpass-api.de/api/interpreter"
# south, west, north, east — covers EP proper + far west coast to Penong
BBOX = "-35.25,131.0,-31.0,137.65"

ROADS_QUERY = f"""
[out:json][timeout:900];
(
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential)$"]({BBOX});
);
out tags geom;
"""

SILOS_QUERY = f"""
[out:json][timeout:300];
(
  nwr["man_made"="silo"]({BBOX});
  nwr["man_made"="storage_tank"]["content"~"grain",i]({BBOX});
  nwr["building"="silo"]({BBOX});
);
out tags center;
"""


def run_query(name: str, query: str, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        print(f"{name}: cached ({dest.stat().st_size/1e6:.1f} MB)")
        return
    with httpx.Client(headers={"User-Agent": UA}, timeout=1000) as client:
        for attempt in range(4):
            r = client.post(OVERPASS, data={"data": query})
            if r.status_code == 200:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                print(f"{name}: {len(r.content)/1e6:.1f} MB")
                return
            print(f"{name}: HTTP {r.status_code}, retrying in {30*(attempt+1)} s")
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"overpass failed for {name}")


def main():
    out = RAW / "osm"
    run_query("roads", ROADS_QUERY, out / "roads_ep.json")
    time.sleep(10)
    run_query("silos", SILOS_QUERY, out / "silos_ep.json")
    update_manifest([out / "roads_ep.json", out / "silos_ep.json"])


if __name__ == "__main__":
    main()
