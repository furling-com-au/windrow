/**
 * Headless calibration (spec Phase 3): random search over 11 free scalars, fitted
 * against data/CALIBRATION.md targets on 2023/24 + 2025/26; 2024/25 is HELD OUT.
 *
 *   npx tsx scripts/calibrate.ts [nSamples]
 *
 * Objective per calibration season:
 *   weekly relative RMSE (weekly Western receivals, obs weeks only)  x 1.0
 *   |season received - observed harvest cum| / observed              x 2.0
 *   |PL shipped - vessel-target total| / target                      x 0.3
 * Deterministic: the search RNG is seeded; every sim run uses seed 42.
 * Writes best params to src/calibrated.json and a search log to
 * ../../docs/calibration_search.json (report is authored in Phase 5).
 */
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import { Rng } from "../src/rng";
import type { Bundle, Params } from "../src/types";
import { loadBundle } from "./load_bundle";

const CAL_SEASONS = ["2023/24", "2025/26"];
const N = parseInt(process.argv[2] ?? "80", 10);

interface Knobs {
  fleetTrucks: number;
  linehaulTrucks: number;
  rateScale: number;
  matShift: number;
  harvestRampDays: number;
  retentionShare: number;
  portAttractBias: number;
  choiceBeta: number;
  choiceRadius: number;
  countryBays: number;
  portBays: number;
  luckyBayBias: number;
}

function applyKnobs(k: Knobs): Params {
  const p = defaultParams();
  p.fleetTrucks = Math.round(k.fleetTrucks);
  p.linehaulTrucks = Math.round(k.linehaulTrucks);
  for (const c of Object.keys(p.harvestRatePerDay) as (keyof typeof p.harvestRatePerDay)[]) {
    p.harvestRatePerDay[c] = p.harvestRatePerDay[c]! * k.rateScale;
  }
  for (const c of Object.keys(p.maturityDayOffset) as (keyof typeof p.maturityDayOffset)[]) {
    p.maturityDayOffset[c] = p.maturityDayOffset[c]! + k.matShift;
  }
  p.harvestRampDays = k.harvestRampDays;
  p.retentionShare = k.retentionShare;
  p.portAttractBias = k.portAttractBias;
  p.choiceBeta = k.choiceBeta;
  p.choiceRadius = k.choiceRadius;
  p.countryBays = Math.round(k.countryBays);
  p.portBays = Math.round(k.portBays);
  p.luckyBayBias = k.luckyBayBias;
  return p;
}

function score(bundles: Bundle[], k: Knobs): { total: number; parts: Record<string, number> } {
  let total = 0;
  const parts: Record<string, number> = {};
  for (const b of bundles) {
    const sim = new Sim(b, applyKnobs(k), 42);
    const res = sim.run(365);
    const obsWeeks = res.weeklyWesternT.filter((w) => w.obsT !== null);
    const obsTotal = b.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 1;
    let sq = 0;
    for (const w of obsWeeks) sq += (w.simT - (w.obsT ?? 0)) ** 2;
    const rmse = Math.sqrt(sq / Math.max(1, obsWeeks.length)) / (obsTotal / obsWeeks.length);
    const totErr = Math.abs(res.seasonReceivedT - obsTotal) / obsTotal;
    const targetShip = (b.vessels?.port_lincoln_berth_visits ?? []).reduce((a, v) => a + (v.est_cargo_t || 0), 0);
    const shipErr = targetShip > 0 ? Math.abs(res.seasonShippedPlT - targetShip) / targetShip : 0;
    const s = rmse * 1.0 + totErr * 2.0 + shipErr * 0.3;
    parts[b.season] = s;
    total += s;
  }
  return { total, parts };
}

const bundles = CAL_SEASONS.map((s) => loadBundle(s));
const rng = new Rng(2026);
const ranges: Record<keyof Knobs, [number, number]> = {
  fleetTrucks: [300, 900],
  linehaulTrucks: [25, 80],
  rateScale: [0.7, 2.2],
  matShift: [-4, 16],
  harvestRampDays: [5, 22],
  retentionShare: [0.1, 0.28],
  portAttractBias: [0.8, 2.8],
  choiceBeta: [1.1, 3.5],
  choiceRadius: [1.05, 3.0],
  countryBays: [3, 5],
  portBays: [5, 7],
  luckyBayBias: [0.4, 2.2],
};

function sample(): Knobs {
  const k = {} as Knobs;
  for (const key of Object.keys(ranges) as (keyof Knobs)[]) {
    const [lo, hi] = ranges[key];
    k[key] = rng.range(lo, hi);
  }
  return k;
}

const t0 = performance.now();
let best: { k: Knobs; s: number; parts: Record<string, number> } | null = null;
const log: { k: Knobs; s: number }[] = [];
for (let i = 0; i < N; i++) {
  const k = sample();
  const { total, parts } = score(bundles, k);
  log.push({ k, s: total });
  if (!best || total < best.s) {
    best = { k, s: total, parts };
    console.log(`#${i} new best ${total.toFixed(3)} ${JSON.stringify(parts)} ${JSON.stringify(k)}`);
  }
}
// local refinement around the best
for (let i = 0; i < Math.round(N / 2); i++) {
  const k = { ...best!.k };
  for (const key of Object.keys(ranges) as (keyof Knobs)[]) {
    const [lo, hi] = ranges[key];
    const span = (hi - lo) * 0.12;
    k[key] = Math.min(hi, Math.max(lo, k[key] + rng.range(-span, span)));
  }
  const { total, parts } = score(bundles, k);
  log.push({ k, s: total });
  if (total < best!.s) {
    best = { k, s: total, parts };
    console.log(`refine new best ${total.toFixed(3)} ${JSON.stringify(parts)}`);
  }
}
const secs = (performance.now() - t0) / 1000;
console.log(`\nsearch done in ${secs.toFixed(0)} s; best score ${best!.s.toFixed(3)}`);
console.log(JSON.stringify(best!.k, null, 2));

const calibrated = applyKnobs(best!.k);
writeFileSync(join(import.meta.dirname, "..", "src", "calibrated.json"), JSON.stringify({ knobs: best!.k, params: calibrated, score: best!.s, parts: best!.parts, nEvaluations: log.length }, null, 2));
writeFileSync(
  join(import.meta.dirname, "..", "..", "..", "docs", "calibration_search.json"),
  JSON.stringify({ calSeasons: CAL_SEASONS, holdout: "2024/25", ranges, evaluations: log.length, best: best!.k, bestScore: best!.s }, null, 2),
);

// validation preview on the held-out season
try {
  const hb = loadBundle("2024/25");
  const sim = new Sim(hb, calibrated, 42);
  const res = sim.run(365);
  const obsTotal = hb.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 1;
  console.log(`\nHELD-OUT 2024/25: sim received ${(res.seasonReceivedT / 1e6).toFixed(3)} Mt vs obs ${(obsTotal / 1e6).toFixed(3)} Mt (${((100 * (res.seasonReceivedT - obsTotal)) / obsTotal).toFixed(1)} %)`);
  for (const w of res.weeklyWesternT) {
    if (w.obsT !== null) console.log(`  ${w.weekEnding} sim ${(w.simT / 1000).toFixed(0).padStart(4)} obs ${((w.obsT ?? 0) / 1000).toFixed(0).padStart(4)}`);
  }
} catch (e) {
  console.warn("holdout preview failed:", e);
}
