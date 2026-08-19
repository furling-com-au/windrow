/** Shared sim types. The bundle shapes mirror app/public/data/*.json (pipeline outputs). */

export const COMMODITIES = ["wheat", "barley", "canola", "lentils", "beans", "other"] as const;
export type Commodity = (typeof COMMODITIES)[number];
export const NC = COMMODITIES.length;

export interface BundleParcel {
  id: number;
  lon: number;
  lat: number;
  district: "WEP" | "LEP" | "EEP";
  cropping_ha: number;
  cluster_id: number;
}

export interface BundleSite {
  id: number;
  name: string;
  role: "port" | "upcountry";
  operator: string;
  status: string;
  lon: number;
  lat: number;
  capacity_t: number | null;
  commodities: string[];
}

export interface BundleCluster {
  id: number;
  lon: number;
  lat: number;
  cropping_ha: number;
  district: "WEP" | "LEP" | "EEP";
  n_parcels: number;
}

export interface Matrix {
  sites: BundleSite[];
  site_minutes: number[][];
  clusters: BundleCluster[];
  cluster_site_minutes: Record<string, Record<string, number>>;
}

export interface VesselVisit {
  craft_id: number;
  arrive: string; // ISO datetime of berthing (AIS berth-visit start)
  anchor_arrive?: string | null; // ISO datetime of arrival at anchorage (AIS-linked)
  observed_wait_h?: number | null;
  berth_hours: number;
  est_cargo_t: number;
  name_candidate?: string;
  stem_volume_t?: number | null;
  stem_commodity?: string | null;
}

export interface VesselsFile {
  season: string;
  port_lincoln_berth_visits: VesselVisit[];
  lucky_bay_anchorage_stays: { craft_id: number; arrive: string; anchor_hours: number }[];
  thevenard_berth_visits_all_cargo: { craft_id: number; arrive: string; berth_hours: number }[];
}

export interface WeatherFile {
  season: string;
  districts: Record<
    "WEP" | "LEP" | "EEP",
    { start: string; rain_mm: number[]; tmax_c: number[]; rh_min_pct: number[]; wind_max_kmh: number[] }
  >;
}

export interface ObservedWeek {
  week_ending: string;
  fortnight: boolean;
  total?: { weekly_t: number | null; cum_t: number | null };
  western?: { weekly_t: number | null; cum_t: number | null };
}

export interface CarryIn {
  port_lincoln_t: number;
  thevenard_t: number;
  upcountry_t: number;
  provenance: string;
}

export interface ChartAnnotation {
  day: number; // season day (0 = 1 Oct)
  label: string;
  kind: "first" | "record" | "rain";
}

export interface ObservedFile {
  season: string;
  first_delivery: string | null;
  weekly_receivals: ObservedWeek[];
  port_lincoln_shipments_monthly: { year: number; month: number; commodity: string; export_t: number }[];
  district_production_t: Record<string, number>;
  carry_in?: CarryIn;
  annotations?: ChartAnnotation[];
}

export interface DemandFile {
  season: string;
  parcels: { id: number; crops: Record<string, number> }[];
}

export interface Bundle {
  season: string;
  parcels: BundleParcel[];
  demand: DemandFile;
  matrix: Matrix;
  vessels: VesselsFile | null;
  weather: WeatherFile;
  observed: ObservedFile;
}

/** Scenario/parameter set — the ~10 calibratable knobs + scenario switches. */
export interface Params {
  fleetTrucks: number; // farm truck fleet across the region
  linehaulTrucks: number;
  truckPayloadT: number; // average net payload (A1 blended)
  harvestRatePerDay: Record<Commodity, number>; // fraction of a parcel's remaining crop harvestable per good day
  maturityDayOffset: Record<Commodity, number>; // days after season start when harvest can begin (base)
  districtStartOffset: Record<"WEP" | "LEP" | "EEP", number>;
  harvestRampDays: number; // days for a parcel to ramp 0->full harvest rate after maturity
  choiceBeta: number; // Huff decay exponent on (travel+queue) minutes
  portAttractBias: number; // multiplier on port attractiveness for direct-to-port share
  retentionShare: number; // fraction of production never delivered (seed/feed/on-farm)
  luckyBayBias: number; // attractiveness multiplier for T-Ports system (market share)
  // scenario switches
  productionScale: number; // 1.0 baseline; 1.3 bumper; 0.6 drought
  railReinstated: boolean; // adds high-capacity Cummins->PL + Wudinna->PL line-haul
  outage: { port: string; fromDay: number; days: number } | null;
  roadClosure: { corridor: "lincoln" | "tod" | "flinders" | "birdseye"; factor: number } | null;
}

export interface SimEvent {
  t: number; // tick
  type: string;
  [k: string]: unknown;
}

export interface Snapshot {
  tick: number;
  day: number;
  dateIso: string;
  trucks: TruckView[];
  sites: SiteView[];
  vessels: VesselView[];
  parcelHarvestFrac: Float32Array;
  kpi: {
    harvestedT: number;
    receivedT: number; // Bunge network (Western) receivals
    receivedLbT: number; // T-Ports system intake
    shippedT: number;
    queueTrucks: number;
    vesselsWaiting: number;
    tonneKm: number; // loaded truck tonne-km to date
    truckKm: number; // total truck km (loaded + empty) to date
    meanWaitH: number; // mean vessel anchorage wait so far (h/vessel arrived)
    peakQueue: number; // worst single-site truck queue so far
    vesselsArrived: number;
  };
}

export interface TruckView {
  id: number;
  kind: "farm" | "linehaul";
  state: number; // TruckState enum
  pathKey: string | null; // "cid-sid" or "si-pj" into paths.json
  forward: boolean; // travelling toward site/port?
  progress: number; // 0..1 along path
  commodity: number;
}

export interface SiteView {
  id: number;
  stockT: number;
  stockByC: number[]; // per COMMODITIES order, tonnes
  queue: number;
  cumReceivedT: number;
}

export interface VesselView {
  id: number;
  port: number; // site index of port
  state: number; // 0 pending 1 anchored 2 berthed 3 departed
  loadedT: number;
  targetT: number;
  name: string | null;
}

export interface RunResult {
  season: string;
  weeklyWesternT: { weekEnding: string; simT: number; obsT: number | null }[];
  seasonReceivedT: number;
  seasonShippedPlT: number;
  vesselCount: number;
  meanVesselWaitH: number;
  peakQueue: number;
  eventLogHash: string;
  events: SimEvent[];
}
