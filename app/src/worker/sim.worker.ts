/// <reference lib="webworker" />
/**
 * Sim runs entirely in this worker; the main thread renders snapshots.
 * Protocol (main -> worker): init | play | pause | speed | seek
 *          (worker -> main): ready | snapshot | done | error
 */
import { DAY_TICKS, Sim, TICK_MIN, defaultParams } from "@windrow/sim";
import type { Bundle, Params, Snapshot } from "@windrow/sim";

let sim: Sim | null = null;
let bundle: Bundle | null = null;
let playing = false;
let speed = 1800; // sim-seconds per real second (default 30 min/s)
let timer: ReturnType<typeof setInterval> | null = null;
let tickCarry = 0;
let curSeason = "";
let curPatch: Partial<Params> = {};
let curSeed = 42;
let dataBase = "/data/";

const FRAME_MS = 33;

async function fetchJson(url: string) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url}: ${r.status}`);
  return r.json();
}

async function loadBundle(season: string): Promise<Bundle> {
  const sid = season.replace("/", "-");
  const base = dataBase;
  const [parcels, demand, matrix, weather, observed] = await Promise.all([
    fetchJson(base + "parcels.json"),
    fetchJson(base + `demand_${sid}.json`),
    fetchJson(base + "matrix.json"),
    fetchJson(base + `weather_${sid}.json`),
    fetchJson(base + `observed_${sid}.json`),
  ]);
  let vessels = null;
  try {
    vessels = await fetchJson(base + `vessels_${sid}.json`);
  } catch {
    vessels = null;
  }
  return { season, parcels: parcels.parcels, demand, matrix, vessels, weather, observed };
}

function post(msg: unknown, transfer?: Transferable[]) {
  (self as unknown as Worker).postMessage(msg, { transfer: transfer ?? [] });
}

function sendSnapshot() {
  if (!sim) return;
  const snap: Snapshot = sim.snapshot();
  post({ type: "snapshot", snap }, [snap.parcelHarvestFrac.buffer]);
}

function frame() {
  if (!sim || !playing) return;
  const simSecondsPerFrame = (speed * FRAME_MS) / 1000;
  const ticksFloat = simSecondsPerFrame / (TICK_MIN * 60) + tickCarry;
  const n = Math.floor(ticksFloat);
  tickCarry = ticksFloat - n;
  if (n > 0) {
    try {
      sim.step(Math.min(n, DAY_TICKS * 4));
    } catch (e) {
      playing = false;
      post({ type: "error", msg: String(e) });
      return;
    }
    if (sim.day >= 365) {
      playing = false;
      post({ type: "done" });
    }
  }
  sendSnapshot();
}

/** headless baseline (default params, seed 42) daily series for the takeaways panel */
const baselineCache = new Map<string, unknown>();

function computeBaseline(season: string) {
  if (!bundle) return;
  if (baselineCache.has(season)) {
    post({ type: "baseline", season, data: baselineCache.get(season) });
    return;
  }
  const b = new Sim(bundle, defaultParams(), 42);
  const receivedByDay: number[] = [];
  const shippedByDay: number[] = [];
  const tonneKmByDay: number[] = [];
  const lbByDay: number[] = [];
  const waitByDay: number[] = [];
  const queueByDay: number[] = [];
  const arrivedByDay: number[] = [];
  for (let d = 0; d < 365; d++) {
    b.step(DAY_TICKS);
    const s = b.snapshot();
    receivedByDay.push(s.kpi.receivedT);
    shippedByDay.push(s.kpi.shippedT);
    tonneKmByDay.push(s.kpi.tonneKm);
    lbByDay.push(s.kpi.receivedLbT);
    waitByDay.push(s.kpi.meanWaitH);
    queueByDay.push(s.kpi.peakQueue);
    arrivedByDay.push(s.kpi.vesselsArrived);
  }
  const data = { receivedByDay, shippedByDay, tonneKmByDay, lbByDay, waitByDay, queueByDay, arrivedByDay };
  baselineCache.set(season, data);
  post({ type: "baseline", season, data });
}

async function init(season: string, patch: Partial<Params>, seed: number) {
  curSeason = season;
  curPatch = patch;
  curSeed = seed;
  if (!bundle || bundle.season !== season) {
    post({ type: "loading" });
    bundle = await loadBundle(season);
    baselineCache.delete(season);
  }
  const params: Params = { ...defaultParams(), ...patch };
  sim = new Sim(bundle, params, seed);
  tickCarry = 0;
  post({
    type: "ready",
    season,
    observed: bundle.observed,
    sites: bundle.matrix.sites,
    clusters: bundle.matrix.clusters,
  });
  sendSnapshot();
  setTimeout(() => computeBaseline(season), 30);
}

self.onmessage = async (ev: MessageEvent) => {
  const m = ev.data;
  try {
    switch (m.type) {
      case "init":
        playing = false;
        if (m.dataBase) dataBase = m.dataBase;
        await init(m.season, m.paramsPatch ?? {}, m.seed ?? 42);
        if (!timer) timer = setInterval(frame, FRAME_MS);
        break;
      case "play":
        playing = true;
        break;
      case "pause":
        playing = false;
        sendSnapshot();
        break;
      case "speed":
        speed = m.value;
        break;
      case "heatmap":
        if (sim) post({ type: "heatmap", data: sim.getTripTonnes() });
        break;
      case "seek": {
        // deterministic scrub: re-init and fast-forward to target day
        if (!bundle) break;
        playing = false;
        const params: Params = { ...defaultParams(), ...curPatch };
        sim = new Sim(bundle, params, curSeed);
        const target = Math.max(0, Math.min(364, m.day)) * DAY_TICKS;
        try {
          sim.step(target);
        } catch (e) {
          post({ type: "error", msg: String(e) });
        }
        sendSnapshot();
        break;
      }
    }
  } catch (e) {
    post({ type: "error", msg: String(e) });
  }
};
