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

const SEG_TO_COMMODITY: Record<string, Commodity> = {
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
  intakeTph: number;
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
  legStart: number; // tick when leg started
}

/** historical EP rail-served sites (rail scenario): Cummins/Kimba/Wudinna lines -> Port Lincoln */
const RAIL_SITES = ["Cummins", "Kimba", "Wudinna"];

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
  private clusterCand: { site: number; minutes: number }[][];

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
  truckTravelMin = 0; // loaded+empty travel minutes (truck-km proxy for corridor analysis)
  tonneKm = 0; // loaded tonne-km (economics layer)
  carryInT = 0; // opening stocks seeded from observed Oct-Nov shipments (A17)
  /** cumulative loaded tonnes per rendered path ("cid-sid" farm, "si-pj" line-haul) */
  tripTonnesByPath = new Map<string, number>();

  events: SimEvent[] = [];
  private debugEvents: boolean;
  private portInboundT: Float64Array = new Float64Array(0);
  private cachedPortNeed: Float64Array = new Float64Array(0);

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
        const tmax = w.tmax_c[i] ?? 25;
        let f = 1.0;
        if (rain >= 5 || rain2 >= 10) f = 0; // A7
        else if (rain >= 2) f = 0.5;
        // hangover: paddocks stay wet after a heavy fall (A7)
        if ((w.rain_mm[i - 1] ?? 0) >= 8) f *= 0.3;
        else if ((w.rain_mm[i - 2] ?? 0) >= 8) f *= 0.5;
        if (tmax >= 38) f *= 0.75;
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
    for (const s of bundle.matrix.sites) {
      const isTports = s.operator.includes("T-Ports");
      const isPort = s.role === "port";
      let open = true;
      if (s.status === "dormant") open = false;
      // T-Ports Lock & Kimba bunkers: closed 2025/26 (documented) and assumed not
      // operated in drought 2024/25 (A15 - unverified, crop too small to fill them)
      if (isTports && !isPort && (season === "2025/26" || season === "2024/25")) open = false;
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
      const name = s.name;
      const capacityT =
        s.capacity_t ??
        (isTports ? 145000 : 120000); // A4: unpublished upcountry capacity (assumed)
      const st: SiteState = {
        idx: this.sites.length,
        name,
        isPort,
        isBunge: !isTports,
        isTports,
        open,
        capacityT,
        stock: new Float64Array(NC),
        bays: isPort ? 4 : 2,
        bayBusyUntil: [],
        queue: [],
        serviceMin: 12, // A2
        accepts,
        cumReceivedT: 0,
        intakeTph: isPort ? (name.includes("Lincoln") ? 4000 : name.includes("Thevenard") ? 1400 : 1000) : 600,
        shiploaderTph: name.includes("Lincoln") ? 3000 : name.includes("Thevenard") ? 1000 : 417, // LB = 10 kt/day transshipment
        berthsFree: name.includes("Lincoln") ? 2 : 1,
        cumShippedT: 0,
      };
      st.bayBusyUntil = new Array(st.bays).fill(0);
      this.sites.push(st);
    }
    // scenario: port outage handled in step()

    // ---- carry-in stocks (A17): seed opening stocks from observed Oct-Nov shipments ----
    const ci = bundle.observed.carry_in;
    if (ci) {
      const SPLIT: [number, number][] = [
        [COMMODITIES.indexOf("wheat"), 0.55],
        [COMMODITIES.indexOf("barley"), 0.3],
        [COMMODITIES.indexOf("lentils"), 0.15],
      ];
      const seed = (siteIdx: number, tonnes: number) => {
        if (siteIdx < 0 || tonnes <= 0) return;
        const s = this.sites[siteIdx]!;
        for (const [c, share] of SPLIT) s.stock[c] = s.stock[c]! + tonnes * share;
        this.carryInT += tonnes;
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
      const cand: { site: number; minutes: number }[] = [];
      for (const [sid, min] of Object.entries(m)) {
        cand.push({ site: parseInt(sid, 10), minutes: min });
      }
      cand.sort((a, b) => a.minutes - b.minutes);
      this.clusterCand.push(cand);
    }

    // ---- road closure scenario: straight-line corridor heuristic ----
    if (params.roadClosure) {
      const corridors: Record<string, [number, number, number, number]> = {
        // lon1, lat1, lon2, lat2 rough corridor axes
        lincoln: [135.87, -34.72, 136.45, -33.05],
        tod: [135.73, -34.27, 135.46, -33.05],
        flinders: [135.86, -34.72, 134.21, -32.8],
        birdseye: [135.76, -33.57, 136.93, -33.68],
      };
      const [x1, y1, x2, y2] = corridors[params.roadClosure.corridor]!;
      const near = (ax: number, ay: number, bx: number, by: number) => {
        // does segment a-b pass within ~0.15 deg of corridor segment? (coarse)
        const midx = (ax + bx) / 2,
          midy = (ay + by) / 2;
        const t = Math.max(
          0,
          Math.min(1, ((midx - x1) * (x2 - x1) + (midy - y1) * (y2 - y1)) / ((x2 - x1) ** 2 + (y2 - y1) ** 2)),
        );
        const px = x1 + t * (x2 - x1),
          py = y1 + t * (y2 - y1);
        return Math.hypot(midx - px, midy - py) < 0.18;
      };
      for (let cl = 0; cl < this.nClusters; cl++) {
        const c = clusters[cl]!;
        for (const cand of this.clusterCand[cl]!) {
          const s = bundle.matrix.sites[cand.site]!;
          if (near(c.lon, c.lat, s.lon, s.lat)) cand.minutes *= params.roadClosure.factor;
        }
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
        payloadT: 45,
        doneAt: 0,
        legMin: 0,
        legStart: 0,
      });
    }
    if (params.railReinstated) {
      // two trainsets shuttling the old Cummins/Kimba/Wudinna lines into Port Lincoln
      for (let k = 0; k < 2; k++) {
        this.trucks.push({
          id: id++, kind: 1, state: T_IDLE, cluster: -1, site: -1, destPort: -1,
          commodity: -1, loadT: 0, payloadT: 1600, doneAt: 0, legMin: 0, legStart: 0,
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
      for (let c = 0; c < NC; c++) {
        if (s.stock[c]! < -0.01) throw new Error(`NEGATIVE STOCK at ${s.name} c=${c} day ${this.day}`);
      }
      if (s.queue.length > 400) throw new Error(`QUEUE INSANE at ${s.name}: ${s.queue.length}`);
    }
  }

  // ---------- site choice ----------
  private chooseSite(cl: number, c: number): { site: number; minutes: number } | null {
    const p = this.params;
    const cand = this.clusterCand[cl]!;
    const weights: number[] = [];
    const opts: { site: number; minutes: number }[] = [];
    for (const cd of cand) {
      const s = this.sites[cd.site]!;
      if (!s.open || !s.accepts[c]) continue;
      if (this.portOutageActive(s) && s.isPort) continue;
      let stockTotal = 0;
      for (let k = 0; k < NC; k++) stockTotal += s.stock[k]!;
      if (stockTotal >= s.capacityT * 0.995) continue; // full
      const queueMin = (s.queue.length * s.serviceMin) / s.bays;
      let attract = 1.0;
      if (s.isPort) attract *= p.portAttractBias;
      if (s.isTports) attract *= p.luckyBayBias;
      const cost = cd.minutes + queueMin + s.serviceMin;
      weights.push(attract / Math.pow(cost, p.choiceBeta));
      opts.push(cd);
    }
    if (!opts.length) return null;
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
      this.peakQueue = Math.max(this.peakQueue, s.queue.length);
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
        tr.legMin = choice.minutes;
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
          const km = (tr.legMin / 60) * 75; // mean 75 km/h (A5-derived)
          this.tonneKm += km * tr.loadT;
          const key = `c:${tr.cluster}-${tr.site}`;
          this.tripTonnesByPath.set(key, (this.tripTonnesByPath.get(key) ?? 0) + tr.loadT);
        }
        return;
      case T_GO:
        if (tick >= tr.doneAt) {
          const s = this.sites[tr.site]!;
          tr.state = T_QUEUE;
          s.queue.push(tr.id);
        }
        return;
      case T_QUEUE:
        return; // bay pull handles transition
      case T_TIP:
        if (tick >= tr.doneAt) {
          const s = this.sites[tr.site]!;
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
        const minutes = this.bundle.matrix.site_minutes[src]![bestPort]!;
        if (minutes <= 0) return;
        const load = Math.min(tr.payloadT, srcT); // road train ~45 t net; trainset 1,600 t
        const s = this.sites[src]!;
        s.stock[srcC] = s.stock[srcC]! - load;
        tr.commodity = srcC;
        tr.loadT = load;
        tr.site = src;
        tr.destPort = bestPort;
        tr.legMin = minutes;
        tr.state = T_GO;
        tr.legStart = tick;
        // handling: ~1 h for a road train; ~4 h combined load/unload for a 1,600 t
        // trainset (A21) — caps trains at a realistic ~2 cycles/day
        const handlingMin = isTrain ? 240 : 60;
        tr.doneAt = tick + Math.ceil((minutes + handlingMin) / TICK_MIN);
        this.truckTravelMin += minutes * 2;
        this.tonneKm += (minutes / 60) * 75 * load;
        const lkey = `s:${src}-${bestPort}`;
        this.tripTonnesByPath.set(lkey, (this.tripTonnesByPath.get(lkey) ?? 0) + load);
        this.portInboundT[bestPort] = this.portInboundT[bestPort]! + load;
        this.cachedPortNeed[bestPort] = this.cachedPortNeed[bestPort]! - load;
        return;
      }
      case T_GO:
        if (tick >= tr.doneAt) {
          const port = this.sites[tr.destPort]!;
          let stock = 0;
          for (let c = 0; c < NC; c++) stock += port.stock[c]!;
          if (stock + tr.loadT > port.capacityT) {
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
      return { id: s.idx, stockT: Math.round(st), stockByC: byC, queue: s.queue.length, cumReceivedT: Math.round(s.cumReceivedT) };
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
        truckKm: Math.round((this.truckTravelMin / 60) * 75),
        meanWaitH: Math.round(this.meanVesselWaitHNow() * 10) / 10,
        peakQueue: this.peakQueue,
        vesselsArrived: this.vessels.reduce((a, v) => a + (v.state !== V_PENDING ? 1 : 0), 0),
        carryInT: Math.round(this.carryInT),
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
