/**
 * Windrow simulation core — pure, headless, deterministic.
 *
 * Time model: fixed 5-minute tick (288/day). Chosen over event-driven because the
 * harvest peak is activity-dense (hundreds of concurrent truck cycles + queue feedback
 * every few minutes), making a tick both simpler and no slower; one full season is
 * ~105k ticks and runs in well under 5 s headless (see tests).
 *
 * Determinism: one seeded sfc32 stream; all loops in fixed index order; no Date.now,
 * no Math.random, no object-key iteration for state-affecting logic. Same bundle +
 * params + seed => byte-identical event log (hashed in RunResult).
 */
import { CORRIDORS, corridorShare } from "./corridors";
import { Rng } from "./rng";
import { COMMODITIES, NC } from "./types";
import type {
  Bundle,
  Commodity,
  Params,
  RunResult,
  SimEvent,
  Snapshot,
  SiteView,
  TruckView,
  VesselView,
} from "./types";

export const TICK_MIN = 5;
export const DAY_TICKS = (24 * 60) / TICK_MIN;
// how long a vessel sits at anchor before the charterer would have re-nominated the
// program rather than keep waiting on grain that may never come (A19/#6)
export const VESSEL_GIVEUP_TICKS = 15 * DAY_TICKS;

// truck states
export const T_IDLE = 0,
  T_LOAD = 1,
  T_GO = 2,
  T_QUEUE = 3,
  T_TIP = 4,
  T_RETURN = 5;
// vessel states
export const V_PENDING = 0,
  V_ANCHOR = 1,
  V_BERTH = 2,
  V_DONE = 3;

// exported (not just used internally) so the app can decode segregation codes for
// display instead of showing raw codes like "WH" / "BA" verbatim (F35)
export const SEG_TO_COMMODITY: Record<string, Commodity> = {
  WH: "wheat",
  BA: "barley",
  CA: "canola",
  LE: "lentils",
  FB: "beans",
};
const STEM_TO_COMMODITY: Record<string, Commodity> = {
  Wheat: "wheat",
  Durum: "wheat",
  Barley: "barley",
  Canola: "canola",
  Lentils: "lentils",
  Beans: "beans",
  Peas: "other",
  Oats: "other",
  Lupins: "other",
  Chickpeas: "other",
};

interface SiteState {
  idx: number;
  name: string;
  isPort: boolean;
  isBunge: boolean;
  isTports: boolean;
  open: boolean;
  capacityT: number;
  stock: Float64Array; // per commodity
  bays: number;
  bayBusyUntil: number[]; // tick when each bay frees
  queue: number[]; // truck ids
  serviceMin: number;
  accepts: boolean[]; // per commodity
  cumReceivedT: number;
  shiploaderTph: number;
  berthsFree: number;
  cumShippedT: number;
}

interface Truck {
  id: number;
  kind: 0 | 1; // 0 farm, 1 linehaul
  state: number;
  cluster: number; // farm: home cluster
  site: number; // current destination site (or source site for linehaul)
  destPort: number; // linehaul destination
  commodity: number;
  loadT: number;
  payloadT: number;
  doneAt: number; // tick when current activity completes
  legMin: number; // total minutes of current travel leg
  legKm: number; // one-way network distance of that leg (routed km, not time x speed)
  legStart: number; // tick when leg started
}

/** historical EP rail-served sites (rail scenario): Cummins/Kimba/Wudinna lines -> Port Lincoln */
const RAIL_SITES = ["Cummins", "Kimba", "Wudinna"];
/** Fallback mean road speed, used ONLY if a bundle predates the matrix `*_km` fields
 *  (issue #10). Real leg distances now come out of the OSM routing step alongside the
 *  minutes; deriving km from minutes at one blended speed understated trunk line-haul by
 *  ~15% and overstated slow low-class farm legs by up to 25%, because A5 actually routes
 *  at 90/80/70/60/40 km/h by road class. Never use this for a bundle that carries km. */
const FALLBACK_SPEED_KMH = 75;
/** mean EP narrow-gauge line speed for a loaded grain train, door to door (A21). The
 *  alignment length is proxied by the road network, so a trainset covers the SAME distance
 *  as the trucks it replaces, at this speed instead of the road speed for that route. */
const RAIL_SPEED_KMH = 40;

/** Degree of curing (%) assumed for a paddock being harvested. A ripe cereal or pulse
 *  crop standing ready for the header is fully cured by definition — this is not a free
 *  parameter, and the published cease-harvest tables that A7 is validated against assume
 *  the same thing (see below). */
const CURING_PCT = 100;
/** Constant term of the Mark 4 grassland meter with the curing term folded in at
 *  CURING_PCT: -23.6 + 5.01 ln(100) = -0.53. Hoisted because the season loop evaluates
 *  the index 1,110 times per Sim and the calibrator builds thousands of Sims. */
const GFDI_C0 = -23.6 + 5.01 * Math.log(CURING_PCT);

/**
 * McArthur **Mark 4 grassland fire-danger index** (GFDI) for a fully cured paddock, in
 * the equation form of Purton (1982), *Equations for the McArthur Mark 4 grassland fire
 * danger meter*, BoM Meteorological Note 147 (the meters were first put into equations by
 * Noble, Bary & Gill 1980):
 *
 *     GFDI = 2.0 exp(-23.6 + 5.01 ln C + 0.0281 T - 0.226 sqrt(RH) + 0.633 sqrt(U))
 *
 * C = degree of curing (%), T = air temperature (°C), RH = relative humidity (%),
 * U = 10 m wind speed (km/h).
 *
 * This is the index the **CFS/PIRSA/Grain Producers SA Grain Harvesting Code of Practice**
 * (Sept 2023) is written against: Required Practice 1 is "suspend grain harvesting
 * operations when the local actual GFDI exceeds 35". District harvesting codes publish
 * that threshold as a lookup table of the wind speed at which to stop for a given
 * temperature and humidity; this implementation reproduces two published entries of that
 * table to within ~3 index points (35 °C / 14 % RH / 26 km/h -> 34; 40 °C / 15 % RH /
 * 26 km/h -> 38, against a stated threshold of 35). See ASSUMPTIONS.md A7.
 *
 * Note this is temperature AND wind AND humidity together. A 41 °C day with a 20 km/h
 * breeze scores ~24 and is a perfectly good harvest day; a 22 °C day with a 47 km/h wind
 * over cured stubble scores ~36 and is not. That is the whole point of using it.
 */
export function gfdiFullyCured(tempC: number, rhPct: number, windKmh: number): number {
  return (
    2.0 *
    Math.exp(GFDI_C0 + 0.0281 * tempC - 0.226 * Math.sqrt(Math.max(0, rhPct)) + 0.633 * Math.sqrt(Math.max(0, windKmh)))
  );
}

interface Vessel {
  id: number;
  port: number; // site index
  arriveTick: number; // arrival at anchorage (AIS-linked where available)
  slotTick: number; // earliest berthing (observed berth time; pilotage/slot proxy)
  targetT: number;
  commodity: number; // -1 = decide at berth
  state: number;
  loadedT: number;
  waitTicks: number;
  berthedAt: number;
  lastDrawTick: number;
  name: string | null;
  rateTph: number;
}

export class Sim {
  readonly bundle: Bundle;
  readonly params: Params;
  private rng: Rng;

  tick = 0;
  private startUtc: number; // ms epoch of season start (Oct 1)

  // parcels
  private nParcels: number;
  private parcelRemaining: Float64Array; // [p*NC + c] deliverable tonnes still in crop
  private parcelInitial: Float64Array;
  private parcelCluster: Int32Array;
  private parcelDistrict: Uint8Array; // 0 WEP 1 LEP 2 EEP
  private parcelMaturity: Float64Array; // [p*NC+c] day when harvest can start

  // clusters
  private nClusters: number;
  private clusterDistrict: Uint8Array = new Uint8Array(0);
  private clusterOnFarm: Float64Array; // [cl*NC+c]
  private clusterParcels: number[][];
  private clusterCand: { site: number; minutes: number; km: number }[][];

  sites: SiteState[] = [];
  private trucks: Truck[] = [];
  private vessels: Vessel[] = [];

