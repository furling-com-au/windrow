"""One-command pipeline regeneration (spec Phase 2).

  uv run python pipeline/build_all.py           # rebuild processed data + app bundle from raw cache
  uv run python pipeline/build_all.py --fetch   # re-run all fetch steps first (idempotent, cached)

Fetch steps are polite/idempotent; nothing in data/raw/ is ever overwritten.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

FETCH = [
    "r2_fetch_receivals.py",
    "r2b_fetch_bunge_pages.py",
    "r1_fetch_sites.py",
    "r3_fetch_ais.py",
    "r3_fetch_stems.py",
    "r3_fetch_flinders.py",
    "r4_fetch_clum.py",
    "r4_fetch_lga.py",
    "r5_fetch_climate.py",
    "r6_fetch_osm.py",
]
BUILD = [
    "r2_parse_receivals.py",
    "r3_derive_vessel_calls.py",
    "r3_parse_flinders.py",
    "r5_parse_climate.py",
    "r4_build_production.py",
    "r1_build_sites.py",
    "r6_build_roads.py",
    "r4_build_demand.py",
    "p2_build_matrix.py",
    "p2_build_observed.py",
    "p2_build_misc.py",
    "p2_stem_names.py",
]


def run(script: str) -> None:
    print(f"\n=== {script} ===", flush=True)
    r = subprocess.run([sys.executable, str(HERE / script)])
    if r.returncode != 0:
        print(f"FAILED: {script}", file=sys.stderr)
        sys.exit(r.returncode)


def main():
    steps = (FETCH if "--fetch" in sys.argv else []) + BUILD
    for s in steps:
        run(s)
    print("\npipeline complete")


if __name__ == "__main__":
    main()
