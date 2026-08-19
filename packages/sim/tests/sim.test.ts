import { describe, expect, it } from "vitest";
import { Sim } from "../src/engine";
import { defaultParams } from "../src/params";
import type { Bundle } from "../src/types";
import { loadBundle } from "../scripts/load_bundle";
import { tinyBundle } from "./tiny_bundle";

describe("sim core", () => {
  it("conserves mass and delivers the deliverable share in the tiny scenario", () => {
    const p = defaultParams();
    p.fleetTrucks = 2;
    p.linehaulTrucks = 1;
    const sim = new Sim(tinyBundle(), p, 7);
    const res = sim.run(200); // invariant checks run daily and throw on violation
    const deliverable = 10000 * (1 - p.retentionShare);
    // everything harvestable should eventually be delivered into the network
    expect(res.seasonReceivedT).toBeGreaterThan(deliverable * 0.95);
    expect(res.seasonReceivedT).toBeLessThanOrEqual(deliverable + 1);
    // the vessel should have loaded its target from delivered stock
    expect(res.vesselCount).toBe(1);
    expect(res.seasonShippedPlT).toBeGreaterThan(5900);
  });

  it("is deterministic: same seed => identical event log hash", () => {
    const a = new Sim(tinyBundle(), defaultParams(), 123).run(120);
    const b = new Sim(tinyBundle(), defaultParams(), 123).run(120);
    expect(a.eventLogHash).toBe(b.eventLogHash);
    expect(a.seasonReceivedT).toBe(b.seasonReceivedT);
    const c = new Sim(tinyBundle(), defaultParams(), 124).run(120);
    // different seed: allowed to differ (jittered load times) though totals stay close
    expect(Math.abs(c.seasonReceivedT - a.seasonReceivedT)).toBeLessThan(2000);
  });

  it("runs a real season headless in < 5 s without invariant violations", () => {
    let bundle: Bundle;
    try {
      bundle = loadBundle("2025/26");
    } catch {
      console.warn("real bundle not present; skipping");
      return;
    }
    const t0 = performance.now();
    const sim = new Sim(bundle, defaultParams(), 42);
    const res = sim.run(365);
    const secs = (performance.now() - t0) / 1000;
    expect(secs).toBeLessThan(5);
    // sane magnitude: within a factor of 2 of observed Western receivals
    const obs = bundle.observed.weekly_receivals.at(-1)?.western?.cum_t ?? 2_000_000;
    expect(res.seasonReceivedT).toBeGreaterThan(obs * 0.5);
    expect(res.seasonReceivedT).toBeLessThan(obs * 2.0);
  });
});