  // accounting (tonnes)
  private harvestedRawT = 0;
  private retainedT = 0;
  private inTransitT = 0;
  receivedBungeT = 0;
  receivedLbT = 0;
  shippedT = 0;
  private dailyBungeReceivals: number[] = [];
  private vesselWaitTicksTotal = 0;
  peakQueue = 0;
  /** worst modelled turnaround at any one site, minutes — the same line as peakQueue
   *  expressed in the units A2's balk tolerance is stated in. F27 was that this number
   *  reached 22 h and was reported as fact; it is now bounded by queueBalkMaxMin plus the
   *  one service slot a joining truck does not yet occupy when the gate checks it. */
  peakQueueMin = 0;
  /** site-days on which a queue was found above params.siteQueueMaxTrucks. Zero by
   *  construction (see checkInvariants); a non-zero value means the join gate leaked. */
  queueCapBreaches = 0;
  truckTravelMin = 0; // ROAD loaded+empty travel minutes (cycle-time diagnostics)
  truckKm = 0; // ROAD loaded+empty vehicle-km, summed from routed leg distances
  tonneKm = 0; // loaded ROAD tonne-km (economics layer; the only tonne-km A18 prices)
  railTravelMin = 0; // trainset loaded+empty travel minutes (rail scenario)
  railTonneKm = 0; // loaded RAIL tonne-km — moved by trainsets, so NOT a road freight cost
  /** trainset dispatches, and the distinct days on which any happened (rail scenario).
   *  docs/scenarios.md quotes the cycles-per-trainset-per-active-day these give; before
   *  #24 that figure could not be reproduced from the code at all. */
  railTrips = 0;
  railActiveDays = new Set<number>();
  /** farm trucks currently en route to each site: growers can see site status/wait
   *  before committing, so the choice model must not ignore committed traffic. */
  private siteInbound: Int32Array = new Int32Array(0);
  /** the same commitment in TONNES rather than trucks: grain that has left a farm bound
   *  for this site and has not tipped yet (#29). `siteInbound` bounds the QUEUE; this
   *  bounds the STORAGE. A truck reserves its load at dispatch and releases it at the
   *  tip that puts it into `stock`, so `stock + siteInboundT <= capacityT` is an
   *  invariant every gate below preserves — including line-haul's arrival check, which
   *  must not spend headroom a farm truck is already rolling toward. */
  private siteInboundT: Float64Array = new Float64Array(0);
  carryInT = 0; // opening stocks seeded from observed Oct-Nov shipments (A17)
  /** carry-in (A17) that would not physically fit in the site it was assigned to, and was
   *  therefore never seeded. Non-zero only when `carryInScale` is pushed far enough that
   *  the scaled opening stock exceeds a published/estimated capacity — see A17. */
  carryInClampedT = 0;
  /** site-days on which stock was found above capacityT. Zero by construction (see
   *  checkInvariants); a non-zero value means a capacity gate leaked (#29). */
  capacityBreaches = 0;
  onFarmTonneDays = 0; // harvested grain waiting on farm x days (holding-cost basis, A22)
  /** cumulative loaded tonnes per rendered path ("cid-sid" farm, "si-pj" line-haul) */
  tripTonnesByPath = new Map<string, number>();

  events: SimEvent[] = [];
  private debugEvents: boolean;
  // chooseSite scratch (see there): hoisted so the per-truck-per-tick call allocates nothing
  private csWeights: number[] = [];
  private csOpts: { site: number; minutes: number; km: number }[] = [];
  private csOpen: { site: number; minutes: number; km: number }[] = [];
  private csOpenQueueMin: number[] = [];
  private portInboundT: Float64Array = new Float64Array(0);
  private cachedPortNeed: Float64Array = new Float64Array(0);
  /** road-closure multiplier on the site->port line-haul leg, [srcSite][portSite].
   *  null unless the scenario is on; 1 for a leg the closed corridor does not touch.
   *  Public so the closure can be inspected without running a season (#28). */
  closureSitePort: number[][] | null = null;

  private weatherFactor: Float64Array; // [district*370 + day]
  private rampDays: number;

