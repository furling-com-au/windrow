/// <reference lib="webworker" />
/**
 * Sim runs entirely in this worker; the main thread renders snapshots.
 * Protocol (main -> worker): init | play | pause | speed | seek
 *          (worker -> main): ready | snapshot | done | error
 */
import { DAY_TICKS, Sim, TICK_MIN, defaultParams } from "@windrow/sim";
import type { Bundle, Params, PathsFile, Snapshot } from "@windrow/sim";

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
let seekSeq = 0; // bumped on every seek request; an in-flight seek bails out if it's superseded

const FRAME_MS = 33;

async function fetchJson(url: string) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url}: ${r.status}`);
  return r.json();
}

/** paths.json is season-independent and the biggest file the worker touches, so it is
 *  fetched and parsed once rather than on every season change. The sim needs it for the
 *  road-closure scenario (#28); the main thread fetches the same URL for rendering. */
let pathsPromise: Promise<PathsFile | null> | null = null;
function loadPaths(): Promise<PathsFile | null> {
  pathsPromise ??= fetchJson(dataBase + "paths.json").catch(() => null);
  return pathsPromise;
}

async function loadBundle(season: string): Promise<Bundle> {
  const sid = season.replace("/", "-");
  const base = dataBase;
  const [parcels, demand, matrix, paths, weather, observed] = await Promise.all([
    fetchJson(base + "parcels.json"),
    fetchJson(base + `demand_${sid}.json`),
    fetchJson(base + "matrix.json"),
    loadPaths(),
    fetchJson(base + `weather_${sid}.json`),
    fetchJson(base + `observed_${sid}.json`),
  ]);
  let vessels = null;
  try {
    vessels = await fetchJson(base + `vessels_${sid}.json`);
  } catch {
    vessels = null;
  }
  return { season, parcels: parcels.parcels, demand, matrix, paths, vessels, weather, observed };
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

const yield0 = () => new Promise<void>((r) => setTimeout(r, 0));

/**
 * Runs in small day-sized chunks with a yield every 20 days rather than one long
 * synchronous loop — a synchronous 365-day loop blocks this worker for its full
 * duration (~1.4s desktop, longer on mobile), during which the "play" message that
 * already told the UI it's playing can't be serviced, so the map freezes even though
 * the Pause button is showing (#17). Yielding lets frame() keep the sim advancing
 * (and later "play"/"pause"/"seek" messages get handled) while this computes.
 */
async function computeBaseline(season: string) {
  if (!bundle) return;
  if (baselineCache.has(season)) {
    post({ type: "baseline", season, data: baselineCache.get(season) });
    return;
  }
  const myBundle = bundle;
  const b = new Sim(myBundle, defaultParams(), 42);
  const receivedByDay: number[] = [];
  const shippedByDay: number[] = [];
  const tonneKmByDay: number[] = [];
  const truckKmByDay: number[] = [];
  const lbByDay: number[] = [];
  const waitByDay: number[] = [];
  const queueByDay: number[] = [];
  const arrivedByDay: number[] = [];
  const onFarmTdByDay: number[] = [];
  for (let d = 0; d < 365; d++) {
    b.step(DAY_TICKS);
    const s = b.snapshot();
    receivedByDay.push(s.kpi.receivedT);
    shippedByDay.push(s.kpi.shippedT);
    tonneKmByDay.push(s.kpi.tonneKm);
    truckKmByDay.push(s.kpi.truckKm);
    lbByDay.push(s.kpi.receivedLbT);
    waitByDay.push(s.kpi.meanWaitH);
    queueByDay.push(s.kpi.peakQueue);
    arrivedByDay.push(s.kpi.vesselsArrived);
    onFarmTdByDay.push(s.kpi.onFarmTd);
    if (d % 20 === 19) await yield0();
    if (bundle !== myBundle) return; // season changed mid-compute; this baseline is stale
  }
  const data = { receivedByDay, shippedByDay, tonneKmByDay, truckKmByDay, lbByDay, waitByDay, queueByDay, arrivedByDay, onFarmTdByDay };
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
        // Deterministic scrub: re-init and step day by day to the target, capturing each
        // day's KPIs along the way. A single big sim.step() to the target only ever gives
        // us the FINAL day's numbers — resetHistories() on the main thread then had nothing
        // to backfill days 0..target-1 with, leaving every earlier index a hole (#15), which
        // in turn made the "recent deliveries" narrator check see the full-season cumulative
        // instead of ~0 (permanently reporting "peak harvest") and collapsed the money
        // chart's line to a single point (#18). Posting the whole day-by-day series here lets
        // the main thread backfill for real instead of guessing.
        if (!bundle) {
          // a seek can race a still-in-flight "init" (e.g. dismissing the intro the
          // instant it appears); the main thread waits on a reply to clear its
          // "seeking" flag, so it must get one even when there's nothing to seek yet
          post({ type: "seekResult", notReady: true });
          break;
        }
        playing = false;
        const mySeq = ++seekSeq;
        const myBundle = bundle;
        const params: Params = { ...defaultParams(), ...curPatch };
        // operate on locally-captured refs, not the shared `sim`/`bundle` — a concurrent
        // "init" (season/scenario change) landing while this loop is paused at a yield
        // would otherwise reassign them out from under this in-flight seek
        const mySim = new Sim(myBundle, params, curSeed);
        sim = mySim;
        const target = Math.max(0, Math.min(364, m.day));
        const plIdx = myBundle.matrix.sites.findIndex((s) => s.name.includes("Lincoln"));
        const receivedByDay: number[] = [];
        const shippedByDay: number[] = [];
        const plBerthedByDay: number[] = [];
        const siteReceivedByDay: number[][] = myBundle.matrix.sites.map(() => []);
        // day-index d must line up with what App.svelte's own dailyReceived[snap.day] means:
        // the state AT day d, not after it. So day 0 is captured pre-step (matching the very
        // first sendSnapshot() in init(), before any ticks run) and only d>=1 steps first —
        // stepping unconditionally at d=0 would land seek(0) one day past where the rest of
        // the app expects day 0 to be (verified in-browser: dismissing the intro landed on
        // 3 Oct instead of 1 Oct before this was corrected).
        const capture = (d: number) => {
          const s = mySim.snapshot();
          receivedByDay[d] = s.kpi.receivedT;
          shippedByDay[d] = s.kpi.shippedT;
          plBerthedByDay[d] = plIdx >= 0 ? s.vessels.filter((v) => v.port === plIdx && v.state === 2).length : 0;
          for (let i = 0; i < s.sites.length; i++) siteReceivedByDay[i]![d] = s.sites[i]!.cumReceivedT;
        };
        try {
          capture(0);
          for (let d = 1; d <= target; d++) {
            mySim.step(DAY_TICKS);
            capture(d);
            if (d % 40 === 0) await yield0();
            // a newer seek, or a season/scenario change, superseded this one — abandon it silently
            if (mySeq !== seekSeq || bundle !== myBundle) return;
          }
        } catch (e) {
          post({ type: "error", msg: String(e) });
          break;
        }
        const finalSnap = mySim.snapshot();
        post(
          { type: "seekResult", snap: finalSnap, series: { receivedByDay, shippedByDay, plBerthedByDay, siteReceivedByDay } },
          [finalSnap.parcelHarvestFrac.buffer],
        );
        break;
      }
    }
  } catch (e) {
    post({ type: "error", msg: String(e) });
  }
};
