# Windrow — working log & phase state

This file is the canonical record of where the project is. Updated as work proceeds.

## Phase state

- [ ] **Phase 1 — Research** (in progress, started 2026-08-19)
  - [ ] R1 receival sites → `data/processed/sites.geojson` (research agent running)
  - [ ] R2 weekly receivals ≥3 seasons → `data/processed/receivals_weekly.parquet`
  - [ ] R3 shipping stem + AMSA CTS AIS + vessel calls → `data/processed/vessel_calls.parquet` (scout agent running)
  - [ ] R4 CLUM land use + district production → `data/processed/production_districts.parquet`
  - [ ] R5 SILO climate 4–6 stations → `data/processed/climate_daily.parquet`
  - [ ] R6 OSM roads + truck params → `data/processed/roads.graph` + `trucks.md` (truck research agent running)
  - [ ] R7 port physics → `data/processed/ports.json` (port research agent running)
  - [ ] R8 `data/CALIBRATION.md`
- [ ] Ask operator the §9 open questions (REQUIRED before Phase 2)
- [ ] Phase 2 — Data pipeline → `app/public/data/` bundle
- [ ] Phase 3 — Sim core (`packages/sim/`)
- [ ] Phase 4 — Browser app (`app/`)
- [ ] Phase 5 — Validation, scenarios, write-up

## Phase 1 acceptance criteria

- ≥ 3 seasons weekly receivals parsed + cross-checked
- ≥ 12 receival sites geocoded with provenance
- ≥ 1 season AIS-derived vessel calls at Port Lincoln w/ berth durations
- District production estimates ≥ 3 seasons
- SOURCES.md / ASSUMPTIONS.md / CALIBRATION.md complete

## Worklog

### 2026-08-19
- Env verified: Python 3.12.6, uv 0.8.15, Node 24.18, git. 44 GB disk free.
- Repo skeleton created; git init.
- **Key finding**: `viterra.com.au` 302-redirects to `bunge.com.au` (e.g. `/media/Receivals-reports`
  → `bunge.com.au/Media/News`). Domain migration complete; historical archives via Wayback Machine.
- 4 research agents launched: R1 sites, R6/R7 trucks+ports, season cross-checks, R3 source scout.

## Key decisions

- Repo root = `C:\Users\justi\grain_simulation` (layout per spec §10).
- `data/raw/` git-ignored; sha256 manifest committed instead.
- Season naming: `2023-24` style ids; Viterra regions Western/Central/Eastern; Windrow models Western.

## Blockers / open questions for operator (§9 — ask before Phase 2)

1. Season priority (suggest 2023/24–2025/26, hold out 2024/25).
2. District-level demand OK for v1?
3. Deployment = static behind Caddy on LAN? Public hosting?
4. Paid ePaddocks appetite?
