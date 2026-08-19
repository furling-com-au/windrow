"""R5: parse cached open-meteo JSON -> data/processed/climate_daily.parquet (long format)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW


def main():
    frames = []
    for f in sorted((RAW / "climate").glob("openmeteo_*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        daily = j["daily"]
        n = len(daily["time"])
        frames.append(
            pl.DataFrame(
                {
                    "station": [f.stem.replace("openmeteo_", "")] * n,
                    "date": daily["time"],
                    "rain_mm": daily["precipitation_sum"],
                    "tmax_c": daily["temperature_2m_max"],
                    "tmin_c": daily["temperature_2m_min"],
                    "wind_max_kmh": daily["wind_speed_10m_max"],
                    "gust_max_kmh": daily["wind_gusts_10m_max"],
                    "rh_mean_pct": daily["relative_humidity_2m_mean"],
                    "rh_min_pct": daily["relative_humidity_2m_min"],
                    "et0_mm": daily["et0_fao_evapotranspiration"],
                }
            ).with_columns(pl.col("date").str.to_date())
        )
    df = pl.concat(frames)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.write_parquet(PROCESSED / "climate_daily.parquet")
    print(f"rows: {df.height}, stations: {df['station'].n_unique()}, {df['date'].min()} .. {df['date'].max()}")
    # sanity: harvest-period rain days per season at Cummins
    cum = df.filter(pl.col("station") == "cummins_lower_ep")
    for y in range(2020, 2026):
        h = cum.filter((pl.col("date") >= pl.date(y, 10, 1)) & (pl.col("date") <= pl.date(y + 1, 1, 31)))
        wet = h.filter(pl.col("rain_mm") >= 5.0).height
        hot = h.filter(pl.col("tmax_c") >= 35.0).height
        print(f"season {y}/{(y+1)%100:02d}: harvest-window days={h.height}, rain>=5mm days={wet}, tmax>=35C days={hot}")


if __name__ == "__main__":
    main()
