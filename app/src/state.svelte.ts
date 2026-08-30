import { defaultParams } from "@windrow/sim";
import type { BundleCluster, BundleSite, ObservedFile, Params, Snapshot } from "@windrow/sim";

/** the calibrated parameter set is the single source of truth for every default the
 *  UI shows: hardcoding copies here let them drift silently after a re-calibration. */
const CAL = defaultParams();

export type ScenarioId =
  | "baseline"
  | "bumper"
  | "drought"
  | "rail"
  | "luckybay"
  | "outage"
  | "roadclosure"
  | "custom";

/** the interactive levers a stakeholder can drag; scenarios are presets of these */
export interface Levers {
  productionScale: number; // 0.5 .. 1.4
  luckyBayBias: number; // 0.2 .. 3
  fleetTrucks: number; // 300 .. 800
  portAttractBias: number; // 0.4 .. 2.5 (direct-to-port pull)
  rail: boolean;
  outage: boolean; // Port Lincoln closed 7 d at day 70
  roadClosure: boolean; // Tod Hwy x2.5
}

export const DEFAULT_LEVERS: Levers = {
  productionScale: 1.0,
  luckyBayBias: CAL.luckyBayBias,
  fleetTrucks: CAL.fleetTrucks,
  portAttractBias: CAL.portAttractBias,
  rail: false,
  outage: false,
  roadClosure: false,
};

/** slider bounds that always bracket the calibrated value */
export const FLEET_MIN = Math.max(50, Math.round((CAL.fleetTrucks * 0.5) / 10) * 10);
export const FLEET_MAX = Math.round((CAL.fleetTrucks * 1.6) / 10) * 10;

export const SCENARIOS: { id: ScenarioId; label: string; story: string; levers: Partial<Levers> }[] = [
  { id: "baseline", label: "The season as it happened", story: "Real crop sizes, the real shipping program, and the network as it ran. The gold dashed line on the chart is what farmers actually delivered.", levers: {} },
  { id: "bumper", label: "Bumper harvest (+30%)", story: "A big year. Watch silos fill toward their limits, truck queues build at the peak, and surplus grain spill toward Lucky Bay.", levers: { productionScale: 1.3 } },
  { id: "drought", label: "Drought (−40%)", story: "A small crop against an unchanged shipping program: the roads and silos relax, but ships sit at anchor waiting for grain that never comes.", levers: { productionScale: 0.6 } },
  { id: "rail", label: "Bring back the trains", story: "Two trainsets return to the old Cummins–Kimba–Wudinna lines and take over part of the silo-to-port shuttle. How much trucking that saves depends on how big the trucks it replaces are: about 2.2 million truck-km against 45 t loads, but only ~0.9 million against the 85 t road trains SA law actually permits. Either way, the figures below count only the trucking saved — NOT what rebuilding and running a railway would cost, which is why the real line closed in 2019.", levers: { rail: true } },
  { id: "luckybay", label: "More grain to Lucky Bay", story: "T-Ports' Lucky Bay made 2.5× more attractive — like posting roughly a $6/t cash premium at a typical eastern-peninsula farm (A23). Grain drains away from the main network.", levers: { luckyBayBias: 2.5 } },
  { id: "outage", label: "Port Lincoln closed a week", story: "The port terminal shuts for a week at harvest peak. Deliveries redirect to country silos — the system holds, at a queueing price.", levers: { outage: true } },
  { id: "roadclosure", label: "Tod Highway closed", story: "The peninsula's central spine is impassable (detours = 2.5× travel time). Trucks re-sort toward Lincoln Highway sites.", levers: { roadClosure: true } },
];

/** assumption levers: defaults = the registered assumptions (A1/A2/A5/A7/A12/A17/A4) */
export interface AssumpLevers {
  payloadT: number; // A1 (farm -> site)
  lhPayloadT: number; // A1 (site -> port line-haul)
  serviceMin: number; // A2
  travelScale: number; // A5
  rainStopMm: number; // A7
  retention: number; // A12 (fitted, but a model guess growers may dispute)
  carryInScale: number; // A17
  capScale: number; // A4
}
export const DEFAULT_ASSUMP: AssumpLevers = {
  payloadT: CAL.truckPayloadT,
  lhPayloadT: CAL.linehaulPayloadT,
  serviceMin: CAL.siteServiceMin,
  travelScale: CAL.travelTimeScale,
  rainStopMm: CAL.rainStopMm,
  retention: CAL.retentionShare,
  carryInScale: CAL.carryInScale,
  capScale: CAL.upcountryCapScale,
};

