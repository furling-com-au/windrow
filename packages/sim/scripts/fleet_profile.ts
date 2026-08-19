/**
 * Profile the calibration objective along the fleet axis alone (all other calibrated
 * knobs held at their fitted values), using the SAME score the calibrator used:
 *   s = weeklyRMSE/meanWeek + 2*|totalErr| + 0.3*|shipErr|
 * If the curve is flat or monotone across the search range [350, 750], the fitted 589
 * is not an identified optimum.
 *
 * Run: npx tsx packages/sim/scripts/fleet_profile.ts
 */
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import { loadBundle } from "./load_bundle";

const bundles = ["2023/24", "2025/26"].map((s) => loadBundle(s));

function calibratorScore(fleet: number) {
  let total = 0;
  const signed: number[] = [];
  for (const b of bundles) {
    const p = defaultParams();
    p.fleetTrucks = fleet;
    const res = new Sim(b, p, 42).run(365);
    const obsWeeks = res.weeklyWesternT.filter((w) => w.obsT !== null);
    const obsTotal = b.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 1;
    let sq = 0;
    for (const w of obsWeeks) sq += (w.simT - (w.obsT ?? 0)) ** 2;
    const rmse = Math.sqrt(sq / Math.max(1, obsWeeks.length)) / (obsTotal / obsWeeks.length);
    const totErr = Math.abs(res.seasonReceivedT - obsTotal) / obsTotal;
    signed.push((100 * (res.seasonReceivedT - obsTotal)) / obsTotal);
    const targetShip = (b.vessels?.port_lincoln_berth_visits ?? []).reduce((a: number, v: any) => a + (v.est_cargo_t || 0), 0);
    const shipErr = targetShip > 0 ? Math.abs(res.seasonShippedPlT - targetShip) / targetShip : 0;
    total += rmse * 1.0 + totErr * 2.0 + shipErr * 0.3;
  }
  return { total, signed };
}

console.log("fleet   calibrator score (lower=better)   season error 23/24, 25/26");
console.log("-----   -----------------------------   -------------------------");
for (const fleet of [350, 450, 550, 589, 650, 750, 850, 1000]) {
  const { total, signed } = calibratorScore(fleet);
  const bar = "#".repeat(Math.max(0, Math.round((total - 1.0) * 60)));
  const flag = fleet === 589 ? "  <- fitted" : fleet === 750 ? "  <- top of search range" : "";
  console.log(`${String(fleet).padStart(5)}   ${total.toFixed(4).padStart(29)}   ${signed.map((s) => `${s >= 0 ? "+" : ""}${s.toFixed(1)}%`).join(", ").padStart(25)} ${bar}${flag}`);
}
