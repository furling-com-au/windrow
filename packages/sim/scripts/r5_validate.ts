/**
 * R5 — retrospective validation (the go/no-go gate in docs/analysis_plan_ep_competition.md).
 *
 *   npx tsx packages/sim/scripts/r5_validate.ts
 *
 * Runs at the EXISTING fitted vector (`{...defaultParams(), ...calibrated.json.params}`,
 * the same construction docs/calibration_report.md uses), seed 42, 365 days. Nothing here
 * refits anything: the whole point of the gate is that the model either reproduces an
 * observed redistribution at frozen parameters or it does not.
 *
 * Part 1 — Test A feasibility probe (2019 closure of six ex-Viterra sites).
 * Part 2 — Test B (T-Ports Lock/Kimba bunkers), season x bunker-state grid.
 *
 * Deterministic; writes nothing.
 */
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Params } from "../src/types";
import { loadBundle } from "./load_bundle";

const ROOT = join(import.meta.dirname, "..", "..", "..");
const DATA = join(ROOT, "app", "public", "data");
const cal = JSON.parse(readFileSync(join(import.meta.dirname, "..", "src", "calibrated.json"), "utf-8"));
const FITTED: Params = { ...defaultParams(), ...cal.params };
const SEED = 42;
const BUNKERS = ["Lock (T-Ports bunker)", "Kimba (T-Ports bunker)"];

const kt = (t: number) => (t / 1000).toFixed(0);
const mt = (t: number) => (t / 1e6).toFixed(3);
const pct = (x: number) => (x * 100).toFixed(2);
const hr = (s: string) => console.log(`\n${"=".repeat(78)}\n${s}\n${"=".repeat(78)}`);

// ---------------------------------------------------------------------------
// Part 1 — can Test A be run at all?
// ---------------------------------------------------------------------------
hr("PART 1 - Test A (2019 closure of six sites): feasibility probe");

const ALL_SEASONS = [
  "2016/17", "2017/18", "2018/19", "2019/20", "2020/21",
  "2021/22", "2022/23", "2023/24", "2024/25", "2025/26",
];
console.log("\nModel INPUT bundles present per season (the sim cannot run a season without");
console.log("demand + weather; observed is the comparison target):\n");
console.log("  season    demand  weather  observed  vessels   runnable");
const runnable: string[] = [];
for (const s of ALL_SEASONS) {
  const sid = s.replace("/", "-");
  const has = (f: string) => existsSync(join(DATA, f));
  const d = has(`demand_${sid}.json`);
  const w = has(`weather_${sid}.json`);
  const o = has(`observed_${sid}.json`);
  const v = has(`vessels_${sid}.json`);
  const ok = d && w && o;
  if (ok) runnable.push(s);
  const y = (b: boolean) => (b ? "  yes " : "  NO  ");
  console.log(`  ${s}  ${y(d)}   ${y(w)}  ${y(o)}   ${y(v)}    ${ok ? "yes" : "NO"}`);
}
console.log(`\n  runnable seasons: ${runnable.join(", ")}`);
console.log("  The 2019 closure needs pre-closure seasons (2016/17-2018/19). None is runnable.");

// the six closed-2019 sites: present in sites.geojson, absent from the engine's input
const geo = JSON.parse(readFileSync(join(DATA, "sites.geojson"), "utf-8"));
const closed2019 = geo.features
  .filter((f: any) => String(f.properties.status ?? "").startsWith("closed_2019"))
  .map((f: any) => f.properties.name as string);
const matrixNames = new Set(JSON.parse(readFileSync(join(DATA, "matrix.json"), "utf-8")).sites.map((s: any) => s.name));
console.log(`\n  sites.geojson features: ${geo.features.length}   matrix.json sites: ${matrixNames.size}`);
console.log(`  closed-2019 sites in sites.geojson (${closed2019.length}): ${closed2019.join(", ")}`);
console.log(`  ...of those present in matrix.json (the engine's input): ${closed2019.filter((n: string) => matrixNames.has(n)).length}`);

// what geography the observed series actually resolves
const obs2526 = JSON.parse(readFileSync(join(DATA, "observed_2025-26.json"), "utf-8"));
const wk = obs2526.weekly_receivals[0] ?? {};
console.log(`\n  finest observed geography carried in a bundle week: ${Object.keys(wk).filter((k) => k !== "week_ending" && k !== "fortnight").join(", ")}`);
console.log("  'western' = the whole Eyre Peninsula (data/CALIBRATION.md: \"Western is EP-only\").");
console.log("  Every closed site AND every surviving neighbour sits inside that one bucket.");

