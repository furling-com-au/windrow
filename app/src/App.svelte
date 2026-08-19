<script lang="ts">
  import { onMount } from "svelte";
  import type { Snapshot } from "@windrow/sim";
  import { DeckMap, type StaticData } from "./lib/deckmap";
  import { SCENARIOS, SEASONS, app, type ScenarioId } from "./state.svelte";
  import MoneyChart from "./components/MoneyChart.svelte";
  import PortPanel from "./components/PortPanel.svelte";
  import AboutModal from "./components/AboutModal.svelte";
  import SimWorker from "./worker/sim.worker?worker";

  let mapEl: HTMLDivElement;
  let map: DeckMap | null = null;
  let worker: Worker | null = null;

  // sim weekly series accumulated in main thread for the chart
  let dailyReceived: number[] = $state([]);
  let lastDay = -1;

  const SPEEDS = [
    { label: "1 h/s", v: 3600 },
    { label: "6 h/s", v: 21600 },
    { label: "1 d/s", v: 86400 },
    { label: "3 d/s", v: 259200 },
  ];

  function post(msg: unknown) {
    worker?.postMessage(msg);
  }

  function initSim() {
    app.loading = true;
    app.done = false;
    dailyReceived = [];
    lastDay = -1;
    const patch = SCENARIOS.find((s) => s.id === app.scenario)?.patch ?? {};
    const dataBase = new URL(import.meta.env.BASE_URL + "data/", location.href).toString();
    post({ type: "init", season: app.season, paramsPatch: patch, seed: 42, dataBase });
  }

  function onSnapshot(snap: Snapshot) {
    app.snap = snap;
    if (snap.day !== lastDay) {
      for (let d = lastDay + 1; d <= snap.day; d++) dailyReceived[d] = snap.kpi.receivedT;
      dailyReceived = dailyReceived;
      lastDay = snap.day;
    }
    map?.update(snap);
  }

  function togglePlay() {
    app.playing = !app.playing;
    post({ type: app.playing ? "play" : "pause" });
  }

  function setSpeed(v: number) {
    app.speed = v;
    post({ type: "speed", value: v });
  }

  function seek(day: number) {
    app.playing = false;
    dailyReceived = dailyReceived.slice(0, Math.max(0, day));
    lastDay = -1;
    post({ type: "seek", day });
  }

  function setSeason(s: string) {
    app.season = s;
    initSim();
  }

  function setScenario(id: ScenarioId) {
    app.scenario = id;
    initSim();
  }

  onMount(() => {
    (async () => {
      const j = (u: string) => fetch("./data/" + u).then((r) => r.json());
      const [basemap, roads, paths, parcels, matrix] = await Promise.all([
        j("basemap.json"),
        j("roads_render.json"),
        j("paths.json"),
        j("parcels.json"),
        j("matrix.json"),
      ]);
      const data: StaticData = { basemap, roads, paths, parcels: parcels.parcels, sites: matrix.sites };
      map = new DeckMap(mapEl, data);
      map.update(null);

      worker = new SimWorker();
      worker.onmessage = (ev: MessageEvent) => {
        const m = ev.data;
        switch (m.type) {
          case "ready":
            app.loading = false;
            app.error = null;
            app.observed = m.observed;
            app.sites = m.sites;
            app.clusters = m.clusters;
            break;
          case "snapshot":
            onSnapshot(m.snap);
            break;
          case "done":
            app.playing = false;
            app.done = true;
            break;
          case "error":
            app.error = m.msg;
            app.playing = false;
            break;
        }
      };
      initSim();
      setSpeed(app.speed);
    })();
    return () => {
      worker?.terminate();
      map?.destroy();
    };
  });

  const fmtMt = (t: number) => (t / 1e6).toFixed(2) + " Mt";
  let obsCumAtDay = $derived.by(() => {
    if (!app.observed || !app.snap) return null;
    const start = Date.UTC(parseInt(app.season.slice(0, 4)), 9, 1);
    let last: number | null = null;
    for (const w of app.observed.weekly_receivals) {
      const d = Math.round((Date.parse(w.week_ending + "T00:00:00Z") - start) / 86400000);
      if (d <= app.snap.day && w.western?.cum_t != null) last = w.western.cum_t;
    }
    return last;
  });
</script>

<div class="map" bind:this={mapEl}></div>