  constructor(bundle: Bundle, params: Params, seed: number, debugEvents = false) {
    this.bundle = bundle;
    this.params = params;
    this.rng = new Rng(seed);
    this.debugEvents = debugEvents;
    this.rampDays = params.harvestRampDays ?? 10;
    const y = parseInt(bundle.season.slice(0, 4), 10);
    this.startUtc = Date.UTC(y, 9, 1); // Oct 1

    // ---- parcels & demand ----
    const parcels = bundle.parcels;
    this.nParcels = parcels.length;
    this.parcelRemaining = new Float64Array(this.nParcels * NC);
    this.parcelInitial = new Float64Array(this.nParcels * NC);
    this.parcelCluster = new Int32Array(this.nParcels);
    this.parcelDistrict = new Uint8Array(this.nParcels);
    this.parcelMaturity = new Float64Array(this.nParcels * NC);
    const distIdx = { WEP: 0, LEP: 1, EEP: 2 } as const;
    const demandById = new Map<number, Record<string, number>>();
    for (const d of bundle.demand.parcels) demandById.set(d.id, d.crops);
    for (let p = 0; p < this.nParcels; p++) {
      const bp = parcels[p]!;
      this.parcelCluster[p] = bp.cluster_id;
      this.parcelDistrict[p] = distIdx[bp.district];
      const crops = demandById.get(bp.id) ?? {};
      for (let c = 0; c < NC; c++) {
        const t = (crops[COMMODITIES[c]!] ?? 0) * params.productionScale;
        this.parcelInitial[p * NC + c] = t;
        this.parcelRemaining[p * NC + c] = t;
        // maturity: base + district offset + deterministic per-parcel jitter (+-6 d)
        const jitter = ((((bp.id * 2654435761) >>> 0) % 1000) / 1000 - 0.5) * 12;
        this.parcelMaturity[p * NC + c] =
          params.maturityDayOffset[COMMODITIES[c]!] + params.districtStartOffset[bp.district] + jitter;
      }
    }

    // ---- weather factors ----
    this.weatherFactor = new Float64Array(3 * 370).fill(1);
    const springShift = [0, 0, 0]; // per district, days added to maturity
    const wd = bundle.weather.districts;
    const wStart = Date.UTC(y, 8, 1); // weather files start Sep 1
    const offsetDays = Math.round((this.startUtc - wStart) / 86400000);
    (["WEP", "LEP", "EEP"] as const).forEach((dname, di) => {
      const w = wd[dname];
      for (let day = 0; day < 370; day++) {
        const i = day + offsetDays;
        const rain = w.rain_mm[i] ?? 0;
        const rain2 = (w.rain_mm[i - 1] ?? 0) + rain;
        const rs = params.rainStopMm ?? 5; // A7 threshold (assumption lever)
        let f = 1.0;
        if (rain >= rs || rain2 >= 2 * rs) f = 0;
        else if (rain >= 0.4 * rs) f = 0.5;
        // hangover: paddocks stay wet after a heavy fall (A7)
        if ((w.rain_mm[i - 1] ?? 0) >= 1.6 * rs) f *= 0.3;
        else if ((w.rain_mm[i - 2] ?? 0) >= 1.6 * rs) f *= 0.5;

        // ---- fire-danger harvest ban (A7) ----
        // Peak-of-day GFDI from the day's worst combination: hottest temperature, driest
        // hour, windiest hour. Those three do broadly coincide in the mid-late afternoon
        // of a hot north-westerly, which is exactly when bans get called; on other days
        // this overstates the peak, which is the main known bias in this rule.
        // Fallbacks outside the weather array are a benign day (GFDI ~10, no ban).
        const g = gfdiFullyCured(w.tmax_c[i] ?? 25, w.rh_min_pct[i] ?? 40, w.wind_max_kmh[i] ?? 20);
        const gb = params.harvestBanGfdi ?? 35; // published cease-harvest trigger (lever)
        if (g > gb) {
          // The code of practice SUSPENDS harvesting while the index is over the
          // threshold — it does not write off the day — so what matters is how long the
          // day spends above it. GFDI traces a diurnal arc, near zero overnight (cool,
          // humid, calm) and peaking mid-late afternoon. Approximating that arc as a
          // cosine of peak height g, the share of it lying above gb is
          //     (2/pi) acos(gb/g)
          // which is 0 for a day that only just touches the trigger, 1/3 at g = 40,
          // 1/2 at g = 50, 2/3 at g = 70, and tends to 1 for a catastrophic day. The
          // remainder is the early morning and the evening after the wind drops, which
          // is when growers actually get a ban day's grain off. No free constant here
          // beyond the published trigger itself.
          f *= 1 - (2 / Math.PI) * Math.acos(Math.min(1, gb / g));
        }
        this.weatherFactor[di * 370 + day] = f;
      }
      // spring-dryness maturity shift (A7 extension): dry Sep-Oct => crops ripen earlier.
      // shift = clamp((springRain - 45 mm) * 0.25 d/mm, -12, +10)
      let springRain = 0;
      for (let i = 0; i < offsetDays + 31 && i < w.rain_mm.length; i++) springRain += w.rain_mm[i] ?? 0;
      springShift[di] = Math.max(-12, Math.min(10, (springRain - 45) * 0.25));
    });
    for (let p = 0; p < this.nParcels; p++) {
      const di = this.parcelDistrict[p]!;
      for (let c = 0; c < NC; c++) this.parcelMaturity[p * NC + c] = this.parcelMaturity[p * NC + c]! + springShift[di]!;
    }

    // ---- clusters ----
    const clusters = bundle.matrix.clusters;
    this.nClusters = clusters.length;
    this.clusterOnFarm = new Float64Array(this.nClusters * NC);
    this.clusterParcels = Array.from({ length: this.nClusters }, () => []);
    for (let p = 0; p < this.nParcels; p++) this.clusterParcels[this.parcelCluster[p]!]!.push(p);
    this.clusterDistrict = new Uint8Array(this.nClusters);
    for (let cl = 0; cl < this.nClusters; cl++) {
      this.clusterDistrict[cl] = ({ WEP: 0, LEP: 1, EEP: 2 } as const)[clusters[cl]!.district];
    }

    // ---- sites ----
    const season = bundle.season;
    // Network-state override (R5/R0/R3). Validated against the bundle BEFORE the loop:
    // a name that matches no site is a typo, and a typo that silently changed nothing
    // would hand back a normal-looking season total for a network state that was never
    // applied — the same class of silent-wrong-number defect as #20 and #29.
    const ns = params.networkState ?? null;
    if (ns) {
      const known = new Set(bundle.matrix.sites.map((s) => s.name));
      const unknown = [...(ns.forceOpen ?? []), ...(ns.forceClosed ?? [])].filter((n) => !known.has(n));
      if (unknown.length) {
        throw new Error(
          `networkState names no site in this bundle: ${unknown.join(", ")}. ` +
            `Sites present: ${[...known].join(", ")}`,
        );
      }
    }
    const forceOpen = new Set(ns?.forceOpen ?? []);
    const forceClosed = new Set(ns?.forceClosed ?? []);
    for (const s of bundle.matrix.sites) {
      const isTports = s.operator.includes("T-Ports");
      const isPort = s.role === "port";
      let open = true;
      if (s.status === "dormant") open = false;
      // Per-season closures are DATA on the site record (pipeline/manual_sites.json ->
      // sites.geojson -> matrix.json). Today that is the two T-Ports bunkers: 2025/26
      // published, 2024/25 assumed (A15). Until 2026-09-06 this was a literal match on
      // the season string in here, so a 2026/27 bundle silently reopened them and A15
      // could only be revised by editing engine code.
      if (s.closed_seasons?.includes(season)) open = false;
      // ...and the network-state override wins over both of the rules above. forceClosed
      // beats forceOpen for a site named in both, so the result never depends on order.
      if (forceOpen.has(s.name)) open = true;
      if (forceClosed.has(s.name)) open = false;
      const accepts = new Array(NC).fill(false) as boolean[];
      if (isPort) accepts.fill(true);
      else {
        for (const code of s.commodities) {
          const c = SEG_TO_COMMODITY[code];
          if (c) accepts[COMMODITIES.indexOf(c)] = true;
        }
        // sites with 3+ segregations act as general receivers for minor "other" crops
        if (s.commodities.length >= 3) accepts[COMMODITIES.indexOf("other")] = true;
      }
      // An OPEN site with no segregation list accepts NOTHING (`chooseSite` skips any
      // site where `accepts[c]` is false), so it would sit in the network looking open,
      // receive zero tonnes for the whole season, and still be seeded carry-in stock by
      // capacity share below — a silent wrong number, whichever rule opened it. Dormant
      // and closed-2019 sites carry `commodities: []` in the bundle, so this is the
      // normal case, not an edge one: opening any of them needs an assumed segregation
      // list in the DATA first (A12-style), which is why this throws rather than
      // guessing one here. It applied only to `forceOpen` until 2026-09-06, while the
      // status path shipped four such sites (the A12 roster correction) unchecked.
      if (open && !isPort && !accepts.some(Boolean)) {
        const how = forceOpen.has(s.name) ? "networkState.forceOpen names" : "the bundle opens";
        throw new Error(
          `${how} "${s.name}", which carries no commodities in this bundle and would ` +
            `therefore accept nothing. Give it a segregation list in the bundle (see A12) ` +
            `before opening it.`,
        );
      }
      const name = s.name;
      // A4: every site now carries a capacity from the bundle - published where one
      // exists (both ports, all three T-Ports sites), otherwise the district allocation
      // r1_build_sites.py computes. upcountryCapScale is the lever on the estimated
      // ones only; a published tonnage is not an assumption to sweep. The `??` is a
      // safety net for a bundle built before issue #20, not the live path.
      const capEstimated = s.capacity_estimated ?? s.capacity_t == null;
      const baseCapacityT = s.capacity_t ?? (isTports ? 145000 : 120000);
      const capacityT = capEstimated ? baseCapacityT * (params.upcountryCapScale ?? 1) : baseCapacityT;
      const st: SiteState = {
        idx: this.sites.length,
        name,
        isPort,
        isBunge: !isTports,
        isTports,
        open,
        capacityT,
        stock: new Float64Array(NC),
        bays: isPort ? Math.max(1, Math.round(params.portBays ?? 4)) : Math.max(1, Math.round(params.countryBays ?? 2)),
        bayBusyUntil: [],
        queue: [],
        serviceMin: params.siteServiceMin ?? 12, // A2 (assumption lever)
        accepts,
        cumReceivedT: 0,
        shiploaderTph: name.includes("Lincoln") ? 3000 : name.includes("Thevenard") ? 1000 : 417, // LB = 10 kt/day transshipment
        berthsFree: name.includes("Lincoln") ? 2 : 1,
        cumShippedT: 0,
      };
      st.bayBusyUntil = new Array(st.bays).fill(0);
      this.sites.push(st);
    }
    this.siteInbound = new Int32Array(this.sites.length);
    this.siteInboundT = new Float64Array(this.sites.length);

    // scenario: port outage handled in step()

    // ---- carry-in stocks (A17): seed opening stocks from observed Oct-Nov shipments ----
    const ci = bundle.observed.carry_in;
    if (ci) {
      const SPLIT: [number, number][] = [
        [COMMODITIES.indexOf("wheat"), 0.55],
        [COMMODITIES.indexOf("barley"), 0.3],
        [COMMODITIES.indexOf("lentils"), 0.15],
      ];
      const ciScale = params.carryInScale ?? 1; // A17 (assumption lever)
      // A shed cannot hold more than it holds. A17's figure is a LOWER BOUND on old crop
      // read off Oct-Nov shipments, and the lever scales it up to 2x — at which point
      // 2023/24's 320,504 t at Port Lincoln becomes 641,008 t against 395,600 t of
      // published storage (162 % full on day one, #29). Seeding it anyway put a physically
      // impossible opening stock on the map and into every capacity-derived reading.
      // The overflow is CLAMPED, not spilled to a neighbour: A17's provenance is
      // specifically port-held old crop shipped out of Port Lincoln and Thevenard, so
      // moving it upcountry would invent a location the source says nothing about. What
      // the clamp really reports is that the scaled figure is not physically realisable
      // there — so it is counted (carryInClampedT), logged, and disclosed in A17 rather
      // than quietly absorbed.
      const seed = (siteIdx: number, tonnes0: number) => {
        const tonnes = tonnes0 * ciScale;
        if (siteIdx < 0 || tonnes <= 0) return;
        const s = this.sites[siteIdx]!;
        let held = 0;
        for (let c = 0; c < NC; c++) held += s.stock[c]!;
        const placed = Math.min(tonnes, Math.max(0, s.capacityT - held));
        if (placed > 0) for (const [c, share] of SPLIT) s.stock[c] = s.stock[c]! + placed * share;
        this.carryInT += placed;
        const spilled = tonnes - placed;
        if (spilled > 0.01) {
          this.carryInClampedT += spilled;
          this.log({ t: 0, type: "carry_in_clamped", site: s.idx, name: s.name, asked_t: tonnes, placed_t: placed });
        }
      };
      seed(this.sites.findIndex((s) => s.name.includes("Lincoln")), ci.port_lincoln_t);
      seed(this.sites.findIndex((s) => s.name.includes("Thevenard")), ci.thevenard_t);
      // upcountry share distributed across open Bunge sites by capacity
      const up = this.sites.filter((s) => !s.isPort && s.isBunge && s.open);
      const capSum = up.reduce((a, s) => a + s.capacityT, 0) || 1;
      for (const s of up) seed(s.idx, (ci.upcountry_t * s.capacityT) / capSum);
    }

    // ---- cluster candidate sites ----
    this.clusterCand = [];
    for (let cl = 0; cl < this.nClusters; cl++) {
      const m = bundle.matrix.cluster_site_minutes[String(cl)] ?? {};
      const mk = bundle.matrix.cluster_site_km?.[String(cl)] ?? {};
      const cand: { site: number; minutes: number; km: number }[] = [];
      for (const [sid, min] of Object.entries(m)) {
        // routed distance along the same path as `min`; the fallback only fires for a
        // bundle built before the routing step exported km (#10)
        const km = mk[sid] ?? (min / 60) * FALLBACK_SPEED_KMH;
        cand.push({ site: parseInt(sid, 10), minutes: min, km });
      }
      cand.sort((a, b) => a.minutes - b.minutes);
      this.clusterCand.push(cand);
    }

    // ---- road closure scenario ----
    // Both legs of the chain detour, not just the first. Before #28 the closure was
    // applied ONLY to farm->site candidates, so silo->port line-haul kept running at full
    // speed over a road the scenario had just declared impassable — and the test itself
    // asked whether the STRAIGHT-LINE MIDPOINT of a leg fell within 0.18 deg of a
    // straight-line corridor axis, which both missed legs that run the corridor end to
    // end (their midpoint lands outside) and hit legs that merely pass near its middle.
    //
    // Now: measure the share of each leg that runs inside the closed corridor, along the
    // leg's REAL routed polyline where the bundle carries one (see corridors.ts), and
    // scale minutes and km by 1 + share*(factor-1). A detour costs distance as well as
    // time, so both move. A leg entirely on the corridor still pays the full factor, as
    // it did before; a leg that only crosses the closure pays almost nothing.
    if (params.roadClosure) {
      const corridor = CORRIDORS[params.roadClosure.corridor];
      const extra = params.roadClosure.factor - 1;
      const paths = bundle.paths;
      for (let cl = 0; cl < this.nClusters; cl++) {
        const c = clusters[cl]!;
        for (const cand of this.clusterCand[cl]!) {
          const s = bundle.matrix.sites[cand.site]!;
          const route = paths?.cluster_site[`${cl}-${cand.site}`] ?? [
            [c.lon, c.lat],
            [s.lon, s.lat],
          ];
          const share = corridorShare(route, corridor);
          if (share <= 0) continue;
          const f = 1 + share * extra;
          cand.minutes *= f;
          cand.km *= f;
        }
      }
      // the same test for the site->port leg, precomputed here because stepLinehaul picks
      // its source and destination fresh on every dispatch
      const nSites = bundle.matrix.sites.length;
      const scale: number[][] = [];
      for (let i = 0; i < nSites; i++) scale.push(new Array<number>(nSites).fill(1));
      for (let i = 0; i < nSites; i++) {
        const src = bundle.matrix.sites[i]!;
        for (let j = 0; j < nSites; j++) {
          if (i === j) continue;
          const dst = bundle.matrix.sites[j]!;
          if (dst.role !== "port") continue; // line-haul only ever runs site -> port
          const route = paths?.site_port[`${i}-${j}`] ?? [
            [src.lon, src.lat],
            [dst.lon, dst.lat],
          ];
          const share = corridorShare(route, corridor);
          if (share > 0) scale[i]![j] = 1 + share * extra;
        }
      }
      this.closureSitePort = scale;
    }
    // A5 assumption lever: global travel-TIME scale. It moves speed, not geography, so
    // distances are deliberately left alone (before #10 they moved with it, silently
    // rescaling the freight task whenever the user touched the speed lever).
    const tts = params.travelTimeScale ?? 1;
    if (tts !== 1) {
      for (let cl = 0; cl < this.nClusters; cl++) {
        for (const cand of this.clusterCand[cl]!) cand.minutes *= tts;
      }
    }

    // ---- trucks ----
    // farm fleet distributed over clusters by seasonal tonnage share
    const clusterSeasonT = new Float64Array(this.nClusters);
    let totalT = 0;
    for (let p = 0; p < this.nParcels; p++) {
      let t = 0;
      for (let c = 0; c < NC; c++) t += this.parcelInitial[p * NC + c]!;
      const ci = this.parcelCluster[p]!;
      clusterSeasonT[ci] = clusterSeasonT[ci]! + t;
      totalT += t;
    }
    let id = 0;
    for (let cl = 0; cl < this.nClusters; cl++) {
      const n = Math.round((params.fleetTrucks * clusterSeasonT[cl]!) / (totalT || 1));
      for (let k = 0; k < n; k++) {
        this.trucks.push({
          id: id++,
          kind: 0,
          state: T_IDLE,
          cluster: cl,
          site: -1,
          destPort: -1,
          commodity: -1,
          loadT: 0,
          payloadT: params.truckPayloadT,
          doneAt: 0,
          legMin: 0,
          legKm: 0,
          legStart: 0,
        });
      }
    }
    for (let k = 0; k < params.linehaulTrucks; k++) {
      this.trucks.push({
        id: id++,
        kind: 1,
        state: T_IDLE,
        cluster: -1,
        site: -1,
        destPort: -1,
        commodity: -1,
        loadT: 0,
        payloadT: params.linehaulPayloadT ?? 45,
        doneAt: 0,
        legMin: 0,
        legKm: 0,
        legStart: 0,
      });
    }
    if (params.railReinstated) {
      // two trainsets shuttling the old Cummins/Kimba/Wudinna lines into Port Lincoln
      for (let k = 0; k < 2; k++) {
        this.trucks.push({
          id: id++, kind: 1, state: T_IDLE, cluster: -1, site: -1, destPort: -1,
          commodity: -1, loadT: 0, payloadT: 1600, doneAt: 0, legMin: 0, legKm: 0, legStart: 0,
        });
      }
    }

    // ---- vessels ----
    const portIdxByName = (frag: string) => this.sites.findIndex((s) => s.name.includes(frag));
    const plIdx = portIdxByName("Lincoln");
    const theIdx = portIdxByName("Thevenard");
    const lbIdx = portIdxByName("Lucky Bay");
    let vid = 0;
    if (bundle.vessels) {
      for (const v of bundle.vessels.port_lincoln_berth_visits) {
        const t = Math.max(0, Math.round((Date.parse(v.arrive) - this.startUtc) / 60000 / TICK_MIN));
        const ta = v.anchor_arrive
          ? Math.max(0, Math.round((Date.parse(v.anchor_arrive) - this.startUtc) / 60000 / TICK_MIN))
          : t;
        const commodity = v.stem_commodity ? COMMODITIES.indexOf(STEM_TO_COMMODITY[v.stem_commodity] ?? "wheat") : -1;
        this.vessels.push({
          id: vid++,
          port: plIdx,
          arriveTick: Math.min(ta, t),
          slotTick: t,
          targetT: Math.max(3000, v.est_cargo_t || 0),
          commodity,
          state: V_PENDING,
          loadedT: 0,
          waitTicks: 0,
          berthedAt: -1,
          lastDrawTick: 0,
          name: v.name_candidate ?? null,
          rateTph: 0,
        });
      }
      // Thevenard: monthly grain tonnes allocated across that month's calls (grain share of mixed-cargo port)
      const theMonthly = new Map<string, number>();
      for (const r of this.bundle.observed.port_lincoln_shipments_monthly) void r; // (PL handled via AIS targets)
      for (const r of (this.bundle.observed as unknown as { thevenard_shipments_monthly?: { year: number; month: number; export_t: number }[] })
        .thevenard_shipments_monthly ?? []) {
        const k = `${r.year}-${r.month}`;
        theMonthly.set(k, (theMonthly.get(k) ?? 0) + r.export_t);
      }
      const theVisits = bundle.vessels.thevenard_berth_visits_all_cargo;
      const byMonth = new Map<string, typeof theVisits>();
      for (const v of theVisits) {
        const d = new Date(v.arrive);
        const k = `${d.getUTCFullYear()}-${d.getUTCMonth() + 1}`;
        if (!byMonth.has(k)) byMonth.set(k, []);
        byMonth.get(k)!.push(v);
      }
      for (const [k, lst] of byMonth) {
        const grainT = theMonthly.get(k) ?? 0;
        if (grainT < 1000) continue;
        const per = grainT / lst.length;
        for (const v of lst) {
          const t = Math.max(0, Math.round((Date.parse(v.arrive) - this.startUtc) / 60000 / TICK_MIN));
          this.vessels.push({
            id: vid++, port: theIdx, arriveTick: t, slotTick: t, targetT: per, commodity: -1,
            state: V_PENDING, loadedT: 0, waitTicks: 0, berthedAt: -1, lastDrawTick: 0, name: null, rateTph: 0,
          });
        }
      }
      for (const v of bundle.vessels.lucky_bay_anchorage_stays) {
        const t = Math.max(0, Math.round((Date.parse(v.arrive) - this.startUtc) / 60000 / TICK_MIN));
        this.vessels.push({
          id: vid++, port: lbIdx, arriveTick: t, slotTick: t,
          targetT: Math.min(35000, Math.max(8000, (v.anchor_hours / 24) * 10000)),
          commodity: -1, state: V_PENDING, loadedT: 0, waitTicks: 0, berthedAt: -1, lastDrawTick: 0, name: null, rateTph: 0,
        });
      }
    }
    this.vessels.sort((a, b) => a.arriveTick - b.arriveTick || a.id - b.id);
  }