// ---------------------------------------------------------------------------
// Part 2 — Test B: the T-Ports Lock/Kimba bunkers
// ---------------------------------------------------------------------------
hr("PART 2 - Test B (T-Ports Lock/Kimba bunkers): season x bunker-state grid");

interface Arm {
  season: string;
  state: "open" | "closed";
  bungeT: number;
  tportsT: number;
  epProdT: number;
  obsBungeT: number;
  perSite: Map<string, number>;
}

function runArm(season: string, state: "open" | "closed"): Arm {
  const bundle = loadBundle(season);
  const params: Params = {
    ...FITTED,
    networkState: state === "open" ? { forceOpen: BUNKERS } : { forceClosed: BUNKERS },
  };
  const sim = new Sim(bundle, params, SEED);
  const res = sim.run(365);
  const perSite = new Map<string, number>();
  for (const s of sim.sites) perSite.set(s.name, s.cumReceivedT);
  const epProdT = Object.values(bundle.observed.district_production_t as Record<string, number>).reduce((a, b) => a + b, 0);
  return {
    season,
    state,
    bungeT: res.seasonReceivedT,
    tportsT: sim.receivedLbT,
    epProdT,
    obsBungeT: bundle.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 0,
    perSite,
  };
}

// The seasons in the grid, and what the record says the bunkers did in each. ONE table
// drives both the printed note and the "state matches observed" test below; until
// 2026-09-06 they were two independent encodings, so revising A15 in one would have left
// the gate table attributing error to the wrong arm.
const SEASONS = ["2022/23", "2023/24", "2024/25", "2025/26"] as const;
const OBSERVED: Record<(typeof SEASONS)[number], { state: "open" | "closed"; note: string }> = {
  "2022/23": { state: "open", note: "OPEN  (both, published)   " },
  "2023/24": { state: "open", note: "OPEN  (both, published)   " },
  "2024/25": { state: "closed", note: "closed (ASSUMED - A15)    " },
  "2025/26": { state: "closed", note: "CLOSED (published)        " },
};

const grid: Arm[] = [];
for (const season of SEASONS) {
  for (const state of ["open", "closed"] as const) grid.push(runArm(season, state));
}

console.log("\nObserved (Tier 1, no model):\n");
console.log("  season    bunkers (verified?)          EP prod Mt   obs Bunge Mt   obs Bunge/prod");
for (const season of SEASONS) {
  const a = grid.find((g) => g.season === season)!;
  console.log(`  ${season}  ${OBSERVED[season].note}   ${mt(a.epProdT)}        ${mt(a.obsBungeT)}          ${pct(a.obsBungeT / a.epProdT)} %`);
}

console.log("\nSimulated at the fitted vector, both bunker states forced explicitly:\n");
console.log("  season    state    Bunge Mt   T-Ports Mt   Bunge/prod   err vs obs Bunge");
for (const a of grid) {
  // obsBungeT is the cumulative at the LAST PUBLISHED week, which ends on a different date
  // each season (2023-12-31 for 2023/24, into January for the others); the sim total is the
  // full 365 days. At the fitted vector the sim's harvest is over by every one of those
  // dates, so the comparison is consistent, but it is a convention, not a like-for-like.
  const err = a.state === OBSERVED[a.season as (typeof SEASONS)[number]].state
    ? `${(((a.bungeT - a.obsBungeT) / a.obsBungeT) * 100).toFixed(1)} % (state matches observed)`
    : "- (counterfactual arm)";
  console.log(`  ${a.season}  ${a.state.padEnd(7)}  ${mt(a.bungeT)}      ${mt(a.tportsT)}       ${pct(a.bungeT / a.epProdT)} %     ${err}`);
}

console.log("\nThe model's own bunker effect (closed minus open), at frozen parameters:\n");
console.log("  season    d Bunge kt   d T-Ports kt   d Bunge/prod pp");
for (const season of SEASONS) {
  const o = grid.find((g) => g.season === season && g.state === "open")!;
  const c = grid.find((g) => g.season === season && g.state === "closed")!;
  const dpp = ((c.bungeT - o.bungeT) / o.epProdT) * 100;
  console.log(`  ${season}  ${kt(c.bungeT - o.bungeT).padStart(9)}    ${kt(c.tportsT - o.tportsT).padStart(9)}       ${dpp >= 0 ? "+" : ""}${dpp.toFixed(2)}`);
}

