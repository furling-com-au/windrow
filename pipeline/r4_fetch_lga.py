"""R4: SA Local Government Area boundaries (for PIRSA district assignment).

Source: data.sa.gov.au 'local-government-areas' (CC-BY, Government of South Australia /
DIT): https://www.dptiapps.com.au/dataportal/LGA_geojson.zip
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, fetch, update_manifest

URL = "https://www.dptiapps.com.au/dataportal/LGA_geojson.zip"


def main():
    dest = RAW / "sa_lga" / "LGA_geojson.zip"
    fetch(URL, dest, timeout=600)
    with zipfile.ZipFile(dest) as z:
        names = z.namelist()
        print("zip contents:", names)
        for n in names:
            if n.lower().endswith((".geojson", ".json")):
                z.extract(n, dest.parent)
                print("extracted:", n, (dest.parent / n).stat().st_size / 1e6, "MB")
    update_manifest([dest])


if __name__ == "__main__":
    main()
