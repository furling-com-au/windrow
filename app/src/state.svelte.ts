import type { BundleCluster, BundleSite, ObservedFile, Params, Snapshot } from "@windrow/sim";

export type ScenarioId =
  | "baseline"
  | "bumper"
  | "drought"
  | "rail"
  | "luckybay"
  | "outage"
  | "roadclosure";

export const SCENARIOS: { id: ScenarioId; label: string; desc: string; patch: Partial<Params> }[] = [
  { id: "baseline", label: "Baseline replay", desc: "Observed production, observed vessel program.", patch: {} },
  { id: "bumper", label: "Bumper (+30%)", desc: "Production scaled 1.3x — watch site storage and queues.", patch: { productionScale: 1.3 } },
  { id: "drought", label: "Drought (-40%)", desc: "Production scaled 0.6x.", patch: { productionScale: 0.6 } },
  { id: "rail", label: "Rail reinstated", desc: "Adds rail-equivalent line-haul capacity Cummins/Wudinna -> Port Lincoln.", patch: { railReinstated: true, linehaulTrucks: 25 } },
  { id: "luckybay", label: "Lucky Bay share shift", desc: "T-Ports attractiveness doubled — grain drains east.", patch: { luckyBayBias: 2.5 } },
  { id: "outage", label: "Terminal outage", desc: "Port Lincoln closed for 7 days at harvest peak (day 70).", patch: { outage: { port: "Lincoln", fromDay: 70, days: 7 } } },
  { id: "roadclosure", label: "Tod Hwy closure", desc: "Tod Highway corridor impassable through harvest (detour factor 2.5x).", patch: { roadClosure: { corridor: "tod", factor: 2.5 } } },
];

// 2022/23 exists in the data bundle but is excluded from the UI: it pre-dates AIS
// coverage and its bumper volumes sit outside the calibrated fleet envelope (see
// docs/calibration_report.md).
export const SEASONS = ["2023/24", "2024/25", "2025/26"];

class AppState {
  season = $state("2025/26");
  scenario = $state<ScenarioId>("baseline");
  playing = $state(false);
  speed = $state(3600); // sim-seconds per real second
  snap = $state<Snapshot | null>(null);
  observed = $state<ObservedFile | null>(null);
  sites = $state<BundleSite[]>([]);
  clusters = $state<BundleCluster[]>([]);
  loading = $state(true);
  error = $state<string | null>(null);
  done = $state(false);
  showAbout = $state(false);
}

export const app = new AppState();