<div class="panel">
  <header>
    <h1>Windrow</h1>
    <span class="sub">Eyre Peninsula grain supply chain — agent simulation</span>
  </header>

  <div class="row">
    <label
      >Season
      <select value={app.season} onchange={(e) => setSeason(e.currentTarget.value)}>
        {#each SEASONS as s}<option value={s}>{s}</option>{/each}
      </select>
    </label>
    <label
      >Scenario
      <select value={app.scenario} onchange={(e) => setScenario(e.currentTarget.value as ScenarioId)}>
        {#each SCENARIOS as sc}<option value={sc.id} title={sc.desc}>{sc.label}</option>{/each}
      </select>
    </label>
  </div>

  <div class="row controls">
    <button class="play" onclick={togglePlay} disabled={app.loading}>
      {app.playing ? "⏸ Pause" : app.done ? "▶ Done" : "▶ Play"}
    </button>
    {#each SPEEDS as sp}
      <button class:active={app.speed === sp.v} onclick={() => setSpeed(sp.v)}>{sp.label}</button>
    {/each}
  </div>

  <div class="row date-row">
    <span class="date">{app.snap?.dateIso ?? "…"}</span>
    <input
      type="range"
      min="0"
      max="364"
      value={app.snap?.day ?? 0}
      oninput={(e) => seek(parseInt(e.currentTarget.value))}
    />
  </div>

  {#if app.snap}
    <div class="kpis">
      <div class="kpi">
        <span class="v">{fmtMt(app.snap.kpi.receivedT)}</span>
        <span class="l">received (sim)</span>
        {#if obsCumAtDay != null}<span class="o">obs {fmtMt(obsCumAtDay)}</span>{/if}
      </div>
      <div class="kpi">
        <span class="v">{fmtMt(app.snap.kpi.shippedT)}</span>
        <span class="l">shipped</span>
      </div>
      <div class="kpi">
        <span class="v">{app.snap.kpi.queueTrucks}</span>
        <span class="l">trucks queued</span>
      </div>
      <div class="kpi">
        <span class="v">{app.snap.kpi.vesselsWaiting}</span>
        <span class="l">vessels waiting</span>
      </div>
    </div>
    <MoneyChart {dailyReceived} observed={app.observed} season={app.season} day={app.snap.day} />
  {/if}

  {#if app.error}<div class="err">{app.error}</div>{/if}
  {#if app.loading}<div class="loading">loading bundle…</div>{/if}

  <footer>
    <button class="link" onclick={() => (app.showAbout = true)}>About & data sources</button>
    <span class="disclaimer">Simulation, not operational data.</span>
  </footer>
</div>

<PortPanel snap={app.snap} sites={app.sites} />
{#if app.showAbout}<AboutModal onclose={() => (app.showAbout = false)} />{/if}

<style>
  .map {
    position: absolute;
    inset: 0;
  }
  .panel {
    position: absolute;
    top: 12px;
    left: 12px;
    width: 330px;
    max-height: calc(100vh - 24px);
    overflow-y: auto;
    background: rgba(13, 22, 34, 0.92);
    border: 1px solid #2a3b50;
    border-radius: 10px;
    padding: 12px 14px;
    color: #dfe7ef;
    font-size: 13px;
    backdrop-filter: blur(4px);
  }
  header h1 {
    margin: 0;
    font-size: 20px;
    letter-spacing: 0.5px;
  }
  .sub {
    color: #8fa3b8;
    font-size: 11.5px;
  }
  .row {
    display: flex;
    gap: 8px;
    margin-top: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 3px;
    font-size: 11px;
    color: #9db1c5;
    flex: 1;
  }
  select {
    background: #17263a;
    color: #dfe7ef;
    border: 1px solid #31465e;
    border-radius: 6px;
    padding: 5px 6px;
    font-size: 12.5px;
  }
  button {
    background: #17263a;
    color: #dfe7ef;
    border: 1px solid #31465e;
    border-radius: 6px;
    padding: 5px 10px;
    cursor: pointer;
    font-size: 12px;
  }
  button:hover {
    background: #1d3049;
  }
  button.active {
    background: #2b578a;
    border-color: #3e73b3;
  }
  button.play {
    background: #2b6a45;
    border-color: #3d8a5c;
    font-weight: 600;
  }
  .date-row {
    gap: 10px;
  }
  .date {
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    min-width: 84px;
  }
  input[type="range"] {
    flex: 1;
  }
  .kpis {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 10px;
  }
  .kpi {
    background: #101c2c;
    border: 1px solid #223650;
    border-radius: 8px;
    padding: 7px 9px;
    display: flex;
    flex-direction: column;
  }
  .kpi .v {
    font-size: 16px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
  .kpi .l {
    color: #8fa3b8;
    font-size: 10.5px;
  }
  .kpi .o {
    color: #e8c568;
    font-size: 10.5px;
  }
  .err {
    margin-top: 8px;
    color: #ff8d80;
    font-size: 12px;
    white-space: pre-wrap;
  }
  .loading {
    margin-top: 8px;
    color: #8fa3b8;
  }
  footer {
    margin-top: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .link {
    background: none;
    border: none;
    color: #7db3e8;
    text-decoration: underline;
    padding: 0;
  }
  .disclaimer {
    color: #708396;
    font-size: 10px;
  }
</style>
