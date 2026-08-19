# Calibration Register — Windrow (R8)

Every observable the simulation must reproduce, with source and tolerance. "Season" =
marketing year 1 Oct–30 Sep. Windrow models the **Western region** (EP + far west) of the
Bunge (ex-Viterra) network plus the T-Ports Lucky Bay system.

All observed series live in `data/processed/`; regeneration: `pipeline/*.py` (see README).

## Primary target — weekly Western-region receivals curve

Source: operator weekly harvest reports, parsed from 128 Wayback-archived pages
(`receivals_weekly.parquet`, 10 seasons 2016/17–2025/26, weekly + cumulative, four region
rows each). Spot-validated to the tonne against Grain Central re-publications for
2022/23, 2024/25, 2025/26 (see notes below).

**Acceptance (from project spec):** held-out season weekly Western receivals within
±15 % weekly RMSE band; season total within ±5 %; vessel calls within ±10 %.

### Season anchor values (harvest-window cumulative, tonnes)

| Season | Network total | Western | Central | Eastern | Weekly reports |
|---|---|---|---|---|---|
| 2016/17 | 8,915,725 | 3,210,369 | 4,005,643 | 1,699,713 | 14 |
| 2017/18 | 5,394,958 | 1,491,641 | 2,624,661 | 1,278,656 | 14 |
| 2018/19 | 3,758,161 | 1,820,684 | 1,512,362 | 425,115 | 11 |
| 2019/20 | 3,621,169 | 1,517,124 | 1,606,650 | 632,281 | 11 |
| 2020/21 | 5,800,852 | 1,755,138 | 2,515,016 | 1,530,698 | 14 |
| 2021/22 | 5,644,875 | 1,986,890 | 2,568,999 | 1,088,986 | 12 |
| 2022/23 | 8,725,162 | 3,266,811 | 3,634,003 | 1,824,348 | 15 |
| 2023/24 | 5,411,487 | 1,864,175 | 2,238,385 | 1,308,927 | 13 |
| 2024/25 | 3,239,644 | 1,507,275 | 1,136,660 | 595,709 | 11 |
| 2025/26 | 5,325,317 | 2,249,112 | 2,162,991 | 913,214 | 12 |

Season-inclusive (post-harvest) maxima from monthly reports: 2024/25 total 3,334,592 /
Western 1,537,465; 2025/26 total 5,653,871 / Western 2,338,257.

