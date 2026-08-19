"""R4: download ABARES CLUM national 50 m land-use raster (Update December 2023, v2).

Source: https://www.agriculture.gov.au/abares/aclump/land-use/catchment-scale-land-use-and-commodities-update-2023
Direct:  https://www.agriculture.gov.au/sites/default/files/documents/clum_50m_2023_v2.zip (158 MB)
Licence: CC BY 4.0. DOI 10.25814/2w2p-ph98. SA is clipped from the national GeoTIFF later.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, fetch, update_manifest

URL = "https://www.agriculture.gov.au/sites/default/files/documents/clum_50m_2023_v2.zip"


def main():
    dest = RAW / "abares_clum" / "clum_50m_2023_v2.zip"
    fetch(URL, dest, timeout=1800)
    print(f"clum: {dest.stat().st_size/1e6:.1f} MB")
    update_manifest([dest])


if __name__ == "__main__":
    main()
