/** Headless season run: npx tsx scripts/run_headless.ts 2025/26 [seed] */
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import { loadBundle } from "./load_bundle";

const season = process.argv[2] ?? "2025/26";
const seed = parseInt(process.argv[3] ?? "42", 10);

const bundle = loadBundle(season);
const t0 = performance.now();
const sim = new Sim(bundle, defaultParams(), seed);
const res = sim.run(365);
const ms = performance.now() - t0;

console.log(`season ${season} seed ${seed}: ran 365 days in ${(ms / 1000).toFixed(2)} s`);
console.log(`received (Bunge Western): ${(res.seasonReceivedT / 1e6).toFixed(3)} Mt  | observed harvest cum: ${(
  (bundle.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 0) / 1e6
).toFixed(3)} Mt`);
console.log(`shipped Port Lincoln: ${(res.seasonShippedPlT / 1e6).toFixed(3)} Mt | vessels loaded: ${res.vesselCount}`);
console.log(`mean vessel wait: ${res.meanVesselWaitH.toFixed(1)} h | peak site queue: ${res.peakQueue} trucks`);
console.log(`event log hash: ${res.eventLogHash} (${res.events.length} events)`);
console.log("\nweekly Western receivals (sim vs observed, kt):");
for (const w of res.weeklyWesternT) {
  const bar = (v: number) => "#".repeat(Math.round(v / 20000));
  console.log(
    `${w.weekEnding}  sim ${(w.simT / 1000).toFixed(0).padStart(4)}  obs ${((w.obsT ?? 0) / 1000)
      .toFixed(0)
      .padStart(4)}  ${bar(w.simT)}`,
  );
}