  get day(): number {
    return Math.floor(this.tick / DAY_TICKS);
  }

  dateIso(): string {
    return new Date(this.startUtc + this.day * 86400000).toISOString().slice(0, 10);
  }

  private log(e: SimEvent) {
    this.events.push(e);
  }

  private portOutageActive(site: SiteState): boolean {
    const o = this.params.outage;
    if (!o) return false;
    return site.name.includes(o.port) && this.day >= o.fromDay && this.day < o.fromDay + o.days;
  }

  // ---------- daily ----------
  private dailyHarvest() {
    const day = this.day;
    const p = this.params;
    for (let pi = 0; pi < this.nParcels; pi++) {
      const di = this.parcelDistrict[pi]!;
      const wf = this.weatherFactor[di * 370 + day]!;
      if (wf <= 0) continue;
      const cl = this.parcelCluster[pi]!;
      for (let c = 0; c < NC; c++) {
        const rem = this.parcelRemaining[pi * NC + c]!;
        if (rem <= 0.01) continue;
        const mat = this.parcelMaturity[pi * NC + c]!;
        if (day < mat) continue;
        const ramp = Math.min(1, (day - mat) / this.rampDays);
        const rate = p.harvestRatePerDay[COMMODITIES[c]!]!;
        let h = Math.min(rem, this.parcelInitial[pi * NC + c]! * rate * ramp * wf);
        if (rem - h < this.parcelInitial[pi * NC + c]! * 0.02) h = rem; // finish the tail
        if (h <= 0) continue;
        this.parcelRemaining[pi * NC + c] = rem - h;
        this.harvestedRawT += h;
        const retained = h * p.retentionShare;
        this.retainedT += retained;
        this.clusterOnFarm[cl * NC + c] = this.clusterOnFarm[cl * NC + c]! + h - retained;
      }
    }
  }

