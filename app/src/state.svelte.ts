import type { BundleCluster, BundleSite, ObservedFile, Params, Snapshot } from "@windrow/sim";

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
  luckyBayBias: 0.651,
  fleetTrucks: 589,
  portAttractBias: 0.8,
  rail: false,
  outage: false,
  roadClosure: false,
};

export const SCENARIOS: { id: ScenarioId; label: string; story: string; levers: Partial<Levers> }[] = [
  { id: "baseline", label: "Baseline replay", story: "The season as it happened: observed production, observed vessel program, calibrated network.", levers: {} },
  { id: "bumper", label: "Bumper harvest (+30%)", story: "A big year. Watch site storage fill, queues build at peak, and surplus grain spill toward T-Ports.", levers: { productionScale: 1.3 } },
  { id: "drought", label: "Drought (−40%)", story: "A small crop against an unchanged export program: the land side relaxes but ships wait at anchor for grain that never comes.", levers: { productionScale: 0.6 } },
  { id: "rail", label: "Rail reinstated", story: "Two trainsets on the old Cummins/Kimba/Wudinna lines take over part of the port shuttle, easing peak road queues.", levers: { rail: true } },
  { id: "luckybay", label: "Lucky Bay share shift", story: "T-Ports made 2.5× more attractive: eastern-EP grain drains to Lucky Bay and out of the Bunge network.", levers: { luckyBayBias: 2.5 } },
  { id: "outage", label: "Port Lincoln outage (7 d)", story: "The terminal closes for a week at harvest peak. Deliveries redirect upcountry; the buffer holds — at a queueing price.", levers: { outage: true } },
  { id: "roadclosure", label: "Tod Hwy closure", story: "The central spine is impassable (2.5× travel time). Trucks re-sort to Lincoln-Highway-side sites.", levers: { roadClosure: true } },
];

export function leversToPatch(l: Levers): Partial<Params> {
  const p: Partial<Params> = {};
  if (l.productionScale !== 1.0) p.productionScale = l.productionScale;
  if (l.luckyBayBias !== DEFAULT_LEVERS.luckyBayBias) p.luckyBayBias = l.luckyBayBias;
  if (l.fleetTrucks !== DEFAULT_LEVERS.fleetTrucks) p.fleetTrucks = Math.round(l.fleetTrucks);
  if (l.portAttractBias !== DEFAULT_LEVERS.portAttractBias) p.portAttractBias = l.portAttractBias;
  if (l.rail) {
    p.railReinstated = true;
    p.linehaulTrucks = 32;
  }
  if (l.outage) p.outage = { port: "Lincoln", fromDay: 70, days: 7 };
  if (l.roadClosure) p.roadClosure = { corridor: "tod", factor: 2.5 };
  return p;
}

export const SEASONS = ["2023/24", "2024/25", "2025/26", "2026/27"];
export const SEASON_LABELS: Record<string, string> = {
  "2023/24": "2023/24",
  "2024/25": "2024/25 (drought · held-out)",
  "2025/26": "2025/26",
  "2026/27": "2026/27 (live · provisional)",
};

export interface BaselineSeries {
  receivedByDay: number[];
  shippedByDay: number[];
  tonneKmByDay: number[];
  lbByDay: number[];
  waitByDay: number[];
  queueByDay: number[];
  arrivedByDay: number[];
}

class AppState {
  season = $state("2025/26");
  scenario = $state<ScenarioId>("baseline");
  levers = $state<Levers>({ ...DEFAULT_LEVERS });
  playing = $state(false);
  speed = $state(3600); // sim-seconds per real second
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
