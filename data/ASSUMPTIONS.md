# Assumptions Register — Windrow

Every value used by the model that is **not** backed by a published source, with
reasoning. Data files mark these `"provenance": "assumed"`. Simulated outputs are never
presented as measured data.

## A1 — truck net payloads per configuration
- **Value**: semi-trailer 28 t; 9-axle B-double 42 t; A-double road train 55 t;
  AB-triple 68 t (net grain tonnes). Model blends: **farm→site 38 t**
  (`truckPayloadT`), **site→port line-haul 45 t** (`linehaulPayloadT`).
- **Used in**: truck agents (Phase 3 params). Both blends are exposed as assumption
  levers in the app.
- **Reasoning**: GTSN publishes gross combination masses only; tares are not published.
  Net ≈ 62–66 % of GCM. The two published anchors pull in different directions and are
  reconciled as follows:
  - ACCC FD p.67 records 72 t loads "being **allowed**" on EP — a *permitted ceiling*
    (≈ Type 1 AB-triple at HML), not an average.
  - Viterra's 2019 rail-replacement statement (48 loaded trucks/day moving
    ~2,100–2,200 t/day) implies **~45 t per line-haul load** in actual operation — this
    is the line-haul default.
  - SA average delivered load >29 t in 2016-17 (all regions, incl. small farm semis)
    bounds the farm→site blend from below; 38 t reflects EP's better road-train access.
- **Known gap (added after review)**: the GTSN **Truck Book** also lists **Type 2** road
  trains (53.5 m) that SA permits to **132.83 t CML / 142.28 t HML** — roughly 85 t net,
  nearly double the line-haul default. Whether EP highways are on SA's pre-approved
  53.5 m network is unresolved (data/trucks.md open question 7). Until it is, 45 t is
  the *operationally anchored* figure and 85 t the *legal ceiling*.
- **Sensitivity**: farm→site payload is linear on truck counts and largely absorbed by
  the fitted fleet size (see A1 note in docs/calibration_report.md). Line-haul payload is
  NOT absorbed: it drives truck-km directly, and the rail scenario's headline saving
  falls from ~2.2 M truck-km (45 t) to ~1.1 M (72 t) to ~0.9 M (85 t) on 2025/26. Loaded
  tonne-km — and therefore the freight dollar figures — barely move, since the same
  grain travels the same distance either way.
- **Upgrade path**: operator turnaround/weighbridge data; truck-spec tare sheets; RAVnet
  53.5 m network coverage for EP.

## A2 — receival site service times and bay counts
- **Value**: sample + weigh + tip cycle 12 min/truck/bay; **4 tipping bays at an upcountry
  site, 6 at a port terminal** (`countryBays`, `portBays`).
- **Reasoning**: not published anywhere in minutes. Bounded by physics against the one
  published throughput anchor — the Port Lincoln site record of **13,148/13,512 t/day
  (Nov 2020) and 13,675 t/day (2022/23)**: at ~40 t average load that is ~340 truck
  visits/day, ~24/h across a 14 h receival day, and a 12-min cycle serves 5 trucks/bay/h,
  so **at least 5 bays** are required to reach the record at all.
- **CORRECTED 2026-08-19 (was 2 bays upcountry / 4 at ports)**: the earlier values were
  never checked against that record. Measured, the 2/4 configuration peaks at
  **10,285 t/day** at Port Lincoln — 24 % below the published record, i.e. the model
  physically could not reproduce a documented day. At 4/6 it reaches **13,224 t/day**,
  inside the published band. Under-provisioned bays inflated queues (mean 120 min,
  peak 189 trucks), which in turn inflated truck cycle times and therefore the fitted
  fleet size: the calibrator was buying missing site throughput with imaginary trucks.
- **Sensitivity**: drives queue lengths at peak — a headline output — and, indirectly,
  the fitted fleet. Bay counts are now calibrated within a band that keeps the modelled
  Port Lincoln peak day inside the published record; must stay marked assumed in the UI.
