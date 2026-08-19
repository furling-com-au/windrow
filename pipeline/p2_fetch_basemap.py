"""Phase 4 basemap: land polygons for a fully self-contained vector basemap.

Source: Natural Earth 10m land (public domain), GeoJSON mirror on naturalearth CDN
(geojson.xyz). Clipped to the EP bbox and quantized -> app/public/data/basemap.json.
The app draws: sea = background colour, land polygons, OSM roads, site/town labels.
No external tile server at runtime (Cloudflare Pages friendly; only attribution needed
is OSM ODbL for roads + Natural Earth public domain note).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, ROOT, fetch, update_manifest

APP_DATA = ROOT / "app" / "public" / "data"
URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson"
BBOX = (129.5, -36.6, 139.5, -30.0)  # generous around EP for map panning


def clip_ring(ring: list[list[float]]) -> list[list[float]] | None:
    (x0, y0, x1, y1) = BBOX
    out = [p for p in ring if x0 - 2 <= p[0] <= x1 + 2 and y0 - 2 <= p[1] <= y1 + 2]
    if len(out) < 3:
        return None
    return [[round(p[0], 4), round(p[1], 4)] for p in out]


def main():
    dest = RAW / "naturalearth" / "ne_10m_land.geojson"
    fetch(URL, dest, timeout=600)
    j = json.loads(dest.read_text(encoding="utf-8"))
    rings: list[list[list[float]]] = []
    for f in j["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                # keep rings that intersect the bbox at all
                if any(BBOX[0] <= p[0] <= BBOX[2] and BBOX[1] <= p[1] <= BBOX[3] for p in ring):
                    c = clip_ring(ring)
                    if c:
                        rings.append(c)
    out = {
        "attribution": "Land: Natural Earth (public domain). Roads: (c) OpenStreetMap contributors (ODbL).",
        "bbox": BBOX,
        "land": rings,
    }
    APP_DATA.mkdir(parents=True, exist_ok=True)
    p = APP_DATA / "basemap.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    print(f"basemap.json: {len(rings)} land rings, {p.stat().st_size/1e6:.2f} MB")
    update_manifest([dest])


if __name__ == "__main__":
    main()