  private checkInvariants() {
    let onFarm = 0;
    for (let i = 0; i < this.clusterOnFarm.length; i++) onFarm += this.clusterOnFarm[i]!;
    let siteStock = 0;
    let shipped = 0;
    for (const s of this.sites) {
      for (let c = 0; c < NC; c++) siteStock += s.stock[c]!;
      shipped += s.cumShippedT;
    }
    let onTrucks = 0;
    for (const t of this.trucks) onTrucks += t.loadT;
    // note: grain on vessels is already inside `shipped` (cumShippedT accrues as the
    // shiploader draws stock), so there is no separate on-vessel term. Carry-in stocks
    // enter the system at t=0 and must balance alongside harvested grain.
    const rhs = this.retainedT + onFarm + onTrucks + siteStock + shipped;
    const diff = Math.abs(this.harvestedRawT + this.carryInT - rhs);
    if (diff > 1.0) {
      throw new Error(
        `MASS CONSERVATION VIOLATED day ${this.day}: harvested=${this.harvestedRawT.toFixed(1)} rhs=${rhs.toFixed(1)} diff=${diff.toFixed(2)}`,
      );
    }
    for (const s of this.sites) {
      let st = 0;
      for (let c = 0; c < NC; c++) {
        if (s.stock[c]! < -0.01) throw new Error(`NEGATIVE STOCK at ${s.name} c=${c} day ${this.day}`);
        st += s.stock[c]!;
      }
      // Storage is bounded by construction now (#29): carry-in is clamped at capacity,
      // farm trucks reserve their load at dispatch, and line-haul honours that
      // reservation before tipping — so no path can put a site past its capacity.
      // Counted rather than thrown, for the same reason as the queue cap below: a guard
      // that kills a running simulation is worse for a visitor than a wrong number, and
      // the regression sweep is where this has to be zero.
      if (st > s.capacityT + 0.01) {
        this.capacityBreaches++;
        if (this.debugEvents) {
          this.log({ t: this.tick, type: "capacity_over", site: s.idx, stock: st, cap: s.capacityT });
        }
      }
      // Queue length is bounded by construction now: chooseSite refuses a site whose line
      // plus committed inbound already reaches siteQueueMaxTrucks, and a truck books its
      // place at dispatch, so the sum cannot climb past the cap. Overshooting it therefore
      // means that gate has a bug — which is worth failing a test over, but not worth
      // killing a running simulation over (#26). The old `throw` here escaped sim.step()
      // into the worker and left the visitor with "Error: QUEUE INSANE at Thevenard: 408"
      // and no way back, on lever combinations the UI itself offers. Count it instead: the
      // regression sweep asserts this stays zero across every preset and lever extreme.
      if (s.queue.length > (this.params.siteQueueMaxTrucks ?? 250)) {
        this.queueCapBreaches++;
        if (this.debugEvents) {
          this.log({ t: this.tick, type: "queue_over_cap", site: s.idx, queue: s.queue.length });
        }
      }
    }
  }

  // ---------- site choice ----------
  /**
   * Where this load goes, or null for "nowhere today — it stays in the field bin".
   *
   * Three thresholds, in order of how hard they bite (#26/#27):
   *   queueBalkMin (4 h)      a grower would rather drive to another site
   *   queueBalkMaxMin (12 h)  a grower would rather not cart at all today
   *   siteQueueMaxTrucks      the site physically cannot hold another truck
   * The first is behavioural and soft: pass 1 relaxes it to the second when NO reachable
   * site clears it. The third is never relaxed. Before this, pass 1 dropped the queue
   * filter outright, so the balk rule bounded nothing whenever it actually mattered — it
   * only moved the pile-up a few hours later, onto whichever site the Huff draw picked
   * (#27), and the resulting 400+ truck lines tripped the engine's own guard and killed
   * the app mid-run (#26).
   */
  private chooseSite(cl: number, c: number): { site: number; minutes: number; km: number } | null {
    const p = this.params;
    const cand = this.clusterCand[cl]!;
    // scratch buffers, reused across calls: chooseSite runs once per idle truck per tick
    const weights = this.csWeights;
    const opts = this.csOpts;
    const open = this.csOpen;
    const openQueueMin = this.csOpenQueueMin;
    const maxQueue = p.siteQueueMaxTrucks ?? 250;
    // the load this truck is about to pick up is capped by its payload; the storage gate
    // below looks that far ahead, exactly as line-haul's arrival gate does (#29)
    const payloadT = p.truckPayloadT;
    // Growers deliver to a site they can realistically reach, or cart direct to port.
    // Without this window a shallow power-law over ~21 candidates sends most traffic to
    // mid-distance sites (measured: 62 min mean leg against a 24 min nearest-accepting
    // floor), which inflates cycle times, truck-km and the fitted fleet. Ports are always
    // candidates so the direct-to-port share (A9) stays governed by portAttractBias.
    //
    // One structural pass: everything that does not depend on the balk tolerance is
    // decided here, so the tolerance passes below re-walk a short array instead of the
    // full candidate list (which matters now that a jammed network can fail BOTH of them).
    open.length = 0;
    openQueueMin.length = 0;
    let nearest = Infinity;
    for (const cd of cand) {
      const s = this.sites[cd.site]!;
      if (!s.open || !s.accepts[c]) continue;
      if (this.portOutageActive(s) && s.isPort) continue;
      let st = 0;
      for (let k = 0; k < NC; k++) st += s.stock[k]!;
      // Storage: what is on the ground PLUS every tonne already rolling toward it, plus
      // the load this truck would add. Testing on-site stock alone (with a 0.5 % cushion)
      // let a dozen trucks each read the same nearly-full site as "room for me" in the
      // same tick, all get dispatched, and all tip — putting eight EP sites 0.2-2.2 %
      // past published capacity in the bumper run and six past it at the calibrated
      // baseline (#29). Once a truck is dispatched nothing stops it tipping, so the
      // reservation has to be taken HERE, at the only point where the choice is still
      // open. That makes `stock + siteInboundT <= capacityT` an invariant rather than a
      // hope, and a site that is full-by-commitment now drops out of the candidate list
      // exactly like one that is full-by-stock — including for the queue rules below.
      if (st + this.siteInboundT[cd.site]! + payloadT > s.capacityT) continue; // storage full
      // Trucks in the line plus trucks already committed to joining it: growers can see
      // site status/wait before setting off, so the choice must not ignore traffic that
      // is loaded and rolling. Counting inbound is also what makes the cap below a hard
      // bound rather than an aspiration — a truck books its place at dispatch, so
      // queue + inbound can never climb past maxQueue, and queue alone never can either.
      const inLine = s.queue.length + (this.siteInbound[cd.site] ?? 0);
      if (inLine >= maxQueue) continue; // no room left to stand: not a candidate, ever
      open.push(cd);
      openQueueMin.push((inLine * s.serviceMin) / s.bays);
      if (cd.minutes < nearest) nearest = cd.minutes;
    }
    if (!open.length) return null;
    const window = nearest * (p.choiceRadius ?? 1.5) + 10;

    const balkMin = p.queueBalkMin ?? 240;
    for (let pass = 0; pass < 2; pass++) {
      // Pass 0 applies the ordinary tolerance: the worst turnaround ever reported on EP is
      // ~4 h (Port Lincoln, Nov 2018 rail-outage congestion). Pass 1 runs only when that
      // left nothing, and stretches to queueBalkMaxMin — a full receival day — rather than
      // to infinity. A load that clears neither waits on farm, where the engine already
      // tracks and prices it (onFarmTonneDays, A22); that is the third state, not a crash.
      const tolerance = pass === 0 ? balkMin : Math.max(balkMin, p.queueBalkMaxMin ?? 720);
      weights.length = 0;
      opts.length = 0;
      for (let i = 0; i < open.length; i++) {
        const cd = open[i]!;
        const s = this.sites[cd.site]!;
        if (cd.minutes > window && !s.isPort) continue; // out of realistic reach
        const queueMin = openQueueMin[i]!;
        if (queueMin > tolerance) continue;
        let attract = 1.0;
        if (s.isPort) attract *= p.portAttractBias;
        if (s.isTports) attract *= p.luckyBayBias;
        const cost = cd.minutes + queueMin + s.serviceMin;
        weights.push(attract / Math.pow(cost, p.choiceBeta));
        opts.push(cd);
      }
      if (opts.length) break;
    }
    if (!opts.length) return null;
    // the fitted Huff draw is kept on both passes: it is already a soft argmin over
    // (travel + queue) minutes at the calibrated beta, so the stretched pass still sends
    // most loads to the least-bad site without swapping in a second, unfitted rule.
    return opts[this.rng.weighted(weights)]!;
  }