/** dollar-rate levers (display-only; never affect the sim) */
export interface EconLevers {
  freightPerTKm: number; // A18
  shipDayCost: number; // A19
  holdingPerTDay: number; // A22
}
export const DEFAULT_ECON: EconLevers = { freightPerTKm: 0.1, shipDayCost: 30000, holdingPerTDay: 0.09 };

export function leversToPatch(l: Levers, a: AssumpLevers): Partial<Params> {
  const p: Partial<Params> = {};
  if (l.productionScale !== 1.0) p.productionScale = l.productionScale;
  if (l.luckyBayBias !== DEFAULT_LEVERS.luckyBayBias) p.luckyBayBias = l.luckyBayBias;
  if (l.fleetTrucks !== DEFAULT_LEVERS.fleetTrucks) p.fleetTrucks = Math.round(l.fleetTrucks);
  if (l.portAttractBias !== DEFAULT_LEVERS.portAttractBias) p.portAttractBias = l.portAttractBias;
  if (l.rail) {
    p.railReinstated = true;
    // A21: the trains take over part of the shuttle, so the road line-haul fleet is cut
    // by a third — same rule the headless scenario set applies (scripts/scenarios.ts).
    p.linehaulTrucks = Math.round((CAL.linehaulTrucks * 2) / 3);
  }
  if (l.outage) p.outage = { port: "Lincoln", fromDay: 70, days: 7 };
  if (l.roadClosure) p.roadClosure = { corridor: "tod", factor: 2.5 };
  if (a.payloadT !== DEFAULT_ASSUMP.payloadT) p.truckPayloadT = a.payloadT;
  if (a.lhPayloadT !== DEFAULT_ASSUMP.lhPayloadT) p.linehaulPayloadT = a.lhPayloadT;
  if (a.serviceMin !== DEFAULT_ASSUMP.serviceMin) p.siteServiceMin = a.serviceMin;
  if (a.travelScale !== DEFAULT_ASSUMP.travelScale) p.travelTimeScale = a.travelScale;
  if (a.rainStopMm !== DEFAULT_ASSUMP.rainStopMm) p.rainStopMm = a.rainStopMm;
  if (a.retention !== DEFAULT_ASSUMP.retention) p.retentionShare = a.retention;
  if (a.carryInScale !== DEFAULT_ASSUMP.carryInScale) p.carryInScale = a.carryInScale;
  if (a.capScale !== DEFAULT_ASSUMP.capScale) p.upcountryCapScale = a.capScale;
  return p;
}

export const SEASONS = ["2023/24", "2024/25", "2025/26", "2026/27"];
export const SEASON_LABELS: Record<string, string> = {
  "2023/24": "2023/24",
  "2024/25": "2024/25 — drought year",
  "2025/26": "2025/26",
  "2026/27": "2026/27 — live (forecast)",
};

export type ViewMode = "simple" | "advanced";

export interface BaselineSeries {
  receivedByDay: number[];
  shippedByDay: number[];
  tonneKmByDay: number[];
  truckKmByDay: number[];
  lbByDay: number[];
  waitByDay: number[];
  queueByDay: number[];
  arrivedByDay: number[];
  onFarmTdByDay: number[];
}

class AppState {
  season = $state("2025/26");
  scenario = $state<ScenarioId>("baseline");
  levers = $state<Levers>({ ...DEFAULT_LEVERS });
  assump = $state<AssumpLevers>({ ...DEFAULT_ASSUMP });
  econ = $state<EconLevers>({ ...DEFAULT_ECON });
  viewMode = $state<ViewMode>(
    typeof localStorage !== "undefined" && localStorage.getItem("windrow_mode") === "advanced" ? "advanced" : "simple",
  );
  playing = $state(false);
  speed = $state(86400); // sim-seconds per real second (1 day/s default)
  snap = $state<Snapshot | null>(null);
  observed = $state<ObservedFile | null>(null);
  sites = $state<BundleSite[]>([]);
  clusters = $state<BundleCluster[]>([]);
  baseline = $state<BaselineSeries | null>(null);
  selectedSite = $state<number | null>(null);
  heatmapOn = $state(false);
  heatmap = $state<Record<string, number> | null>(null);
  loading = $state(true);
  error = $state<string | null>(null);
  done = $state(false);
  showAbout = $state(false);
  showTour = $state(false);
  tourStep = $state(0);
}

export const app = new AppState();