Cross-checks (independent publications):
- 2022/23 total 8,725,162 & Western 3,266,811 — identical in Grain Central 31 Jan 2023.
- 2024/25 total 3,239,644 & Western 1,507,275 — identical in Grain Central 13 Jan 2025.
- 2025/26 total 5,325,317 & Western 2,249,112 — identical in Australian Bulk Handling
  Review, Jan 2026. (Confirms the spec's "~2.25 Mt Western 2025/26".)
- 2023/24 Western 1,864,175 t fills a value not found in any live news source (only
  "1.83 Mt at 10 Dec 2023" was still published) — recovered from the archived
  week-ending-31-Dec-2023 report.

Caveats: "network total" includes a few western-Victorian sites (Eastern region);
Western is EP-only, which is why Windrow calibrates on Western. Fortnight reports
(Christmas) carry `report_kind="fortnight"`; treat weekly_t as a 2-week sum.

## Port Lincoln shipped tonnage (per shipping year)

Source: Flinders Port Holdings monthly statistics, Bulk Break sheets, grain reporting
group (`port_shipments_monthly.parquet`; 2022–2026 by commodity, 2022–2023 as
"(all grain)" only). Tolerance: ±5 % season, ±15 % monthly profile shape.

| Shipping year | Port Lincoln grain exports (t) | Independent check |
|---|---|---|
| 2021/22 (from Jan 2022 only) | 1,156,500 (partial) | — |
| 2022/23 | 1,761,500 | Viterra: "1.8 Mt loaded at Port Lincoln" to Jul 2023 ✓ |
| 2023/24 | 1,432,700 | Viterra: EP ports (PL+Thevenard) 1.7 Mt to Jun 2024 ✓ |
| 2024/25 | 1,118,500 | Viterra: ">900,000 t" (mid-season statement) ✓ |
| 2025/26 (to Jul 2026) | 1,543,000 | Bunge: ">1 Mt from Port Lincoln" by Apr 2026 ✓ |

Monthly shape target: strong Dec–Mar peak (e.g. Dec 2025: 289,387 t), winter tail,
**September ≈ 0 (annual maintenance shutdown; stem shows Pt Lincoln closed 1–30 Sep 2026;
AIS shows 0–1 berth visits each Aug–Oct)**.

## Vessel calls at Port Lincoln

Two independent series (`vessel_calls.parquet` from AIS; `port_vessel_calls_monthly.parquet`
from Flinders "Vessel Calls" sheets, class "Dry Bulk"). Monthly agreement between the two
is ±1–2 calls throughout (AIS additionally counts tankers/other cargo). Tolerance: ±10 %
on season count, per spec.

| Shipping year | AIS cargo berth visits | Median berth stay (h) |
|---|---|---|
| 2023/24 | 86 | 52.9 |
| 2024/25 | 53 | 56.1 |
| 2025/26 (to May) | 51 | 62.9 |

Berth-stay distribution: median ~55 h, mean ~60 h — consistent with the published
"~75,000 t vessel loadable in ~3 days" at 3,000 t/h.
Anchorage stays (Boston Bay area): 186 over 31 months, median 26.8 h (upper bound on
pre-berth waiting; includes non-berthing anchor calls — refine in Phase 2 by linking
anchor→berth sequences per craftID).
Lucky Bay: 0 berth visits by ocean vessels (transshipment-only, as expected); 40
anchorage stays > 24 h in 31 months (~15/season) — matches T-Ports scale (~20 shipments
in 15 months per ACCC).

## Production ceiling (per district)

`production_districts.parquet` (PIRSA Crop and Pasture Reports, 4 seasons; spot-verified
verbatim against cached PDFs). EP grain production (t):

| Season | Western EP | Lower EP | Eastern EP | EP total |
|---|---|---|---|---|
| 2022/23 | 1,434,100 | 1,313,150 | 1,402,250 | 4,149,500 |
| 2023/24 | 729,360 | 1,083,300 | 775,800 | 2,588,460 |
| 2024/25 | 408,369 | 907,500 | 573,350 | 1,889,219 |
| 2025/26 | 733,808 | 1,143,700 | 1,029,425 | 2,906,933 |

Constraint: simulated harvest tonnage per season ≤ EP production; Western-region
receivals / EP production ratio observed ≈ 0.77–0.80 (2025/26: 2.34 / 2.91), residual =
on-farm retention + T-Ports intake + domestic/container — a calibration parameter.

## Harvest timing & dynamics

- First receival dates: 2022/23 = 11 Oct (Port Pirie); 2023/24 = **25 Sep** (Thevenard;
  earliest on record); 2024/25 = 10 Oct (Thevenard); 2025/26 = 13 Oct (Thevenard,
  lentils). Sim: first Western deliveries mid-Oct ±1 week (lentils/barley lead).
- Peak-week: statewide records 1.35 Mt (w/e 4 Dec 2022), 1.25 Mt (w/e 14 Dec 2025;
  Western share 486,931 t). Biggest days > 200–250 kt statewide; Port Lincoln site
  record 13,675 t/day (2022/23).
- Harvest effectively complete by mid-late January every season (weekly reporting stops
  first week of Jan in recent seasons).
- Weather pauses: `climate_daily.parquet` (8 EP points, 2020–2026). Rain days ≥5 mm in
  the Oct–Jan window range 5 (2024/25 drought) to 14 (2022/23) at Cummins; sim's
  weather-gated harvest model must reproduce receival dips after such events.

## Commodity mix (Western region)

From PIRSA district tables (above) + report narratives: wheat ~50–60 % of Western
tonnes, barley ~20–25 %, lentils rising strongly (75,000 ha WEP by 2025/26), canola
mostly Lower EP, faba beans minor (Tumby Bay/Yeelanna/Kapinnie segregations). Sequence:
lentils/barley first (far-west starts), wheat dominates Nov–Dec peak, canola mid-Dec on
lower EP. Tolerance: qualitative ordering + ±10 pp on shares.

## Known upstream data quirks (affect calibration windows)

1. AMSA CTS Feb–Apr 2024 files contain only ~half of each UTC day (positions 01:00–12:30)
   — berth visits were merged across ≤16 h gaps to compensate; treat arrival/departure
   times in those months as ±8 h.
2. CTS positions are thinned to ≥60-min per vessel; all berth timings ±1 h.
3. May 2024 CTS file is present upstream but named `_Pt` (case) — handled.
4. 2019/20 and 2018/19 weekly series are 11 weeks (drought-shortened harvests).
5. Weekly network totals include western-Vic sites; use Western region only.
6. Flinders monthly workbooks change layout twice (2024-05→06 narrow switch;
   sheet renamed) — parser handles all three; 2021 data not published in monthly form.