  // ---------- tick ----------
  step(nTicks = 1) {
    for (let k = 0; k < nTicks; k++) this.oneTick();
  }

  private oneTick() {
    const tick = this.tick;
    if (tick % DAY_TICKS === 0) {
      this.dailyHarvest();
      if (this.day > 0) this.checkInvariants();
      let onFarm = 0;
      for (let i = 0; i < this.clusterOnFarm.length; i++) onFarm += this.clusterOnFarm[i]!;
      this.onFarmTonneDays += onFarm;
      this.dailyBungeReceivals.push(this.receivedBungeT);
      if (this.day % 7 === 0 && this.debugEvents) {
        this.log({ t: tick, type: "week", received: Math.round(this.receivedBungeT) });
      }
    }
    const hourOfDay = (tick % DAY_TICKS) * TICK_MIN / 60;
    const sitesOpenNow = hourOfDay >= 7 && hourOfDay < 19; // receival hours (A2-adjacent assumption)

    // hourly: refresh line-haul port shortfalls (demand next 21 d - stock - inbound)
    if (this.portInboundT.length === 0) {
      this.portInboundT = new Float64Array(this.sites.length);
      this.cachedPortNeed = new Float64Array(this.sites.length);
    }
    if (tick % 12 === 0) {
      for (const s of this.sites) {
        if (!s.isPort) continue;
        let demand = 0;
        for (const v of this.vessels) {
          if (v.port === s.idx && v.state !== V_DONE && v.arriveTick < tick + 21 * DAY_TICKS) {
            demand += v.targetT - v.loadedT;
          }
        }
        let stock = 0;
        for (let c = 0; c < NC; c++) stock += s.stock[c]!;
        this.cachedPortNeed[s.idx] =
          s.open && !this.portOutageActive(s) ? demand - stock - this.portInboundT[s.idx]! : 0;
      }
    }

    // trucks
    for (const tr of this.trucks) {
      if (tr.kind === 0) this.stepFarmTruck(tr, sitesOpenNow);
      else this.stepLinehaul(tr);
    }

    // site bays: pull queued trucks into free bays
    for (const s of this.sites) {
      if (!s.open) continue;
      for (let b = 0; b < s.bays; b++) {
        if (s.bayBusyUntil[b]! <= tick && s.queue.length > 0) {
          const tid = s.queue.shift()!;
          const tr = this.trucks[tid]!;
          tr.state = T_TIP;
          tr.doneAt = tick + Math.ceil(s.serviceMin / TICK_MIN);
          s.bayBusyUntil[b] = tr.doneAt;
        }
      }
      if (s.queue.length > this.peakQueue) this.peakQueue = s.queue.length;
      const waitMin = (s.queue.length * s.serviceMin) / s.bays;
      if (waitMin > this.peakQueueMin) this.peakQueueMin = waitMin;
    }

    // vessels
    this.stepVessels();

    this.tick++;
  }

  private stepFarmTruck(tr: Truck, sitesOpenNow: boolean) {
    const tick = this.tick;
    const p = this.params;
    switch (tr.state) {
      case T_IDLE: {
        if (!sitesOpenNow) return;
        // rain suppresses deliveries too (EP harvest is largely header-direct to site,
        // so receivals track weather with little on-farm buffering): dispatch attempts
        // are skipped with probability 0.75 x (1 - weather factor)
        const cdist = this.clusterDistrict[tr.cluster] ?? 1;
        const wf = this.weatherFactor[cdist * 370 + this.day]!;
        if (wf < 1 && this.rng.next() < 0.75 * (1 - wf)) return;
        // pick largest on-farm commodity in home cluster
        let best = -1,
          bestT = 0;
        for (let c = 0; c < NC; c++) {
          const t = this.clusterOnFarm[tr.cluster * NC + c]!;
          if (t > bestT) {
            bestT = t;
            best = c;
          }
        }
        if (best < 0 || bestT < 5) return;
        const choice = this.chooseSite(tr.cluster, best);
        if (!choice) return;
        const load = Math.min(p.truckPayloadT, bestT);
        this.clusterOnFarm[tr.cluster * NC + best] = bestT - load;
        tr.commodity = best;
        tr.loadT = load;
        tr.site = choice.site;
        this.siteInbound[choice.site] = (this.siteInbound[choice.site] ?? 0) + 1;
        // book the storage as well as the place in the line (#29): released at the tip
        // that turns it into stock, so the two never double-count
        this.siteInboundT[choice.site] = (this.siteInboundT[choice.site] ?? 0) + load;
        tr.legMin = choice.minutes;
        tr.legKm = choice.km;
        tr.state = T_LOAD;
        tr.doneAt = tick + Math.ceil((30 * this.rng.range(0.8, 1.3)) / TICK_MIN);
        return;
      }
      case T_LOAD:
        if (tick >= tr.doneAt) {
          tr.state = T_GO;
          tr.legStart = tick;
          tr.doneAt = tick + Math.ceil(tr.legMin / TICK_MIN);
          this.truckTravelMin += tr.legMin * 2; // out + return
          this.truckKm += tr.legKm * 2; // loaded out, empty back
          this.tonneKm += tr.legKm * tr.loadT; // only the loaded direction carries tonnes
          const key = `c:${tr.cluster}-${tr.site}`;
          this.tripTonnesByPath.set(key, (this.tripTonnesByPath.get(key) ?? 0) + tr.loadT);
        }
        return;
      case T_GO:
        if (tick >= tr.doneAt) {
          const s = this.sites[tr.site]!;
          this.siteInbound[tr.site] = Math.max(0, (this.siteInbound[tr.site] ?? 1) - 1);
          tr.state = T_QUEUE;
          s.queue.push(tr.id);
        }
        return;
      case T_QUEUE:
        return; // bay pull handles transition
      case T_TIP:
        if (tick >= tr.doneAt) {
          const s = this.sites[tr.site]!;
          // reservation -> stock: the site's committed total is unchanged by this line,
          // which is why the gate in chooseSite can treat the sum as a hard ceiling (#29)
          this.siteInboundT[tr.site] = Math.max(0, this.siteInboundT[tr.site]! - tr.loadT);
          s.stock[tr.commodity] = s.stock[tr.commodity]! + tr.loadT;
          s.cumReceivedT += tr.loadT;
          if (s.isBunge) this.receivedBungeT += tr.loadT;
          else this.receivedLbT += tr.loadT;
          if (this.debugEvents) this.log({ t: tick, type: "tip", site: s.idx, t_t: tr.loadT, c: tr.commodity });
          tr.loadT = 0;
          tr.state = T_RETURN;
          tr.legStart = tick;
          tr.doneAt = tick + Math.ceil(tr.legMin / TICK_MIN);
        }
        return;
      case T_RETURN:
        if (tick >= tr.doneAt) tr.state = T_IDLE;
        return;
    }
  }