console.log("\nObserved comparison the plan asks for (open season vs closed season):");
const o2324 = grid.find((g) => g.season === "2023/24" && g.state === "open")!;
const c2526 = grid.find((g) => g.season === "2025/26" && g.state === "closed")!;
const obsShift = (c2526.obsBungeT / c2526.epProdT - o2324.obsBungeT / o2324.epProdT) * 100;
const o2223 = grid.find((g) => g.season === "2022/23" && g.state === "open")!;
console.log(`  observed 2023/24 (open) -> 2025/26 (closed): ${obsShift >= 0 ? "+" : ""}${obsShift.toFixed(2)} pp of EP production`);
console.log(`  but observed 2022/23, ALSO bunkers-open, sits at ${pct(o2223.obsBungeT / o2223.epProdT)} % —`);
console.log(`  ABOVE the closed 2025/26 season's ${pct(c2526.obsBungeT / c2526.epProdT)} %. The two open seasons straddle the closed one.`);

console.log("\nWhere the model sends the bunker tonnes, 2025/26 (counterfactual, NOT validated):\n");
{
  const o = grid.find((g) => g.season === "2025/26" && g.state === "open")!;
  const c = grid.find((g) => g.season === "2025/26" && g.state === "closed")!;
  const rows = [...c.perSite.keys()]
    .map((n) => ({ n, d: (c.perSite.get(n) ?? 0) - (o.perSite.get(n) ?? 0) }))
    .filter((r) => Math.abs(r.d) >= 1000)
    .sort((a, b) => b.d - a.d);
  console.log("  site                      d received kt (closed - open)");
  for (const r of rows) console.log(`  ${r.n.padEnd(26)} ${(r.d / 1000).toFixed(1).padStart(8)}`);
}

// ---------------------------------------------------------------------------
// Part 3 — is the model's bunker effect a number, or a free parameter?
// ---------------------------------------------------------------------------
hr("PART 3 - bunker effect across the A24 identification ridge (no refitting)");

console.log("\nA24 records that `luckyBayBias` and `retentionShare` are NOT separately");
console.log("identified: every tonne taken off retention reappears at Lucky Bay at almost no");
console.log("cost to the objective. luckyBayBias is also the knob that decides how attractive");
console.log("the bunkers are — so it is the knob the Test B effect is measured through.");
console.log("Below: luckyBayBias swept over its OWN published search range (0.4-2.2,");
console.log("docs/calibration_search.json), every other knob frozen at the fitted vector.\n");
console.log("  luckyBayBias   Bunge open Mt   Bunge closed Mt   d pp   err vs obs: open / closed");
{
  const bundle = loadBundle("2025/26");
  const epProd = Object.values(bundle.observed.district_production_t as Record<string, number>).reduce((a, b) => a + b, 0);
  const obs = bundle.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 0;
  for (const lb of [0.4, 0.6, 0.885, 1.2, 1.6, 2.2]) {
    const mk = (ns: Params["networkState"]) => {
      const sim = new Sim(bundle, { ...FITTED, luckyBayBias: lb, networkState: ns }, SEED);
      return sim.run(365).seasonReceivedT;
    };
    const o = mk({ forceOpen: BUNKERS });
    const c = mk({ forceClosed: BUNKERS });
    const dpp = ((c - o) / epProd) * 100;
    const mark = lb === FITTED.luckyBayBias ? "  <- fitted" : "";
    const err = (v: number) => `${(((v - obs) / obs) * 100).toFixed(1)} %`;
    console.log(
      `  ${lb.toFixed(3).padStart(10)}   ${mt(o).padStart(11)}   ${mt(c).padStart(13)}   ${(dpp >= 0 ? "+" : "") + dpp.toFixed(2)}   ${err(o).padStart(7)} / ${err(c).padStart(7)}${mark}`,
    );
  }
  console.log("\n  2025/26's calibrated state is CLOSED, so only that column is anchored to data");
  console.log("  at all — and only at the fitted knob. The OPEN column is the counterfactual.");
}

hr("done");
