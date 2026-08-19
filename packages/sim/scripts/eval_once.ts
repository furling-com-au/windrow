/** Evaluate the current calibrated knobs once per season (used for quick A/B checks). */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Params } from "../src/types";
import { loadBundle } from "./load_bundle";

const cal = JSON.parse(readFileSync(join(import.meta.dirname, "..", "src", "calibrated.json"), "utf-8"));
const params: Params = { ...defaultParams(), ...cal.params };
for (const season of ["2023/24", "2025/26", "2024/25"]) {
  const b = loadBundle(season);
  const res = new Sim(b, params, 42).run(365);
  const obsTotal = b.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 1;
  const cmp = res.weeklyWesternT.filter((w) => w.obsT !== null);
  const meanObs = cmp.reduce((a, w) => a + (w.obsT ?? 0), 0) / Math.max(1, cmp.length);
  const rmse = Math.sqrt(cmp.reduce((a, w) => a + (w.simT - (w.obsT ?? 0)) ** 2, 0) / Math.max(1, cmp.length));
  console.log(
    `${season}${season === "2024/25" ? " (HOLDOUT)" : ""}: total ${(res.seasonReceivedT / 1e6).toFixed(3)} vs ${(obsTotal / 1e6).toFixed(3)} Mt (${((100 * (res.seasonReceivedT - obsTotal)) / obsTotal).toFixed(1)}%), weeklyRMSE/mean ${((100 * rmse) / meanObs).toFixed(0)}%`,
  );
  if (season === "2024/25") {
    for (const w of res.weeklyWesternT) if (w.obsT !== null) console.log(`  ${w.weekEnding} sim ${(w.simT / 1000).toFixed(0)} obs ${((w.obsT ?? 0) / 1000).toFixed(0)}`);
  }
}