- **Related finding**: with bays under-provisioned the calibration objective is monotone
  in fleet size (more trucks always scored better, to 900+), and only the engine's own
  `QUEUE INSANE` invariant (>400 trucks at one site) bounded it. Fleet size is therefore
  **not identifiable from the weekly regional receivals alone** — it is pinned by site
  throughput and queue plausibility. See docs/calibration_report.md.
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

## A17 — carry-in (opening) stocks
- **Value**: each season opens with stocks = that season's observed Oct+Nov grain
  shipments at Port Lincoln and Thevenard (Flinders statistics), +20 % assigned to
  upcountry sites; commodity split wheat 55 / barley 30 / lentils 15.
- **Used in**: engine seeding; `observed_{season}.json.carry_in`.
- **Reasoning**: October–November vessels load almost entirely old crop (new-crop
  receivals only begin mid-October), so those shipments are a direct, season-specific
  measurement of the carry-over actually drawn down.
- **Sensitivity**: sets early-season shipping feasibility; receivals calibration
  unaffected (carry-in is never "received").

## A18 — road grain freight rate (economics layer, indicative)
- **Value**: A$0.10 per tonne-km (range 0.07–0.13).
- **Used in**: app takeaways panel only (freight $ deltas). Never in the sim itself.
- **Reasoning**: consistency-checked against published anchors: ~144 km average
  site→port haul ⇒ ≈A$14/t cartage, sitting sensibly inside the published $60–75/t
  whole-of-chain cost at 200 km (AEGIC via ESCOSA 2019) and EP-vs-eastern-SA relative
  cost statements. No single public EP $/t-km schedule exists.
- **Sensitivity**: linear on displayed freight dollars; labelled "indicative" in-app.

## A19 — vessel waiting cost (economics layer, indicative)
- **Value**: A$30,000 per vessel-day at anchor (≈US$15–25k/day demurrage-equivalent
  for handy-to-panamax bulk carriers, mid-range).
- **Used in**: app takeaways panel only. Labelled indicative; market rates vary widely.

## A20 — provisional 2026/27 live-season demand
- **Value**: district×crop production = mean of PIRSA 2022/23–2025/26 estimates
  (2.88 Mt EP total); carry-in = mean of prior two seasons' Oct+Nov shipments.
- **Used in**: `demand_2026-27.json` etc. via `pipeline/p2_build_live.py`.
- **Upgrade path**: replace automatically when PIRSA publishes 2026/27 estimates and
  as live receivals/shipments land (re-run the live builder).

## A21 — rail-reinstatement scenario parameters
- **Value**: 2 trainsets × 1,600 t net, serving only the historically rail-served silos
  (Cummins, Kimba, Wudinna) into Port Lincoln; no timetable — dispatch is demand-driven
  like the road shuttle; combined load/unload handling 4 h; line speed 40 km/h against
  the matrix's 75 km/h road mean, so a trainset covers the same distance as the trucks
  it replaces but takes ~1.9× as long; road line-haul fleet cut by one-third in the
  scenario. Cycle time = 2 × transit + 4 h handling, which works out at **~1.8
  cycles/day on the Kimba and Wudinna lines and ~3.6 on the short Cummins run** — 1.5
  per trainset per active day as actually dispatched on 2025/26 (a demand-driven
  shuttle idles when port stocks are covered). There is no hard cycle cap: an earlier
  version of this entry claimed a "≈2 cycles/day ceiling" that the engine never
  enforced and, at road speeds, never observed.
