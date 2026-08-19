# Assumptions Register — Windrow

Every value used by the model that is **not** backed by a published source, with
reasoning. Data files mark these `"provenance": "assumed"`. Simulated outputs are never
presented as measured data.

## A1 — truck net payloads per configuration
- **Value**: semi-trailer 28 t; 9-axle B-double 42 t; A-double road train 55 t;
  AB-triple 68 t (net grain tonnes).
- **Used in**: truck agents (Phase 3 params).
- **Reasoning**: GTSN publishes gross combination masses only (42.5–110 t); tares are not
  published. Net ≈ 62–66 % of GCM matches the two published anchors: AEGIC "72 t load
  size on EP" (≈ AB-triple at HML 107.5 t ⇒ tare ~35 t) and SA average delivered load
  >29 t in 2016-17 (mixed fleet incl. farm semis).
- **Sensitivity**: linear on truck counts; fleet size is a calibrated free parameter, so
  payload error is partly absorbed by calibration.
- **Upgrade path**: operator turnaround/weighbridge data; truck-spec tare sheets.

## A2 — receival site service times
- **Value**: sample + weigh + tip cycle 12 min/truck/bay baseline; sites have 2 tipping
  bays (4 at Port Lincoln, per its 14 hoppers & 4,000 t/h intake).
- **Reasoning**: not published anywhere in minutes. Bounded by physics: Port Lincoln site
  record 13,512 t/day ⇒ at ~40 t avg load ≈ 340 trucks/day ≈ 24/h over 14 h. A 12-min
  cycle × multiple bays reproduces observed records. The 4-hour 2018 anecdote is
  congestion queueing, not service time.
- **Sensitivity**: drives queue lengths at peak — a headline output; must be marked
  assumed in UI tooltips.
- **Upgrade path**: operator site-cycle statistics (Viterra used to publish average site
  turnaround minutes in some harvest communications — none found archived).

## A3 — farm→site assignment geography
- **Value**: demand generated on CLUM cropping pixels, disaggregated from PIRSA district
  totals; each parcel's farm→site distance emerges from geography (no assumed constant).
- **Reasoning**: no published farm→site distances exist; only site→port (~144 km SA avg).
  District-level disaggregation is the spec's accepted v1 approach (pending operator
  answer to §9 Q2).
- **Sensitivity**: affects truck-km, not tonnage balances.

## A4 — upcountry site storage capacities (Bunge, EP)
- **Value**: per-site capacity allocated proportional to long-run district receivals,
  scaled so Western upcountry total ≈ 2.5 Mt (network Western max harvest 3.27 Mt minus
  port storage 0.73 Mt, rounded).
- **Reasoning**: individual EP site capacities are not published; even ACCC redacted
  Viterra's EP storage total ("[c-i-c]"). Published anchors: Port Lincoln 395,600 t,
  Thevenard 335,925 t, T-Ports Lucky Bay 384,000 t / Lock 140,000 t / Kimba 150,000 t.
- **Sensitivity**: matters only when sites fill (bumper scenarios); mark clearly.
- **Upgrade path**: operator data; or per-site bunker/silo footprint digitisation from
  aerial imagery.

## A5 — road speeds by class (loaded grain truck)
- **Value**: trunk/primary 90 km/h, secondary 80, tertiary 70, unclassified 60,
  residential 40; ±0 for empty legs (same).
- **Reasoning**: SA road-train limit 100 km/h (Eyre Hwy) / 90 km/h elsewhere (2011 DTEI
  guide, historical); loaded B-doubles practically cruise below limits on rural seal.
- **Sensitivity**: linear on cycle times; absorbed partly by fleet-size calibration.

## A6 — climate source: ERA5 (open-meteo) instead of SILO/BOM point data
- **Value**: daily rain/tmax/RH/wind at 8 district points from the open-meteo ERA5
  archive (CC-BY 4.0).
- **Reasoning**: SILO's API requires an identifying email; none could be supplied in an
  autonomous run. ERA5 reproduces the harvest-relevant signal (multi-day rain events,
  heat days) at district scale.
- **Sensitivity**: harvest-pause timing ±1 day vs station obs; acceptable for weekly
  calibration.
- **Upgrade path**: swap in SILO patched-point (same schema) when an operator email is
  provided — single fetch script change (`pipeline/r5_fetch_climate.py`).

## A7 — harvestable-day rule (to be calibrated in Phase 3)
- **Value** (initial): a day is non-harvestable if rain_mm ≥ 5 on the day, or ≥ 10 over
  the prior 2 days; daily harvestable fraction reduced 25 % when tmax ≥ 38 °C (harvest
  bans / grower behaviour); commodity-specific ramp per calibration.
- **Reasoning**: standard industry heuristics (GRDC harvest-management guidance
  discusses rain/humidity delays qualitatively); exact thresholds are free parameters
  fitted to the weekly receivals dips.

