"""R5: daily climate for EP cropping districts, seasons 2020/21 -> 2025/26.

Source: open-meteo.com historical archive API (ERA5-family reanalysis; CC-BY 4.0,
no key required). NOTE: the project spec suggested SILO/BOM point data; SILO's API
requires an email identifier which this autonomous run does not supply, so ERA5
reanalysis at district points is used instead. Recorded in ASSUMPTIONS.md with an
upgrade path (swap in SILO patched-point once an operator email is provided).

Purpose: derive "harvestable day" windows (rain events, extreme heat, high RH
mornings) that explain pauses in weekly receivals.

Output: data/raw/climate/openmeteo_<name>.json (immutable cache)
        -> parsed later into data/processed/climate_daily.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, fetch, update_manifest

# Representative district points (town coordinates, approximate — provenance: OSM town
# locations, precision "district representative", NOT receival-site coordinates).
POINTS = {
    "cummins_lower_ep": (-34.264, 135.729),
    "yeelanna_lower_ep": (-34.141, 135.727),
    "lock_central_ep": (-33.568, 135.756),
    "wudinna_central_ep": (-33.046, 135.461),
    "kimba_eastern_ep": (-33.140, 136.417),
    "cleve_eastern_ep": (-33.699, 136.492),
    "streaky_bay_western_ep": (-32.796, 134.209),
    "ceduna_far_west": (-32.127, 133.673),
}

# The archive endpoint lags real time by a few days (ERA5T); END is bumped by hand when
# the series is refreshed, and each window is cached under its own filename so nothing in
# data/raw/ is overwritten. r5_parse_climate.py keeps the latest window per station.
START, END = "2020-09-01", "2026-08-27"

URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}"
    "&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,"
    "wind_speed_10m_max,wind_gusts_10m_max,relative_humidity_2m_mean,"
    "relative_humidity_2m_min,et0_fao_evapotranspiration"
    "&timezone=Australia%2FAdelaide"
)


def main():
    out = RAW / "climate"
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for name, (lat, lon) in POINTS.items():
        dest = out / f"openmeteo_{name}__to{END}.json"
        url = URL.format(lat=lat, lon=lon, start=START, end=END)
        data = fetch(url, dest, timeout=180)
        status = "cached" if data is None else f"{len(data)/1e3:.0f} kB"
        print(f"{name}: {status}")
        saved.append(dest)
    update_manifest(saved)


if __name__ == "__main__":
    main()
