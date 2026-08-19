/**
 * Is the fitted fleet size (589) actually identified by the data, or does it just
 * absorb the assumed payload (A1, 38 t)?
 *
 * Sweeps payload x fleet and reports fit quality (season total error + weekly RMSE)
 * on the calibration seasons. If lines of constant fleet*payload all fit equally well,
 * the data pins down the TONNAGE FLOW, not the number of trucks.
 *
 * Run: npx tsx packages/sim/scripts/fleet_identifiability.ts
 */
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import { loadBundle } from "./load_bundle";

const SEASONS = ["2023/24", "2025/26"];
const bundles = SEASONS.map((s) => ({ season: s, b: loadBundle(s) }));

function score(fleet: number, payload: number) {
  let totErr = 0;
  let rmsePct = 0;
  for (const { b } of bundles) {
    const p = defaultParams();
    p.fleetTrucks = fleet;
    p.truckPayloadT = payload;
    const res = new Sim(b, p, 42).run(365);
    const obsTotal = b.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 1;
    totErr += Math.abs((res.seasonReceivedT - obsTotal) / obsTotal);
    const cmp = res.weeklyWesternT.filter((w) => w.obsT !== null);
    const meanObs = cmp.reduce((a, w) => a + (w.obsT ?? 0), 0) / Math.max(1, cmp.length);
    const rmse = Math.sqrt(cmp.reduce((a, w) => a + (w.simT - (w.obsT ?? 0)) ** 2, 0) / Math.max(1, cmp.length));
    rmsePct += (100 * rmse) / meanObs;
  }
  return { totErrPct: (100 * totErr) / bundles.length, rmsePct: rmsePct / bundles.length };
}

console.log("payload  fleet   fleet*payload   |total err|   weeklyRMSE/mean");
console.log("-------  -----   -------------   -----------   ---------------");

// the calibrated point, then equal-capacity points at other payloads,
// then off-capacity points to show what the data DOES constrain
const CAL_CAPACITY = 589 * 38;
const rows: Array<[number, number, string]> = [
  [38, 589, "calibrated"],
  [28, Math.round(CAL_CAPACITY / 28), "semis only, equal capacity"],
  [45, Math.round(CAL_CAPACITY / 45), "B-double mix, equal capacity"],
  [55, Math.round(CAL_CAPACITY / 55), "road trains, equal capacity"],
  [68, Math.round(CAL_CAPACITY / 68), "AB-triples, equal capacity"],
  [38, 300, "half the fitted fleet (control)"],
  [38, 900, "1.5x the fitted fleet (control)"],
];

for (const [payload, fleet, label] of rows) {
  const s = score(fleet, payload);
  console.log(
    `${String(payload).padStart(7)}  ${String(fleet).padStart(5)}   ${String(fleet * payload).padStart(13)}   ${s.totErrPct.toFixed(2).padStart(10)}%   ${s.rmsePct.toFixed(1).padStart(14)}%   ${label}`,
  );
}