  /** line-haul: keep port stocks ahead of upcoming vessel demand (simple v1 policy) */
  private stepLinehaul(tr: Truck) {
    const tick = this.tick;
    switch (tr.state) {
      case T_IDLE: {
        // find the port with the biggest cached 21-day shortfall
        let bestPort = -1,
          bestNeed = 0;
        for (const s of this.sites) {
          if (!s.isPort) continue;
          const need = this.cachedPortNeed[s.idx]!;
          if (need > bestNeed) {
            bestNeed = need;
            bestPort = s.idx;
          }
        }
        if (bestPort < 0 || bestNeed < 40) return; // ~one truckload deadband
        const isTrain = tr.payloadT > 100;
        if (isTrain) {
          // trains only serve Port Lincoln from the old rail-line sites
          const pl = this.sites.findIndex((s) => s.name.includes("Lincoln"));
          if (pl < 0 || this.cachedPortNeed[pl]! < 40) return;
          bestPort = pl;
        }
        // source: Bunge upcountry site with max stock (T-Ports bunkers feed only Lucky Bay)
        const port = this.sites[bestPort]!;
        let src = -1,
          srcT = 0,
          srcC = -1;
        for (const s of this.sites) {
          if (s.isPort || !s.open) continue;
          if (port.isTports !== s.isTports) continue;
          if (isTrain && !RAIL_SITES.some((r) => s.name.includes(r))) continue;
          for (let c = 0; c < NC; c++) {
            if (s.stock[c]! > srcT) {
              srcT = s.stock[c]!;
              src = s.idx;
              srcC = c;
            }
          }
        }
        if (src < 0 || srcT < 100) return;
        // road-closure detour on the site->port leg (#28). Trainsets are exempt: the
        // scenario closes a HIGHWAY, and the narrow-gauge line is not on it.
        const closure = isTrain ? 1 : (this.closureSitePort?.[src]?.[bestPort] ?? 1);
        const roadMin = this.bundle.matrix.site_minutes[src]![bestPort]! * closure * (this.params.travelTimeScale ?? 1);
        if (roadMin <= 0) return;
        // routed network distance for this leg; both vehicles cover the same ground (#10)
        const legKm =
          (this.bundle.matrix.site_km?.[src]?.[bestPort] ??
            (this.bundle.matrix.site_minutes[src]![bestPort]! / 60) * FALLBACK_SPEED_KMH) * closure;
        // trains follow the same alignment but at rail line speed (A21), so their transit
        // comes off the distance, not off the road minutes -- the A5 road-speed lever is
        // not a lever on narrow-gauge line speed
        const minutes = isTrain ? (legKm / RAIL_SPEED_KMH) * 60 : roadMin;
        const load = Math.min(tr.payloadT, srcT); // road train ~45 t net; trainset 1,600 t
        const s = this.sites[src]!;
        s.stock[srcC] = s.stock[srcC]! - load;
        tr.commodity = srcC;
        tr.loadT = load;
        tr.site = src;
        tr.destPort = bestPort;
        tr.legMin = minutes;
        tr.legKm = legKm;
        tr.state = T_GO;
        tr.legStart = tick;
        // handling: ~1 h for a road train; ~4 h combined load/unload for a 1,600 t
        // trainset (A21). Cycle time = 2 x transit + handling, so a trainset manages
        // ~1.8 cycles/day on the Kimba/Wudinna lines and ~3.6 on the short Cummins run.
        const handlingMin = isTrain ? 240 : 60;
        tr.doneAt = tick + Math.ceil((minutes + handlingMin) / TICK_MIN);
        // distance is the same either way; only the vehicle and the time differ
        if (isTrain) {
          this.railTravelMin += minutes * 2;
          this.railTonneKm += legKm * load;
          this.railTrips++;
          this.railActiveDays.add(this.day);
        } else {
          this.truckTravelMin += minutes * 2;
          this.truckKm += legKm * 2; // loaded out, empty back
          this.tonneKm += legKm * load;
        }
        // the corridor layer is a TRUCK-flow heatmap: trainset tonnes are not road traffic,
        // and the rail corridors are exactly the ones this scenario is meant to empty
        if (!isTrain) {
          const lkey = `s:${src}-${bestPort}`;
          this.tripTonnesByPath.set(lkey, (this.tripTonnesByPath.get(lkey) ?? 0) + load);
        }
        this.portInboundT[bestPort] = this.portInboundT[bestPort]! + load;
        this.cachedPortNeed[bestPort] = this.cachedPortNeed[bestPort]! - load;
        return;
      }
      case T_GO:
        if (tick >= tr.doneAt) {
          const port = this.sites[tr.destPort]!;
          let stock = 0;
          for (let c = 0; c < NC; c++) stock += port.stock[c]!;
          // Room for this load: on-site stock, this truck's tonnes, and the farm loads
          // already rolling toward this port (#29). Without that last term a
          // line-haul truck could spend headroom a grower had already reserved, and the
          // grower's truck tips unconditionally on arrival — so the overshoot would land
          // on the farm side instead of being prevented. Only THIS truck's load is
          // tested against the remainder, not every line-haul truck en route: testing the
          // whole line-haul fleet's inbound would deadlock two trucks that each fit but do
          // not fit together. Arrivals are processed one at a time, so sequential tips
          // re-test against the stock the previous one just added.
          if (stock + this.siteInboundT[tr.destPort]! + tr.loadT > port.capacityT) {
            // port full: wait a tick (rare; policy shortfall)
            tr.doneAt = tick + 6;
            return;
          }
          port.stock[tr.commodity] = port.stock[tr.commodity]! + tr.loadT;
          this.portInboundT[tr.destPort] = Math.max(0, this.portInboundT[tr.destPort]! - tr.loadT);
          tr.loadT = 0;
          tr.state = T_RETURN;
          tr.doneAt = tick + Math.ceil(tr.legMin / TICK_MIN);
        }
        return;
      case T_RETURN:
        if (tick >= tr.doneAt) tr.state = T_IDLE;
        return;
      default:
        tr.state = T_IDLE;
    }
  }

