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
  import Intro from "./components/Intro.svelte";
  import { narrate } from "./lib/narrator";
  import SimWorker from "./worker/sim.worker?worker";

  let showIntro = $state(false);
  let userTouchedSpeed = false;
  let legendOpen = $state(typeof window !== "undefined" && window.innerWidth > 900);

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

  // local scrub state so dragging the date slider doesn't fight the sim's own snapshots
  // (F16) — it only tracks app.snap.day while the user isn't actively dragging
  let scrubDay = $state(0);
  let dragging = false;
  $effect(() => {
    if (!dragging && app.snap) scrubDay = app.snap.day;
  });

  type SeekSeries = {
    receivedByDay: number[];
    shippedByDay: number[];
    plBerthedByDay: number[];
    siteReceivedByDay: number[][];
  };

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
      // clear a still-running quiet-months auto-speedup so it can't leak into the next
      // run as an unlabelled speed (#18) — but leave a genuine user speed choice alone
      if (!userTouchedSpeed) setSpeed(86400, false);
      const dataBase = new URL(import.meta.env.BASE_URL + "data/", location.href).toString();
      post({ type: "init", season: app.season, paramsPatch: leversToPatch(app.levers, app.assump), seed: 42, dataBase });
    }, debounceMs);
  }

  function onSnapshot(snap: Snapshot) {
    // Normal playback only: day advances by a tick or (rarely, after a lag spike) a
    // few days at once, never backward and never by a scrub-sized jump — seeks are
    // handled entirely by onSeekResult below instead, with a real backfilled series
    // rather than guessed values, so this no longer needs to special-case jumps (#15).
    app.snap = snap;
    if (snap.day !== lastDay) {
      // once harvest is over, quietly fast-forward the shipping months (unless the
      // viewer chose a speed themselves)
      if (!userTouchedSpeed && app.speed === 86400 && snap.day >= 130) {
        const recent = snap.kpi.receivedT - (dailyReceived[Math.max(0, snap.day - 7)] ?? 0);
        if (recent < 8000) setSpeed(259200, false); // 3 d/s (a real, highlightable speed) through the quiet months
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

  /** a scrub landed: the worker replayed day 0..target and sent the real per-day series
   *  back, so this replaces (not patches) the histories rather than leaving holes (#15) */
  function onSeekResult(snap: Snapshot, series: SeekSeries) {
    app.snap = snap;
    dailyReceived = series.receivedByDay;
    dailyShipped = series.shippedByDay;
    plBerthedByDay = series.plBerthedByDay;
    siteHistory = series.siteReceivedByDay;
    lastDay = snap.day;
    map?.update(snap, app.heatmapOn ? app.heatmap : null);
  }

  function togglePlay() {
    app.playing = !app.playing;
    post({ type: app.playing ? "play" : "pause" });
  }

  function setSpeed(v: number, fromUser = true) {
    if (fromUser) userTouchedSpeed = true;
    app.speed = v;
    post({ type: "speed", value: v });
  }

  function seek(day: number, { resume = false }: { resume?: boolean } = {}) {
    app.done = false; // otherwise scrubbing back from a finished run leaves no play control at all (#18)
    app.playing = resume; // manual scrub pauses; replay/intro-dismiss keep playing once the seek lands
    app.seeking = true;
    post({ type: "seek", day });
  }

  function setSeason(s: string) {
    app.season = s;
    app.baseline = null;
    initSim();
  }

  function setMode(m: "simple" | "advanced") {
    app.viewMode = m;
    localStorage.setItem("windrow_mode", m);
    if (m === "simple" && app.heatmapOn) toggleHeatmap();
  }

  function replay() {
    if (!userTouchedSpeed) setSpeed(86400, false);
    seek(0, { resume: true });
  }

  /** the sim keeps running (by design — "the map should live immediately") while the
   *  intro's opaque backdrop hides it, so a slow first-time reader can dismiss it 40-60s
   *  in, past the season's first delivery (#14). Land back at day 0 rather than delay the
   *  clock, so the ambient motion behind the modal stays, but watching starts at the start. */
  function dismissIntro() {
    showIntro = false;
    if (!userTouchedSpeed) setSpeed(86400, false);
    seek(0, { resume: true });
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
            // the map should live immediately — a frozen dashboard reads as broken
            app.playing = true;
            post({ type: "play" });
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
          case "seekResult":
            app.seeking = false;
            if (m.notReady) break; // raced the worker's own init; nothing to apply
            onSeekResult(m.snap, m.series);
            if (app.playing) post({ type: "play" }); // resume (replay / intro dismiss) now that the seek has landed
            break;
          case "done":
            app.playing = false;
            app.done = true;
            break;
          case "error":
            app.error = m.msg;
            app.playing = false;
            app.seeking = false;
            break;
        }
      };
      initSim();
      setSpeed(app.speed, false);
      heatTimer = setInterval(() => {
        if (app.heatmapOn) post({ type: "heatmap" });
      }, 1500);
      if (!localStorage.getItem("windrow_intro")) showIntro = true;
    })();
    return () => {
      if (heatTimer) clearInterval(heatTimer);
      worker?.terminate();
      map?.destroy();
    };
  });

  const fmtMt = (t: number) => (t / 1e6).toFixed(2) + " Mt";
  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  // driven by scrubDay (not app.snap.day) so the date label tracks the thumb live while
  // dragging, instead of only updating once a scrub commits (#16)
  let prettyDate = $derived.by(() => {
    if (!app.snap) return "…";
    const start = Date.UTC(parseInt(app.season.slice(0, 4)), 9, 1);
    const d = new Date(start + scrubDay * 86400000);
    return `${d.getUTCDate()} ${MON[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
  });
  let narratorText = $derived(
    app.snap && !app.loading ? narrate(app.snap, app.observed, app.sites, dailyReceived) : "",
  );
  /** the observed weekly cumulative only updates on its own week-ending date — compare there and nowhere else, so this never mixes a continuous sim total against a stale weekly one */
  let obsCumAtDay = $derived.by(() => {
    if (!app.observed || !app.snap) return null;
    const start = Date.UTC(parseInt(app.season.slice(0, 4)), 9, 1);
    const w = app.observed.weekly_receivals.find(
      (w) => Math.round((Date.parse(w.week_ending + "T00:00:00Z") - start) / 86400000) === app.snap!.day,
    );
    return w?.western?.cum_t != null ? { value: w.western.cum_t, weekEnding: w.week_ending } : null;
  });
  const fmtWeekEnding = (iso: string) => {
    const d = new Date(iso + "T00:00:00Z");
    return `${d.getUTCDate()} ${MON[d.getUTCMonth()]}`;
  };
</script>

<div class="map" bind:this={mapEl}></div>

<div class="panel">
  <header>
    <div>
      <h1>Windrow</h1>
      <span class="sub">Watch an Eyre Peninsula harvest move from paddock to ship</span>
    </div>
    <button class="help" title="Guided tour" onclick={() => { app.tourStep = 0; app.showTour = true; }}>?</button>
  </header>

  <div class="modes">
    <button class:active={app.viewMode === "simple"} onclick={() => setMode("simple")}>Simple</button>
    <button class:active={app.viewMode === "advanced"} onclick={() => setMode("advanced")} title="Levers, dollar takeaways, truck-flow heatmap, CSV export">Advanced</button>
  </div>

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
    {#if app.done}
      <button class="play" onclick={replay}>↺ Replay season</button>
    {:else}
      <button class="play" onclick={togglePlay} disabled={app.loading || app.seeking}>
        {app.playing ? "⏸ Pause" : "▶ Play"}
      </button>
    {/if}
    {#each SPEEDS as sp}
      <button class:active={app.speed === sp.v} onclick={() => setSpeed(sp.v)} title="simulation speed">{sp.label}</button>
    {/each}
  </div>

  <div class="row date-row">
    <span class="date">{prettyDate}</span>
    <div class="scrub">
      <input
        type="range"
        min="0"
        max="364"
        value={scrubDay}
        oninput={(e) => {
          dragging = true;
          scrubDay = parseInt(e.currentTarget.value);
        }}
        onchange={(e) => {
          dragging = false;
          seek(parseInt(e.currentTarget.value));
        }}
      />
      <div class="phases"><span class="ph h">harvest</span><span class="ph s">shipping</span></div>
    </div>
  </div>

  {#if app.snap}
    <div class="kpis">
      <div class="kpi" title="Grain delivered into the main network's silos and ports so far (simulated). 'actual' = the operator's published weekly figure, shown only on the week-ending date it was reported — the observed total doesn't move between Sundays. Deliveries to T-Ports Lucky Bay are counted separately.">
        <span class="v">{(app.snap.kpi.receivedT / 1e6).toFixed(2)}</span>
        <span class="l">million t delivered (sim)</span>
        {#if obsCumAtDay}<span class="o">actual {(obsCumAtDay.value / 1e6).toFixed(2)} (w/e {fmtWeekEnding(obsCumAtDay.weekEnding)})</span>{/if}
      </div>
      {#if app.viewMode === "simple"}
        <div class="kpi" title="Trucks currently loading, driving or queued in the simulation">
          <span class="v">{app.snap.trucks.length}</span>
          <span class="l">trucks on the road now</span>
        </div>
      {:else}
        <div
          class="kpi"
          title="Grain loaded onto ships at all three ports (Port Lincoln, Thevenard, Lucky Bay). Ships also load stock carried over from last season, so this can exceed this season's deliveries."
        >
          <span class="v">{(app.snap.kpi.shippedT / 1e6).toFixed(2)}</span>
          <span class="l">million t shipped out</span>
          {#if app.snap.kpi.carryInT > 10000}<span class="o">incl. {(app.snap.kpi.carryInT / 1e6).toFixed(2)} carry-over</span>{/if}
        </div>
        <div class="kpi" title="Trucks waiting to unload across all sites right now">
          <span class="v">{app.snap.kpi.queueTrucks}</span>
          <span class="l">trucks queued</span>
        </div>
        <div class="kpi" title="Ships at anchor waiting for a berth or for grain">
          <span class="v">{app.snap.kpi.vesselsWaiting}</span>
          <span class="l">ships waiting</span>
        </div>
      {/if}
    </div>
    <MoneyChart {dailyReceived} observed={app.observed} season={app.season} day={scrubDay} />
  {/if}

  <LeversPanel onchange={() => initSim(350)} />

  {#if app.viewMode === "advanced"}
    <div class="row tools">
      <button class:active={app.heatmapOn} onclick={toggleHeatmap} title="Cumulative loaded tonnes per route">🚚 truck-flow heatmap</button>
      <button onclick={downloadCsv} title="Daily sim series + actual weekly deliveries (CSV)">⬇ CSV</button>
    </div>
  {/if}

  {#if app.error}<div class="err">{app.error}</div>{/if}
  {#if app.loading}<div class="loading">loading bundle…</div>{/if}
  {#if app.seeking}<div class="loading">seeking…</div>{/if}

  <footer>
    <button class="link" onclick={() => (app.showAbout = true)}>About & data sources</button>
    <span class="disclaimer">Simulation, not operational data.</span>
  </footer>
</div>

{#if narratorText}
  <div class="narrator" class:shift={app.viewMode === "advanced"}>{narratorText}</div>
{/if}

<PortPanel snap={app.snap} sites={app.sites} {plBerthedByDay} />
<SiteDetail {siteHistory} />
<Tour />
{#if showIntro}<Intro onwatch={dismissIntro} />{/if}

{#if legendOpen}
  <div class="legend">
    <div class="lg-head">
      <b>Map key</b>
      <button class="lg-x" onclick={() => (legendOpen = false)}>×</button>
    </div>
    <div><span class="sw" style="background:linear-gradient(90deg,#3e7040,#c4a85c)"></span> paddocks: green = crop standing, gold = harvested</div>
    <div class="lg-sub">moving dots are trucks, coloured by their load:</div>
    <div class="chips">
      <span><i style="background:#ebc85a"></i>wheat</span>
      <span><i style="background:#d6a864"></i>barley</span>
      <span><i style="background:#fadc28"></i>canola</span>
      <span><i style="background:#c85a50"></i>lentils</span>
      <span><i style="background:#96b45a"></i>beans</span>
      <span><i style="background:#5ac8eb"></i>silo→port shuttle</span>
    </div>
    <div><span class="sw ring"></span> silo/site: turns bright blue as storage fills · red ring = trucks queued · click it for detail</div>
    <div><span class="sw dot" style="background:#f0c850"></span> ship waiting at anchor</div>
    <div><span class="sw dot" style="background:#50dca0"></span> ship loading at berth</div>
  </div>
{:else}
  <button class="legend-btn" onclick={() => (legendOpen = true)}>🗺 map key</button>
{/if}

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
  .modes {
    display: flex;
    gap: 0;
    margin-top: 8px;
    border: 1px solid #31465e;
    border-radius: 6px;
    overflow: hidden;
    width: fit-content;
  }
  .modes button {
    border: none;
    border-radius: 0;
    font-size: 11px;
    padding: 4px 14px;
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
    min-width: 88px;
  }
  .scrub {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  input[type="range"] {
    width: 100%;
    accent-color: #3e73b3;
  }
  .phases {
    display: flex;
    font-size: 8.5px;
    color: #64788c;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .ph.h {
    width: 34%;
    border-top: 2px solid #3d8a5c;
    text-align: center;
  }
  .ph.s {
    width: 66%;
    border-top: 2px solid #31465e;
    text-align: center;
  }
  .narrator {
    position: absolute;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    max-width: min(560px, 55vw);
    background: rgba(13, 22, 34, 0.9);
    border: 1px solid #2a3b50;
    border-radius: 10px;
    padding: 8px 16px;
    color: #e8eef5;
    font-size: 13px;
    line-height: 1.45;
    text-align: center;
    backdrop-filter: blur(4px);
    pointer-events: none;
    z-index: 4;
  }
  @media (max-width: 1100px) {
    .narrator {
      left: auto;
      right: 12px;
      transform: none;
      max-width: 300px;
      text-align: left;
    }
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
    max-width: 300px;
    background: rgba(13, 22, 34, 0.94);
    border: 1px solid #2a3b50;
    border-radius: 8px;
    padding: 8px 10px;
    color: #b9c7d6;
    font-size: 10.5px;
    display: flex;
    flex-direction: column;
    gap: 3px;
    backdrop-filter: blur(4px);
    z-index: 6;
  }
  .legend-btn {
    position: absolute;
    left: 356px;
    bottom: 12px;
    z-index: 6;
    background: rgba(13, 22, 34, 0.9);
    border: 1px solid #2a3b50;
    color: #b9c7d6;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11px;
    cursor: pointer;
  }
  .lg-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #dfe7ef;
  }
  .lg-x {
    background: none;
    border: none;
    color: #9db1c5;
    font-size: 14px;
    cursor: pointer;
    padding: 0 2px;
  }
  .lg-sub {
    color: #8fa3b8;
    margin-top: 2px;
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 10px;
    margin: 1px 0 3px;
  }
  .chips span i {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 4px;
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
    background: linear-gradient(90deg, #163449, #4dd7ff);
    border: 2px solid #ff5046;
    margin-left: 5px;
    margin-right: 11px;
  }
  @media (max-width: 800px) {
    .panel {
      width: calc(100vw - 24px);
      max-height: 55vh;
    }
    .legend,
    .legend-btn {
      left: 12px;
      bottom: 58vh;
    }
  }
</style>
