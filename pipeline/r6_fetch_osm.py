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
    """POST via curl: overpass-api.de returns 406 to httpx's fingerprint but accepts curl."""
    import subprocess
    import tempfile

    if dest.exists() and dest.stat().st_size > 0:
        print(f"{name}: cached ({dest.stat().st_size/1e6:.1f} MB)")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".ql", delete=False, encoding="utf-8") as tf:
        tf.write(query)
        qfile = tf.name
    try:
        for attempt in range(4):
            proc = subprocess.run(
                [
                    "curl", "-sS", "--max-time", "1000", "-A", UA,
                    "--data-urlencode", f"data@{qfile}",
                    "-o", str(dest), "-w", "%{http_code}",
                    OVERPASS,
                ],
                capture_output=True,
                text=True,
            )
            code = proc.stdout.strip()
            if proc.returncode == 0 and code == "200" and dest.exists() and dest.stat().st_size > 0:
                print(f"{name}: {dest.stat().st_size/1e6:.1f} MB", flush=True)
                return
            print(f"{name}: HTTP {code} (curl rc {proc.returncode}), retrying in {30*(attempt+1)} s", flush=True)
            dest.unlink(missing_ok=True)
            time.sleep(30 * (attempt + 1))
    finally:
        Path(qfile).unlink(missing_ok=True)
    raise RuntimeError(f"overpass failed for {name}")


def main():
    out = RAW / "osm"
    run_query("roads", ROADS_QUERY, out / "roads_ep.json")
    time.sleep(10)
    run_query("silos", SILOS_QUERY, out / "silos_ep.json")
    update_manifest([out / "roads_ep.json", out / "silos_ep.json"])


if __name__ == "__main__":
    main()
