"""Phase 2: remaining bundle files.

- roads_render.json : simplified major-road polylines for the basemap overlay
- weather_{season}.json : daily climate per district (drives the harvest gate)
- sites.geojson, ports.json : copied into the bundle
- bundle size report
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from datetime import date
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, ROOT

APP_DATA = ROOT / "app" / "public" / "data"
RENDER_CLASSES = {"trunk", "primary", "secondary", "tertiary"}
SEASONS = ["2022/23", "2023/24", "2024/25", "2025/26"]
# station -> PIRSA district weighting (A6 points)
STATION_DISTRICT = {
    "cummins_lower_ep": "LEP",
    "yeelanna_lower_ep": "LEP",
    "lock_central_ep": "EEP",   # Lock sits on the EEP/WEP boundary; grouped east
    "kimba_eastern_ep": "EEP",
    "cleve_eastern_ep": "EEP",
    "wudinna_central_ep": "WEP",
    "streaky_bay_western_ep": "WEP",
    "ceduna_far_west": "WEP",
}


def simplify(points, tol=0.003):
    if len(points) < 3:
        return points

    def dp(pts):
        if len(pts) < 3:
            return pts
        (x1, y1), (x2, y2) = pts[0], pts[-1]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy) or 1e-12
        dmax, idx = 0.0, 0
        for i in range(1, len(pts) - 1):
            d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / norm
            if d > dmax:
                dmax, idx = d, i
        if dmax > tol:
            return dp(pts[: idx + 1])[:-1] + dp(pts[idx:])
        return [pts[0], pts[-1]]

    return dp(points)


def main():
    g = json.loads((PROCESSED / "roads.graph.json").read_text(encoding="utf-8"))
    lines = []
    for (u, v, L, hw), geom in zip(g["edges"], g["geometry"]):
        if hw in RENDER_CLASSES:
            s = simplify(geom)
            lines.append({"class": hw, "path": [[round(x, 4), round(y, 4)] for x, y in s]})
    rr = APP_DATA / "roads_render.json"
    rr.write_text(json.dumps({"attribution": "(c) OpenStreetMap contributors (ODbL)", "lines": lines}), encoding="utf-8")
    print(f"roads_render.json: {len(lines)} lines, {rr.stat().st_size/1e6:.2f} MB")

    clim = pl.read_parquet(PROCESSED / "climate_daily.parquet")
    clim = clim.with_columns(pl.col("station").replace_strict(STATION_DISTRICT).alias("district"))
    daily = clim.group_by("district", "date").agg(
        pl.col("rain_mm").mean().round(2),
        pl.col("tmax_c").mean().round(1),
        pl.col("rh_min_pct").mean().round(0),
        pl.col("wind_max_kmh").mean().round(0),
    ).sort("district", "date")
    for season in SEASONS:
        y = int(season[:4])
        s0, s1 = date(y, 9, 1), date(y + 1, 3, 31)
        sub = daily.filter((pl.col("date") >= s0) & (pl.col("date") <= s1))
        out: dict[str, dict] = {}
        for d in ("WEP", "LEP", "EEP"):
            dd = sub.filter(pl.col("district") == d)
            out[d] = {
                "start": dd["date"].min().isoformat(),
                "rain_mm": dd["rain_mm"].to_list(),
                "tmax_c": dd["tmax_c"].to_list(),
                "rh_min_pct": dd["rh_min_pct"].to_list(),
                "wind_max_kmh": dd["wind_max_kmh"].to_list(),
            }
        f = APP_DATA / f"weather_{season.replace('/', '-')}.json"
        f.write_text(json.dumps({"season": season, "source": "ERA5 via open-meteo (CC-BY 4.0); district mean of A6 points", "districts": out}), encoding="utf-8")
        print(f"{f.name}: {f.stat().st_size/1e3:.0f} kB")

    shutil.copy(PROCESSED / "sites.geojson", APP_DATA / "sites.geojson")
    shutil.copy(PROCESSED / "ports.json", APP_DATA / "ports.json")

    total = sum(f.stat().st_size for f in APP_DATA.glob("*.json")) + sum(
        f.stat().st_size for f in APP_DATA.glob("*.geojson")
    )
    print(f"\nbundle total: {total/1e6:.2f} MB across {len(list(APP_DATA.iterdir()))} files")
    for f in sorted(APP_DATA.iterdir()):
        print(f"  {f.name:28s} {f.stat().st_size/1e3:8.0f} kB")


if __name__ == "__main__":
    main()
