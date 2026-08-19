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
  { id: "baseline", label: "The season as it happened", story: "Real crop sizes, the real shipping program, and the network as it ran. The gold dashed line on the chart is what farmers actually delivered.", levers: {} },
  { id: "bumper", label: "Bumper harvest (+30%)", story: "A big year. Watch silos fill toward their limits, truck queues build at the peak, and surplus grain spill toward Lucky Bay.", levers: { productionScale: 1.3 } },
  { id: "drought", label: "Drought (−40%)", story: "A small crop against an unchanged shipping program: the roads and silos relax, but ships sit at anchor waiting for grain that never comes.", levers: { productionScale: 0.6 } },
  { id: "rail", label: "Bring back the trains", story: "Two trainsets return to the old Cummins–Kimba–Wudinna lines and take over part of the silo-to-port shuttle, taking millions of truck-kilometres off the highways.", levers: { rail: true } },
  { id: "luckybay", label: "More grain to Lucky Bay", story: "T-Ports' Lucky Bay made 2.5× more attractive: eastern-peninsula grain drains away from the main network.", levers: { luckyBayBias: 2.5 } },
  { id: "outage", label: "Port Lincoln closed a week", story: "The port terminal shuts for a week at harvest peak. Deliveries redirect to country silos — the system holds, at a queueing price.", levers: { outage: true } },
  { id: "roadclosure", label: "Tod Highway closed", story: "The peninsula's central spine is impassable (detours = 2.5× travel time). Trucks re-sort toward Lincoln Highway sites.", levers: { roadClosure: true } },
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
  "2024/25": "2024/25 — drought year",
  "2025/26": "2025/26",
  "2026/27": "2026/27 — live (forecast)",
};

export type ViewMode = "simple" | "advanced";

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
