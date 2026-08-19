<script lang="ts">
  import { onMount } from "svelte";
  import type { Snapshot } from "@windrow/sim";
  import { DeckMap, type StaticData } from "./lib/deckmap";
  import { DEFAULT_LEVERS, SCENARIOS, SEASONS, SEASON_LABELS, app, leversToPatch, type ScenarioId } from "./state.svelte";
  import MoneyChart from "./components/MoneyChart.svelte";
  import PortPanel from "./components/PortPanel.svelte";
  import AboutModal from "./components/AboutModal.svelte";
  import LeversPanel from "./components/LeversPanel.svelte";
  import SiteDetail from "./components/SiteDetail.svelte";
  import Tour from "./components/Tour.svelte";
  import SimWorker from "./worker/sim.worker?worker";

  let mapEl: HTMLDivElement;
  let map: DeckMap | null = null;
  let worker: Worker | null = null;

  // main-thread histories for chart, CSV, drill-downs
  let dailyReceived: number[] = $state([]);
  let dailyShipped: number[] = [];
  let siteHistory: number[][] = $state([]);
  let plBerthedByDay: number[] = $state([]);
  let lastDay = -1;
  let plPortIdx = -1;

  const SPEEDS = [
    { label: "1 h/s", v: 3600 },
    { label: "6 h/s", v: 21600 },
    { label: "1 d/s", v: 86400 },
    { label: "3 d/s", v: 259200 },
  ];

  function post(msg: unknown) {
    worker?.postMessage(msg);
  }

  function resetHistories() {
    dailyReceived = [];
    dailyShipped = [];
    siteHistory = app.sites.map(() => []);
    plBerthedByDay = [];
    lastDay = -1;
  }

  let initTimer: ReturnType<typeof setTimeout> | null = null;
  function initSim(debounceMs = 0) {
    if (initTimer) clearTimeout(initTimer);
    initTimer = setTimeout(() => {
      app.loading = true;
      app.done = false;
      app.playing = false; // worker pauses itself on init; keep the UI in sync
      resetHistories();
      const dataBase = new URL(import.meta.env.BASE_URL + "data/", location.href).toString();
      post({ type: "init", season: app.season, paramsPatch: leversToPatch(app.levers), seed: 42, dataBase });
    }, debounceMs);
  }

  function onSnapshot(snap: Snapshot) {
    app.snap = snap;
    if (snap.day !== lastDay) {
      if (snap.day < lastDay || snap.day > lastDay + 3) {
        // scrub jump: keep series sparse rather than flood-filling with post-jump values
        resetHistories();
        lastDay = snap.day - 1;
      }
      for (let d = Math.max(0, lastDay + 1); d <= snap.day; d++) {
        dailyReceived[d] = snap.kpi.receivedT;
        dailyShipped[d] = snap.kpi.shippedT;
        plBerthedByDay[d] = plPortIdx >= 0 ? snap.vessels.filter((v) => v.port === plPortIdx && v.state === 2).length : 0;
        for (let s = 0; s < snap.sites.length; s++) {
          (siteHistory[s] ??= [])[d] = snap.sites[s]!.cumReceivedT;
        }
      }
      dailyReceived = dailyReceived;
      plBerthedByDay = plBerthedByDay;
      siteHistory = siteHistory;
      lastDay = snap.day;
    }
    map?.update(snap, app.heatmapOn ? app.heatmap : null);
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
    post({ type: "seek", day });
  }

  function setSeason(s: string) {
    app.season = s;
    app.baseline = null;
    initSim();
  }

  function setScenario(id: ScenarioId) {
    app.scenario = id;
    const preset = SCENARIOS.find((s) => s.id === id);
    if (preset) app.levers = { ...DEFAULT_LEVERS, ...preset.levers };
    initSim();
  }

  function toggleHeatmap() {
    app.heatmapOn = !app.heatmapOn;
    if (app.heatmapOn) post({ type: "heatmap" });
    else map?.update(app.snap, null);
  }

  function downloadCsv() {
    const start = Date.UTC(parseInt(app.season.slice(0, 4)), 9, 1);
    const obsByDate = new Map<string, { w: number | null; c: number | null }>();
    for (const w of app.observed?.weekly_receivals ?? []) {
      obsByDate.set(w.week_ending, { w: w.western?.weekly_t ?? null, c: w.western?.cum_t ?? null });
    }
    let csv = `# Windrow simulated season ${app.season} · scenario ${app.scenario} · seed 42\n`;
    csv += "# Simulation, not operational data. Sources & assumptions: github.com/furling-com-au/windrow\n";
    csv += "date,sim_cum_received_t,sim_cum_shipped_t,obs_western_weekly_t,obs_western_cum_t\n";
    for (let d = 0; d < dailyReceived.length; d++) {
      const date = new Date(start + d * 86400000).toISOString().slice(0, 10);
      const o = obsByDate.get(date);
      csv += `${date},${dailyReceived[d] ?? ""},${dailyShipped[d] ?? ""},${o?.w ?? ""},${o?.c ?? ""}\n`;
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    a.download = `windrow_${app.season.replace("/", "-")}_${app.scenario}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  onMount(() => {
    let heatTimer: ReturnType<typeof setInterval> | null = null;
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
      map = new DeckMap(mapEl, data, (siteId) => (app.selectedSite = siteId));
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
            plPortIdx = app.sites.findIndex((s) => s.name.includes("Lincoln"));
            resetHistories();
            break;
          case "baseline":
            if (m.season === app.season) app.baseline = m.data;
            break;
          case "heatmap":
            app.heatmap = m.data;
            if (app.heatmapOn) map?.update(app.snap, m.data);
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
      heatTimer = setInterval(() => {
        if (app.heatmapOn) post({ type: "heatmap" });
      }, 1500);
      if (!localStorage.getItem("windrow_tour")) {
        app.tourStep = 0;
        app.showTour = true;
      }
    })();
    return () => {
      if (heatTimer) clearInterval(heatTimer);
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
    <div>
      <h1>Windrow</h1>
      <span class="sub">Eyre Peninsula grain supply chain — agent simulation</span>
    </div>
    <button class="help" title="Guided tour" onclick={() => { app.tourStep = 0; app.showTour = true; }}>?</button>
  </header>

  <div class="row">
    <label
      >Season
      <select value={app.season} onchange={(e) => setSeason(e.currentTarget.value)}>
        {#each SEASONS as s}<option value={s}>{SEASON_LABELS[s] ?? s}</option>{/each}
      </select>
    </label>
    <label
      >Scenario
      <select value={app.scenario} onchange={(e) => setScenario(e.currentTarget.value as ScenarioId)}>
        {#each SCENARIOS as sc}<option value={sc.id}>{sc.label}</option>{/each}
        {#if app.scenario === "custom"}<option value="custom">Custom (levers)</option>{/if}
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

  <LeversPanel onchange={() => initSim(350)} />

  <div class="row tools">
    <button class:active={app.heatmapOn} onclick={toggleHeatmap} title="Cumulative loaded tonnes per route">🚚 truck-flow heatmap</button>
    <button onclick={downloadCsv} title="Daily sim series + observed weekly (CSV)">⬇ CSV</button>
  </div>

  {#if app.error}<div class="err">{app.error}</div>{/if}
  {#if app.loading}<div class="loading">loading bundle…</div>{/if}

  <footer>
    <button class="link" onclick={() => (app.showAbout = true)}>About & data sources</button>
    <span class="disclaimer">Simulation, not operational data.</span>
  </footer>
</div>

<PortPanel snap={app.snap} sites={app.sites} {plBerthedByDay} />
<SiteDetail {siteHistory} />
<Tour />

<div class="legend">
  <div><span class="sw" style="background:linear-gradient(90deg,#3e7040,#c4a85c)"></span> paddocks: unharvested → harvested</div>
  <div><span class="sw dot" style="background:#ebc85a"></span> farm trucks (colour = commodity)</div>
  <div><span class="sw dot" style="background:#5ac8eb"></span> line-haul to port</div>
  <div><span class="sw ring"></span> site: fill = storage used, red ring = queue · click for detail</div>
  <div><span class="sw dot" style="background:#f0c850"></span> ship waiting at anchor</div>
  <div><span class="sw dot" style="background:#50dca0"></span> ship loading at berth</div>
</div>

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
    width: 332px;
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
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
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
  .help {
    background: #17263a;
    border: 1px solid #31465e;
    color: #9db1c5;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
    font-weight: 700;
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
    font-size: 12px;
    max-width: 158px;
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
  .tools button {
    font-size: 11px;
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
  .legend {
    position: absolute;
    left: 356px;
    bottom: 12px;
    background: rgba(13, 22, 34, 0.88);
    border: 1px solid #2a3b50;
    border-radius: 8px;
    padding: 8px 10px;
    color: #b9c7d6;
    font-size: 10.5px;
    display: flex;
    flex-direction: column;
    gap: 3px;
    backdrop-filter: blur(4px);
  }
  .legend .sw {
    display: inline-block;
    width: 22px;
    height: 8px;
    border-radius: 4px;
    margin-right: 5px;
    vertical-align: middle;
  }
  .legend .sw.dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-left: 6px;
    margin-right: 12px;
  }
  .legend .sw.ring {
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: #4c7a62;
    border: 2px solid #ff5046;
    margin-left: 5px;
    margin-right: 11px;
  }
  @media (max-width: 800px) {
    .panel {
      width: calc(100vw - 24px);
      max-height: 55vh;
    }
    .legend {
      display: none;
    }
  }
</style>