  private stepVessels() {
    const tick = this.tick;
    for (const v of this.vessels) {
      const port = this.sites[v.port]!;
      switch (v.state) {
        case V_PENDING:
          if (tick >= v.arriveTick) {
            v.state = V_ANCHOR;
            this.log({ t: tick, type: "vessel_arrive", id: v.id, port: port.name, name: v.name });
          }
          break;
        case V_ANCHOR: {
          if (this.portOutageActive(port)) {
            v.waitTicks++;
            this.vesselWaitTicksTotal++;
            break;
          }
          let stock = 0;
          for (let c = 0; c < NC; c++) stock += port.stock[c]!;
          if (tick >= v.slotTick && port.berthsFree > 0 && stock > Math.min(2000, v.targetT * 0.1)) {
            port.berthsFree--;
            v.state = V_BERTH;
            v.berthedAt = tick;
            v.lastDrawTick = tick;
            if (v.commodity < 0) {
              // choose the port's largest stock commodity
              let best = 0,
                bestT = -1;
              for (let c = 0; c < NC; c++)
                if (port.stock[c]! > bestT) {
                  bestT = port.stock[c]!;
                  best = c;
                }
              v.commodity = best;
            }
            this.log({ t: tick, type: "vessel_berth", id: v.id, port: port.name, waitH: (v.waitTicks * TICK_MIN) / 60 });
          } else if (v.waitTicks >= VESSEL_GIVEUP_TICKS) {
            // a vessel program held for a crop that shrank should have been re-issued: after
            // ~2 weeks at anchor with no grain coming, the charterer re-nominates rather than
            // wait indefinitely — the vessel leaves without ever taking a berth, so it stops
            // consuming wait time (and doesn't tie up a berth other vessels need) (#6)
            v.state = V_DONE;
            this.log({ t: tick, type: "vessel_reissue", id: v.id, port: port.name, waitH: (v.waitTicks * TICK_MIN) / 60 });
          } else {
            v.waitTicks++;
            this.vesselWaitTicksTotal++;
          }
          break;
        }
        case V_BERTH: {
          // effective rate: Port Lincoln's single 3000 t/h circuit is shared across berths
          let rate = port.shiploaderTph;
          if (port.name.includes("Lincoln")) {
            const busy = 2 - port.berthsFree;
            rate = busy > 1 ? 1500 : 3000;
          }
          const want = Math.min((rate * TICK_MIN) / 60, v.targetT - v.loadedT);
          // draw preferred commodity first, then others (multi-commodity parcels)
          let drawn = 0;
          let c = v.commodity;
          const take = Math.min(want, port.stock[c]!);
          port.stock[c] = port.stock[c]! - take;
          drawn += take;
          if (drawn < want * 0.5) {
            for (let k = 0; k < NC && drawn < want; k++) {
              const t2 = Math.min(want - drawn, port.stock[k]!);
              port.stock[k] = port.stock[k]! - t2;
              drawn += t2;
            }
          }
          v.loadedT += drawn;
          port.cumShippedT += drawn;
          this.shippedT += drawn;
          if (drawn > 0) v.lastDrawTick = tick;
          // sail when the parcel is effectively complete (50 t tolerance), or when
          // starved at berth for 5 days (stock-out guard; logged as short-loaded)
          const complete = v.loadedT >= v.targetT - 50;
          const starved = tick - v.lastDrawTick > 5 * DAY_TICKS && v.loadedT > 0;
          if (complete || starved) {
            v.state = V_DONE;
            port.berthsFree++;
            this.log({
              t: tick, type: "vessel_sail", id: v.id, port: port.name,
              loaded: Math.round(v.loadedT), berthH: ((tick - v.berthedAt) * TICK_MIN) / 60,
              short: starved && !complete ? true : undefined,
            });
          }
          break;
        }
      }
    }
  }

  // ---------- outputs ----------
  snapshot(): Snapshot {
    const trucks: TruckView[] = [];
    for (const tr of this.trucks) {
      if (tr.state === T_IDLE) continue;
      let pathKey: string | null = null;
      let forward = true;
      let progress = 0;
      if (tr.state === T_GO || tr.state === T_RETURN) {
        const el = (this.tick - tr.legStart) / Math.max(1, tr.doneAt - tr.legStart);
        progress = Math.min(1, el);
        forward = tr.state === T_GO;
        pathKey = tr.kind === 0 ? `${tr.cluster}-${tr.site}` : `${tr.site}-${tr.destPort}`;
        if (tr.kind === 0) forward = tr.state === T_GO;
        else forward = tr.loadT > 0 ? true : false;
      } else if (tr.state === T_QUEUE || tr.state === T_TIP) {
        pathKey = tr.kind === 0 ? `${tr.cluster}-${tr.site}` : `${tr.site}-${tr.destPort}`;
        progress = 1;
      }
      trucks.push({
        id: tr.id,
        kind: tr.kind === 0 ? "farm" : "linehaul",
        state: tr.state,
        pathKey,
        forward,
        progress,
        commodity: tr.commodity,
      });
    }
    const sites: SiteView[] = this.sites.map((s) => {
      let st = 0;
      const byC: number[] = new Array(NC);
      for (let c = 0; c < NC; c++) {
        byC[c] = Math.round(s.stock[c]!);
        st += s.stock[c]!;
      }
      return {
        id: s.idx,
        stockT: Math.round(st),
        stockByC: byC,
        queue: s.queue.length,
        cumReceivedT: Math.round(s.cumReceivedT),
        capacityT: Math.round(s.capacityT),
      };
    });
    const vessels: VesselView[] = this.vessels
      .filter((v) => v.state === V_ANCHOR || v.state === V_BERTH || (v.state === V_DONE && this.tick - v.berthedAt < DAY_TICKS))
      .map((v) => ({
        id: v.id,
        port: v.port,
        state: v.state,
        loadedT: Math.round(v.loadedT),
        targetT: Math.round(v.targetT),
        name: v.name,
      }));
    const frac = new Float32Array(this.nParcels);
    for (let p = 0; p < this.nParcels; p++) {
      let init = 0,
        rem = 0;
      for (let c = 0; c < NC; c++) {
        init += this.parcelInitial[p * NC + c]!;
        rem += this.parcelRemaining[p * NC + c]!;
      }
      frac[p] = init > 0 ? 1 - rem / init : 0;
    }
    let vesselsWaiting = 0;
    for (const v of this.vessels) if (v.state === V_ANCHOR) vesselsWaiting++;
    let queueTrucks = 0;
    for (const s of this.sites) queueTrucks += s.queue.length;
    return {
      tick: this.tick,
      day: this.day,
      dateIso: this.dateIso(),
      trucks,
      sites,
      vessels,
      parcelHarvestFrac: frac,
      kpi: {
        harvestedT: Math.round(this.harvestedRawT),
        receivedT: Math.round(this.receivedBungeT),
        receivedLbT: Math.round(this.receivedLbT),
        shippedT: Math.round(this.shippedT),
        queueTrucks,
        vesselsWaiting,
        tonneKm: Math.round(this.tonneKm),
        railTonneKm: Math.round(this.railTonneKm),
        truckKm: Math.round(this.truckKm),
        meanWaitH: Math.round(this.meanVesselWaitHNow() * 10) / 10,
        peakQueue: this.peakQueue,
        vesselsArrived: this.vessels.reduce((a, v) => a + (v.state !== V_PENDING ? 1 : 0), 0),
        carryInT: Math.round(this.carryInT),
        onFarmTd: Math.round(this.onFarmTonneDays),
      },
    };
  }

  /** mean anchorage wait so far, hours per vessel that has arrived */
  meanVesselWaitHNow(): number {
    let n = 0;
    for (const v of this.vessels) if (v.state !== V_PENDING) n++;
    return n ? (this.vesselWaitTicksTotal * TICK_MIN) / 60 / n : 0;
  }

  /** cumulative loaded tonnes per path key, for the corridor heatmap */
  getTripTonnes(): Record<string, number> {
    const out: Record<string, number> = {};
    for (const [k, v] of this.tripTonnesByPath) out[k] = Math.round(v);
    return out;
  }

  /** headless full-season run + calibration series */
  run(days = 365): RunResult {
    const totalTicks = days * DAY_TICKS;
    while (this.tick < totalTicks) this.oneTick();
    // weekly Western receivals aligned to observed week endings
    const weekly: RunResult["weeklyWesternT"] = [];
    const obs = this.bundle.observed.weekly_receivals;
    for (const w of obs) {
      const end = Math.round((Date.parse(w.week_ending + "T23:59:59Z") - this.startUtc) / 86400000);
      const span = w.fortnight ? 14 : 7;
      const start = end - span;
      const cumAt = (d: number) => this.dailyBungeReceivals[Math.max(0, Math.min(this.dailyBungeReceivals.length - 1, d + 1))] ?? 0;
      const simT = cumAt(end) - cumAt(start);
      weekly.push({ weekEnding: w.week_ending, simT: Math.round(simT), obsT: w.western?.weekly_t ?? null });
    }
    let pl = 0;
    let vesselCount = 0;
    for (const s of this.sites) if (s.name.includes("Lincoln")) pl = s.cumShippedT;
    for (const v of this.vessels) if (v.state === V_DONE && this.sites[v.port]!.name.includes("Lincoln")) vesselCount++;
    // event log hash (fnv-1a over JSON lines)
    let h = 0x811c9dc5;
    for (const e of this.events) {
      const s = JSON.stringify(e);
      for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 0x01000193) >>> 0;
      }
    }
    const doneVessels = this.vessels.filter((v) => v.state === V_DONE).length;
    return {
      season: this.bundle.season,
      weeklyWesternT: weekly,
      seasonReceivedT: Math.round(this.receivedBungeT),
      seasonShippedPlT: Math.round(pl),
      vesselCount,
      meanVesselWaitH: doneVessels ? (this.vesselWaitTicksTotal * TICK_MIN) / 60 / doneVessels : 0,
      peakQueue: this.peakQueue,
      eventLogHash: ("0000000" + h.toString(16)).slice(-8),
      events: this.events,
    };
  }
}
