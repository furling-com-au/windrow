# Windrow — working log & phase state

This file is the canonical record of where the project is. Updated as work proceeds.

## Phase state

- [x] **Phase 1 — Research** (COMPLETE 2026-08-19; all acceptance criteria exceeded)
  - [x] R1 sites → `data/processed/sites.geojson` (32 features; 23 operator facility-grade coords via live API; OSM silo cross-check ≤200 m for most)
  - [x] R2 receivals → `receivals_weekly.parquet` (**10 seasons** 2016/17–2025/26, 128 archived reports, 0 missing; digit-exact vs Grain Central for 3 seasons) + `receivals_monthly.parquet` + `receivals_notes.jsonl`
  - [x] R3 vessels → `vessel_calls.parquet` (31 months AIS; 190 PL berth visits, median 55 h; validated ±1-2/mo vs Flinders official Dry Bulk counts) + `ais_ep_points.parquet` + `port_shipments_monthly.parquet` + `port_vessel_calls_monthly.parquet` + 53 archived stem PDFs + 22 T-Ports stems + PortMIS capture
  - [x] R4 production → `production_districts.parquet` (4 seasons × 3 EP districts × 12 crops; PDF spot-verification passes) + CLUM 50 m raster cached (clip in Phase 2)
  - [x] R5 climate → `climate_daily.parquet` (8 points, 2020-09→2026-02; ERA5 via open-meteo — see ASSUMPTIONS A6 for SILO deviation)
  - [x] R6 roads/trucks → `roads.graph.json` (9,320 nodes/12,566 edges; Cummins→PL 62.7 km ✓) + `data/trucks.md` (GTSN masses, payload assumptions)
  - [x] R7 ports → `data/processed/ports.json` (per-value citations; PL 3,000 t/h + 395.6 kt verified)
  - [x] R8 `data/CALIBRATION.md` complete (targets + tolerances + quirks)
  - [x] `SOURCES.md` (14 sources + rejected list), `ASSUMPTIONS.md` (A1–A13)
- [x] **§9 operator answers (2026-08-19)**: seasons 2023/24–2025/26 with drought 2024/25 held out & visible for comparison · district-level demand OK · **public deploy on Cloudflare** · no paid data
- [x] Phase 2 — Data pipeline → `app/public/data/` bundle (4.9 MB total: parcels+demand, cluster matrix + route polylines, observed overlays, AIS vessel schedules w/ stem names, weather, self-contained basemap). One command: `uv run python pipeline/build_all.py`
- [x] Phase 3 — Sim core (`packages/sim/`): 5-min tick, sfc32 seeded, mass-conservation invariants, 3 unit tests, full season in ~0.8 s headless. Calibrated: 9 knobs, random search + refine (313 s, deterministic), fitted on 2023/24+2025/26
- [x] Phase 4 — Browser app: Svelte 5 + deck.gl standalone (no tile server), sim in Web Worker, KPI strip, sim-vs-observed money chart, 7 scenarios, port panels, About/attribution. Build 222 kB gz. Playwright happy-path passes
- [x] Phase 5 — `docs/calibration_report.md` (+SVG charts), `docs/scenarios.md`, README
- [x] **DEPLOYED: https://windrow.justinjywong.workers.dev** (Cloudflare Workers static assets, `npx wrangler deploy`)

## Validation headline (see docs/calibration_report.md)

- Held-out 2024/25: season total **−1.9 %** (spec ±5 % ✓); weekly RMSE 65 % of mean weekly
  (timing-dominated; the late-Nov 2024 rain collapse is missing from ERA5 at the A6
  points — documented). Vessel counts = AIS schedule by construction.
- 2023/24 +0.7 %, 2025/26 −2.5 % (calibration seasons).
- 2022/23 bumper replays at −31 % (outside calibrated fleet envelope; excluded from UI).

## Phase 1 acceptance criteria — status

| Criterion | Required | Achieved |
|---|---|---|
| Seasons of weekly receivals parsed + cross-checked | ≥3 | **10** (3 digit-exact cross-checks) |
| Receival sites geocoded w/ provenance | ≥12 | **32** (23 facility-grade) |
| Seasons of AIS vessel calls w/ berth durations | ≥1 | **~3** (Oct 2023–May 2026) |
| Seasons of district production | ≥3 | **4** |
| Registers complete | yes | yes |

## Key numbers (see data/CALIBRATION.md for full tables)

- Western region harvest receivals: 2023/24 = 1,864,175 t · 2024/25 = 1,507,275 t · 2025/26 = 2,249,112 t (2.34 Mt incl. post-harvest)
- Port Lincoln grain shipped (Flinders official): 2022/23 = 1.76 Mt · 2023/24 = 1.43 Mt · 2024/25 = 1.12 Mt · 2025/26 = 1.54 Mt (to Jul)
- PL berth visits (AIS): 86 / 53 / 51 per shipping year; median stay 53–63 h; Sept = maintenance shutdown (~0 calls)
- Lucky Bay: 0 ocean-vessel berth visits (transshipment-only confirmed); ~15 long anchorage stays/season

## Worklog

### 2026-08-19 (Phase 1, single day)
- Env: Python 3.12/uv, Node 24, git init. 4 research agents (sites, trucks+ports, cross-checks, shipping-source scout) + 1 later (PIRSA/CLUM).
- Key discoveries: viterra.com.au → bunge.com.au migration (Wayback required); Jan-2026 listing snapshot enumerates ALL weekly reports to 2016; AODN cloud-optimised AMSA parquet (45 MB/mo vs 300+ MB zips) with per-vessel craftID + draught; live operator sites API with facility coords; Flinders monthly XLSX = per-port grain tonnes + vessel calls (official calibration series); stem PDFs text-extractable with completed-loading timestamps.
- Data quirks handled: AMSA Feb–Apr 2024 half-day coverage (16 h visit merge); May 2024 `_Pt` case; Flinders 3 workbook layouts + duplicate Copy-of/V2 files; Overpass 406 on "crawler" UAs; several hosts 403 non-browser TLS (curl fallback); WebFetch blocked for web.archive.org (curl).
- All fetch scripts idempotent; raw cache 1.6 GB, 398+ files hashed in MANIFEST.sha256.

## Key decisions

- Repo root = `C:\Users\justi\grain_simulation` (spec layout §10). `data/raw/` git-ignored, manifest committed.
- Seasons ids like `2023/24`; marketing year Oct 1–Sep 30; Windrow calibrates on **Western region** (EP-only; network totals include some Vic sites).
- AIS via AODN parquet product (licence: AODN says CC-BY 4.0, AMSA source says CC BY-NC 3.0 AU → treat as NC; project is non-commercial research).
- Climate via ERA5/open-meteo (SILO needs identifying email; upgrade path in A6).
- Roads graph from OSM Overpass (ODbL); routable; travel-time matrix in Phase 2.

## Blockers / open questions for operator (§9 — asked 2026-08-19)

1. Season priority (recommend calibrate 2023/24 + 2025/26, hold out 2024/25; 2016/17–2022/23 available as replay-only).
2. District-level demand OK for v1? (recommend yes; CLUM-pixel disaggregation)
3. Deployment: static Caddy LAN only, or public too (affects tile choice)?
4. ePaddocks paid data: skip (recommend) or budget?
