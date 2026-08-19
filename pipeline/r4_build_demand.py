"""R4/Phase 2: build harvest-demand parcels from CLUM cropping land x PIRSA district totals.

Steps:
 1. Read CLUM 50 m raster (from inside the zip) windowed to the EP bbox.
 2. Mask to dryland-cropping ALUM classes (330-338).
 3. Aggregate to ~2.5 km cells (50 x 50 px) -> cropping_ha per cell.
 4. Assign cells to PIRSA districts via LGA polygons (mapping = ASSUMPTIONS A14);
    unassigned far-west cropping cells (unincorporated SA, west of Ceduna LGA) -> WEP.
 5. Validate: per-district cropping_ha vs PIRSA sown area (prints ratios).
 6. Allocate district x crop production (production_districts.parquet) to cells
    proportional to cropping_ha -> app/public/data/parcels.json + demand_{season}.json.

Commodity grouping: wheat, barley, canola, lentils, beans (faba), other
(oats+triticale+peas+lupins+chickpeas+vetch).
"""
from __future__ import annotations

import json
import math
import os
import sys
import zipfile
from pathlib import Path

# A PostgreSQL/PostGIS install on this machine exports an old PROJ database via
# PROJ_LIB, which breaks rasterio's bundled PROJ. Point PROJ/GDAL at the wheel's data.
_pkg = Path(__file__).resolve().parents[1] / ".venv" / "Lib" / "site-packages" / "rasterio"
for _var, _sub in (("PROJ_LIB", "proj_data"), ("PROJ_DATA", "proj_data"), ("GDAL_DATA", "gdal_data")):
    _p = _pkg / _sub
    if _p.exists():
        os.environ[_var] = str(_p)

import numpy as np
import polars as pl
import rasterio
from rasterio.warp import transform as rio_transform
from rasterio.warp import transform_bounds
from shapely.geometry import Point, shape
from shapely.prepared import prep
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW, ROOT

APP_DATA = ROOT / "app" / "public" / "data"
BBOX = (131.0, -35.3, 137.8, -31.0)  # lon/lat EP + far west
CROPPING_CLASSES = set(range(330, 339))
CELL_PX = 50  # 50 x 50m = 2.5 km cells

# ASSUMPTIONS A14: PIRSA EP district composition by LGA (validated against sown areas below)
LGA_DISTRICT = {
    "CITY OF PORT LINCOLN": "LEP",
    "LOWER EYRE PENINSULA": "LEP",
    "TUMBY BAY": "LEP",
    "CLEVE": "EEP",
    "FRANKLIN HARBOUR": "EEP",
    "KIMBA": "EEP",
    "WUDINNA": "WEP",
    "ELLISTON": "WEP",
    "STREAKY BAY": "WEP",
    "CEDUNA": "WEP",
}
CROP_GROUPS = {
    "wheat": ["wheat"],
    "barley": ["barley"],
    "canola": ["canola"],
    "lentils": ["lentils"],
    "beans": ["beans"],
    "other": ["oats", "triticale", "peas", "lupins", "chickpeas", "vetch"],
}


def load_lgas():
    lga_dir = RAW / "sa_lga"
    gj_files = list(lga_dir.glob("*.geojson")) + list(lga_dir.glob("*.json"))
    gj_files = [f for f in gj_files if not f.name.endswith(".zip")]
    j = json.loads(gj_files[0].read_text(encoding="utf-8"))
    feats = j["features"]
    name_key = None
    for k in feats[0]["properties"]:
        if "name" in k.lower():
            name_key = k
            break
    polys, districts = [], []
    for f in feats:
        nm = str(f["properties"].get(name_key, "")).upper()
        for lga, dist in LGA_DISTRICT.items():
            if lga in nm or nm in lga:
                polys.append(shape(f["geometry"]))
                districts.append(dist)
                break
    print(f"LGA polygons matched: {len(polys)}/{len(LGA_DISTRICT)} (name key: {name_key})")
    return polys, districts