## A8 — AIS berth-visit derivation parameters
- **Value**: berth geofence = 400 m around the empirically-clustered berth point
  (-34.7155, 135.8700); stationary = ≤0.5 kn; visits merged across gaps ≤16 h; minimum
  visit 3 h / 2 pings; anchorage = stationary ≥1.5 km from berth within zone.
- **Reasoning**: berth cluster contains 7,746 stationary cargo pings; 16 h merge
  compensates the Feb–Apr 2024 half-day data gaps; monthly totals then agree ±1–2 with
  Flinders' official Dry Bulk call counts.
- **Sensitivity**: ±1 visit/month at margins; validated against official counts.

## A9 — direct-to-port share prior
- **Value**: 25 % of receivals direct to port (calibration prior, range 15–35 %).
- **Reasoning**: ESCOSA 2019: "~75 % of Viterra receivals go to upcountry sites". EP has
  a large port-adjacent catchment (lower EP), so Western share may be higher. Free
  parameter in calibration.

## A10 — Thevenard vessel calls: grain share
- **Value**: grain vessels at Thevenard identified by month-weighting AIS calls with
  Flinders' Thevenard monthly grain tonnage (port also ships gypsum/salt/mineral sands,
  which dominate call counts).
- **Reasoning**: AIS cannot distinguish cargo; Flinders Bulk Break gives the grain
  tonnes; grain-vessel count ≈ tonnes / typical parcel (~10–30 kt at 9.8 m draft).

## A11 — T-Ports inland site coordinates
- **Value**: town coordinates (Lock, Kimba); exact pads unpublished (Kimba pad is "east
  of the township").
- **Sensitivity**: ≤ 5 km error on two closed-in-2025/26 sites; negligible for v1.

## A12 — season site sets
- **Value**: baseline network = the 18 active 2025/26 Bunge sites + 3 T-Ports sites;
  earlier seasons re-enable dormant sites (Penong, Nunjikompita, Darke Peak, Buckleboo,
  Elliston) when named in that season's reports (site-mention extraction from report
  narratives), else keep 2025/26 set.
- **Reasoning**: per-season official site lists aren't archived in machine-readable
  form; ACCC records 21 EP upcountry sites in 2020-21, 25 in 2019-20.
- **Sensitivity**: small re-routing effects in early seasons.

## A14 — PIRSA district boundaries approximated by LGA composition
- **Value**: WEP = Ceduna + Streaky Bay + Elliston + Wudinna (+ unincorporated far-west
  cropping strip); EEP = Kimba + Cleve + Franklin Harbour; LEP = Lower Eyre Peninsula +
  Tumby Bay + City of Port Lincoln. LGA polygons: data.sa.gov.au (CC-BY).
- **Used in**: `pipeline/r4_build_demand.py` (district assignment of demand cells).
- **Reasoning**: PIRSA does not publish machine-readable district boundaries. Validation
  against PIRSA sown areas: LEP ratio 1.04 (excellent), EEP 1.29, WEP 2.14 — WEP's CLUM
  cropping mask includes large opportunistically-sown marginal country, consistent with
  PIRSA sowing about half of WEP arable in a given year; allocation is proportional so
  totals are conserved exactly.
- **Sensitivity**: shifts tonnage between adjacent border cells only.

## A15 — T-Ports Lock/Kimba bunkers not operated in 2024/25
- **Value**: T-Ports inland bunker sites closed in the sim for 2024/25 (and 2025/26,
  which IS documented).
- **Reasoning**: 2025/26 closure is published (tports.com/harvest). 2024/25 is
  unverified; with WEP+EEP production at drought lows (0.41 + 0.57 Mt) and the observed
  Bunge Western share at 79.8 % of EP production, material T-Ports inland intake is
  arithmetically implausible.
- **Sensitivity**: without this, the sim under-delivers Bunge receivals ~8-10 % in
  2024/25.
- **Upgrade path**: T-Ports/operator confirmation of 2024/25 site operations.

## A16 — AIS-derived Lucky Bay vessel counts are an upper bound
- **Value**: "Lucky Bay anchorage stays" in `vessel_calls.parquet` (>24 h, cargo class)
  include vessels anchored in western Spencer Gulf for other reasons (e.g. awaiting
  Whyalla berths); they are not used as a calibration anchor.
- **Used in**: vessels_{season}.json (LB arrival schedule is indicative only).

## A13 — vessel arrival schedules for seasons before stem coverage
- **Value**: for seasons where archived stem snapshots are sparse (2021/22–2023/24
  ≈ monthly snapshots), vessel arrivals derive from AIS-observed berth visits instead of
  the stem; stem used for names/tonnages where join succeeds (date-window matching).
- **Reasoning**: stems are rolling snapshots archived ~monthly (65 PDFs, 2021–2026);
  AIS is continuous. Identifier-stripped AIS cannot be joined to names except via dates.
