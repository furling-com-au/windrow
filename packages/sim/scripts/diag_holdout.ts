import { readFileSync } from "node:fs";
import { join } from "node:path";
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Params } from "../src/types";
import { loadBundle } from "./load_bundle";

const b = loadBundle("2024/25");

// 1) weather around the observed 1 Dec 2024 receival collapse (season days ~54-63)
for (const dn of ["WEP", "LEP", "EEP"] as const) {
  const w = b.weather.districts[dn];
  const start = Date.parse(w.start + "T00:00:00Z");
  const oct1 = Date.UTC(2024, 9, 1);
  const off = Math.round((oct1 - start) / 86400000);
  const rain = w.rain_mm.slice(off + 52, off + 64).map((r) => r.toFixed(1));
  console.log(`${dn} rain Nov22-Dec3:`, rain.join(" "));
}

// 2) calibrated run: where does the grain go?
const cal = JSON.parse(readFileSync(join(import.meta.dirname, "..", "src", "calibrated.json"), "utf-8"));
const params: Params = { ...defaultParams(), ...cal.params };
const sim = new Sim(b, params, 42);
const res = sim.run(365);
const s = sim.snapshot();
let siteStock = 0;
for (const sv of s.sites) siteStock += sv.stockT;
console.log(`\nreceived Bunge ${(res.seasonReceivedT / 1e6).toFixed(3)} Mt | LB system ${(sim.receivedLbT / 1e6).toFixed(3)} Mt`);
console.log(`harvested ${(s.kpi.harvestedT / 1e6).toFixed(3)} Mt | shipped ${(s.kpi.shippedT / 1e6).toFixed(3)} Mt | end site+port stocks ${(siteStock / 1e6).toFixed(3)} Mt`);
const deliverable = s.kpi.harvestedT * (1 - params.retentionShare);
console.log(`deliverable ${(deliverable / 1e6).toFixed(3)} Mt | delivered total ${((res.seasonReceivedT + sim.receivedLbT) / 1e6).toFixed(3)} Mt | undelivered on-farm ${((deliverable - res.seasonReceivedT - sim.receivedLbT) / 1e6).toFixed(3)} Mt`);
