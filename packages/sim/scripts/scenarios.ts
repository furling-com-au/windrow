/**
 * Phase 5: run the v1 scenario set headless against the baseline and report deltas.
 *   npx tsx scripts/scenarios.ts [season]
 * Emits docs/scenarios_data.json for the write-up.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Params, RunResult } from "../src/types";
import { loadBundle } from "./load_bundle";

const season = process.argv[2] ?? "2025/26";

const SCENARIOS: { id: string; label: string; patch: Partial<Params> }[] = [
  { id: "baseline", label: "Baseline replay", patch: {} },
  { id: "bumper", label: "Bumper (+30%)", patch: { productionScale: 1.3 } },
  { id: "drought", label: "Drought (-40%)", patch: { productionScale: 0.6 } },
  { id: "rail", label: "Rail reinstated", patch: { railReinstated: true, linehaulTrucks: Math.round((defaultParams().linehaulTrucks * 2) / 3) } },
  { id: "luckybay", label: "Lucky Bay share shift", patch: { luckyBayBias: 2.5 } },
  { id: "outage", label: "Port Lincoln outage (7 d @ day 70)", patch: { outage: { port: "Lincoln", fromDay: 70, days: 7 } } },
  { id: "roadclosure", label: "Tod Hwy closure (x2.5)", patch: { roadClosure: { corridor: "tod", factor: 2.5 } } },
];

interface ScenarioOut {
  id: string;
  label: string;
  receivedMt: number;
  receivedLbMt: number;
  shippedPlMt: number;
  vesselCount: number;
  meanVesselWaitH: number;
  peakQueue: number;
  truckKmProxy: number; // sum of farm-truck travel minutes (relative measure)
  peakWeekKt: number;
}

const bundle = loadBundle(season);
const out: ScenarioOut[] = [];
for (const sc of SCENARIOS) {
  const params: Params = { ...defaultParams(), ...sc.patch };
  const sim = new Sim(bundle, params, 42);
  const res: RunResult = sim.run(365);
  const peakWeek = Math.max(0, ...res.weeklyWesternT.map((w) => w.simT));
  out.push({
    id: sc.id,
    label: sc.label,
    receivedMt: +(res.seasonReceivedT / 1e6).toFixed(3),
    receivedLbMt: +(sim.receivedLbT / 1e6).toFixed(3),
    shippedPlMt: +(res.seasonShippedPlT / 1e6).toFixed(3),
    vesselCount: res.vesselCount,
    meanVesselWaitH: +res.meanVesselWaitH.toFixed(1),
    peakQueue: res.peakQueue,
    truckKmProxy: Math.round(sim.truckTravelMin * (75 / 60)), // minutes -> ~km at 75 km/h mean
    peakWeekKt: Math.round(peakWeek / 1000),
  });
  console.log(`${sc.id.padEnd(12)} received ${(res.seasonReceivedT / 1e6).toFixed(2)} Mt | LB ${(sim.receivedLbT / 1e6).toFixed(2)} | shipped PL ${(res.seasonShippedPlT / 1e6).toFixed(2)} | peakQ ${res.peakQueue} | wait ${res.meanVesselWaitH.toFixed(1)} h | peak wk ${Math.round(peakWeek / 1000)} kt`);
}
writeFileSync(join(import.meta.dirname, "..", "..", "..", "docs", "scenarios_data.json"), JSON.stringify({ season, scenarios: out }, null, 2));
console.log("wrote docs/scenarios_data.json");