def main():
    # 1-2: CLUM window + cropping mask
    zpath = RAW / "abares_clum" / "clum_50m_2023_v2.zip"
    with zipfile.ZipFile(zpath) as z:
        tifs = [n for n in z.namelist() if n.lower().endswith((".tif", ".tiff"))]
    print("tifs in zip:", tifs)
    vsipath = f"zip://{zpath.as_posix()}!{tifs[0]}"
    with rasterio.open(vsipath) as src:
        print("CRS:", src.crs, "size:", src.width, "x", src.height)
        l, b, r, t = transform_bounds("EPSG:4326", src.crs, *BBOX)
        win = rasterio.windows.from_bounds(l, b, r, t, src.transform)
        win = win.round_offsets().round_lengths()
        arr = src.read(1, window=win)
        wtransform = src.window_transform(win)
        crs = src.crs
    print("window shape:", arr.shape)
    vals, counts = np.unique(arr[np.isin(arr, list(CROPPING_CLASSES))], return_counts=True)
    print("cropping classes present:", dict(zip(vals.tolist(), counts.tolist())))
    mask = np.isin(arr, list(CROPPING_CLASSES))
    print(f"cropping pixels: {mask.sum():,} (= {mask.sum()*0.25/1e6:.2f} Mha)")

    # 3: aggregate to cells
    H, W = mask.shape
    ch, cw = H // CELL_PX, W // CELL_PX
    trimmed = mask[: ch * CELL_PX, : cw * CELL_PX]
    cells = trimmed.reshape(ch, CELL_PX, cw, CELL_PX).sum(axis=(1, 3))  # px count per cell
    ys, xs = np.nonzero(cells > 160)  # >40 ha cropping per 2.5 km cell
    print(f"cells with >40 ha cropping: {len(ys):,}")

    # cell centroids in raster CRS -> lon/lat
    cxs = [wtransform.c + wtransform.a * (x * CELL_PX + CELL_PX / 2) for x in xs]
    cys = [wtransform.f + wtransform.e * (y * CELL_PX + CELL_PX / 2) for y in ys]
    lons, lats = rio_transform(crs, "EPSG:4326", cxs, cys)

    # 4: district assignment
    polys, districts = load_lgas()
    prepared = [prep(p) for p in polys]
    cell_district = []
    for lon, lat in zip(lons, lats):
        pt = Point(lon, lat)
        d = None
        for pp, dist in zip(prepared, districts):
            if pp.contains(pt):
                d = dist
                break
        if d is None and lon < 134.7 and lat > -33.2:
            d = "WEP"  # unincorporated far west cropping strip
        cell_district.append(d)

    keep = [i for i, d in enumerate(cell_district) if d is not None]
    print(f"cells assigned to EP districts: {len(keep):,} (dropped {len(ys)-len(keep):,} outside EP)")

    parcels = []
    for i in keep:
        parcels.append(
            {
                "id": len(parcels),
                "lon": round(lons[i], 4),
                "lat": round(lats[i], 4),
                "district": cell_district[i],
                "cropping_ha": round(float(cells[ys[i], xs[i]]) * 0.25, 1),
            }
        )

    # 5: validation vs PIRSA sown areas
    prod = pl.read_parquet(PROCESSED / "production_districts.parquet")
    sown = prod.filter((pl.col("crop") == "TOTAL")).group_by("district").agg(pl.col("area_ha").max().alias("max_sown_ha"))
    by_d = {}
    for p in parcels:
        by_d[p["district"]] = by_d.get(p["district"], 0.0) + p["cropping_ha"]
    print("\ndistrict validation (CLUM cropping vs PIRSA max sown):")
    for d in ("WEP", "LEP", "EEP"):
        srow = sown.filter(pl.col("district") == d)
        s = srow["max_sown_ha"][0] if srow.height else None
        c = by_d.get(d, 0)
        print(f"  {d}: CLUM {c:,.0f} ha | PIRSA max sown {s:,.0f} ha | ratio {c/s:.2f}")

    # 6: per-season demand
    APP_DATA.mkdir(parents=True, exist_ok=True)
    (APP_DATA / "parcels.json").write_text(json.dumps({"parcels": parcels}), encoding="utf-8")
    seasons = ["2022/23", "2023/24", "2024/25", "2025/26"]
    dist_ha = by_d
    for season in seasons:
        sp = prod.filter((pl.col("season") == season) & (pl.col("crop") != "TOTAL"))
        if sp.height == 0:
            continue
        # district x group production
        dg: dict[tuple[str, str], float] = {}
        for row in sp.iter_rows(named=True):
            grp = next((g for g, crops in CROP_GROUPS.items() if row["crop"] in crops), "other")
            key = (row["district"], grp)
            dg[key] = dg.get(key, 0.0) + float(row["production_t"])
        demand = []
        for p in parcels:
            w = p["cropping_ha"] / dist_ha[p["district"]]
            crops = {}
            for (d, g), t in dg.items():
                if d == p["district"] and t > 0:
                    v = round(t * w, 1)
                    if v >= 1:
                        crops[g] = v
            demand.append({"id": p["id"], "crops": crops})
        total = sum(v for d in demand for v in d["crops"].values())
        fname = f"demand_{season.replace('/', '-')}.json"
        (APP_DATA / fname).write_text(json.dumps({"season": season, "parcels": demand}), encoding="utf-8")
        print(f"{fname}: {len(demand)} parcels, {total/1e6:.3f} Mt ({(APP_DATA/fname).stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