- **Used in**: engine `railReinstated`; "Bring back the trains" scenario.
- **Reasoning**: anchored to the published replacement task — Viterra stated the closed
  railway's work equalled "48 loaded trucks a day" (~2,100–2,200 t/day; ABC, Feb 2019) —
  and ACCC's record that rail carried only the Cummins/Kimba/Wudinna lines. Consist
  size, trainset count, cycle handling time, line speed and the absence of
  track-capacity limits are modelling choices, not citations; the EP narrow gauge was
  slow and speed-restricted, and 40 km/h door to door is a judgement, not a measurement.
  Rail distance is proxied by the road matrix (no rail alignment lengths in the bundle).
- **Accounting**: trainset tonne-km accumulate in a separate `railTonneKm` counter and
  trainset kilometres are excluded from `truckKm`. Only ROAD tonne-km are priced at the
  A18 cartage rate — the road rate does not describe rail haulage, and the cost of
  rebuilding and operating the railway is not priced anywhere in the model. Trainset
  tonnes are likewise excluded from the corridor truck-flow heatmap, which shows road
  traffic only.
- **Sensitivity**: affects only the rail scenario's truck-km savings and queue relief —
  and those are dominated by the line-haul payload the trains displace (A1): the saving
  falls from ~2.2 M truck-km at 45 t/load to ~0.9 M at 85 t. Report it as a range.
- **Upgrade path**: a real reinstatement proposal (consist sizes, timetable, loop
  lengths) would replace all of this.

## A22 — on-farm holding cost (economics layer, indicative)
- **Value**: A$0.09 per tonne per day for harvested grain waiting on farm before
  delivery (≈ $380/t farm-gate value financed at ~9 % p.a. agricultural overdraft).
- **Used in**: app takeaways ("Grain waiting on farm" row/sentence), driven by the
  engine's cumulative on-farm tonne-days. Never affects sim behaviour.
- **Reasoning**: growers are not paid until grain is delivered/warehoused; delay is a
  financing cost (PIRSA's 2024/25 report notes extended overdrafts under exactly this
  pressure). Deliberately financing-ONLY: weather, insect and quality risks of on-farm
  holding are real but have no public price, so they are named in the UI as unpriced
  rather than guessed.
- **Sensitivity**: linear on the displayed holding dollars; labelled indicative.

## A23 — site-attractiveness ⇄ cash-premium translation (economics layer, indicative)
- **Value**: a Lucky Bay attractiveness multiplier m is displayed as an equivalent cash
  premium of `90 min × (1 − m^(−1/β)) × (80/60 km/min) × A18 freight rate` A$/t, with
  β the calibrated choiceBeta (1.965). Default constants: representative eastern-EP
  haul 90 generalized minutes (drive + queue + service), 80 km/h effective speed.
  Example: the 2.5× scenario ≈ +$6/t at the default 10¢/t·km rate.
- **Used in**: app only (Lucky Bay lever readout, scenario story, About). Never affects
  sim behaviour — site choice stays `attract / cost^β` on minutes.
- **Reasoning**: in a Huff-style power-law choice, multiplying attractiveness by m is
  identical to shrinking generalized cost by the factor m^(−1/β); pricing that shrinkage
  at the road freight rate expresses the fitted bias in the units growers actually see
  (a $/t site premium). T-Ports' public launch pitch was precisely price/convenience
  incentives, so the translation direction is meaningful even though the representative
  haul is a modelling choice.
- **Sensitivity**: linear in the representative haul and freight rate; only the
  displayed $/t label changes.
- **Upgrade path**: v2 net-price site choice using the captured daily cash-bid series
  (data/processed/cash_prices/) once a harvest of EP bids exists — then premiums are
  data, not a translation.

## A13 — vessel arrival schedules for seasons before stem coverage
- **Value**: for seasons where archived stem snapshots are sparse (2021/22–2023/24
  ≈ monthly snapshots), vessel arrivals derive from AIS-observed berth visits instead of
  the stem; stem used for names/tonnages where join succeeds (date-window matching).
- **Reasoning**: stems are rolling snapshots archived ~monthly (65 PDFs, 2021–2026);
  AIS is continuous. Identifier-stripped AIS cannot be joined to names except via dates.
