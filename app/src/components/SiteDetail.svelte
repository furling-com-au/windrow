<script lang="ts">
  import { COMMODITIES, SEG_TO_COMMODITY } from "@windrow/sim";
  import { app } from "../state.svelte";
  import { fmtTonnes } from "../lib/economics";
  import InfoTip from "./InfoTip.svelte";

  // "WH" / "BA" are the operator's raw segregation codes, not something a reader should
  // have to decode themselves two lines above this component's own spelled-out legend
  // (F35). Title-cased for a chip; falls back to the raw code for anything unmapped
  // (T-Ports segregations use different codes and aren't in this table).
  const commodityLabel = (code: string) => {
    const c = SEG_TO_COMMODITY[code];
    return c ? c[0]!.toUpperCase() + c.slice(1) : code;
  };

  let { siteHistory }: { siteHistory: number[][] } = $props();

  // Okabe-Ito colour-blind-safe palette — keep in sync with deckmap.ts's COMMODITY_COLORS
  // and App.svelte's legend chips (F32)
  const C_COLORS = ["#e69f00", "#cc79a7", "#f0e442", "#d55e00", "#009e73", "#aaaaaa"];

  let site = $derived(app.selectedSite != null ? app.sites[app.selectedSite] : null);
  let view = $derived(app.selectedSite != null && app.snap ? app.snap.sites[app.selectedSite] : null);
  // the capacity the run enforces (upcountryCapScale already applied where estimated),
  // not the raw bundle figure — otherwise the panel contradicts the capacity lever
  let capT = $derived(view?.capacityT ?? site?.capacity_t ?? 120000);
  // A4: the two ports and the three T-Ports sites have published capacities; every
  // Bunge upcountry figure is an estimate allocated by PIRSA district
  let capAssumed = $derived(site?.capacity_estimated ?? site?.capacity_t == null);
  let hist = $derived(app.selectedSite != null ? (siteHistory[app.selectedSite] ?? []) : []);

  let spark = $derived.by(() => {
    if (hist.length < 2) return "";
    const max = Math.max(...hist, 1);
    const W = 220, H = 34;
    return hist
      .map((v, i) => `${((i / Math.max(1, hist.length - 1)) * W).toFixed(1)},${(H - (v / max) * H).toFixed(1)}`)
      .join(" ");
  });
</script>

{#if site && view}
  <div class="detail" role="region" aria-label="Site detail: {site.name}">
    <div class="head">
      <span class="name">{site.name}</span>
      <button class="x" aria-label="Close the {site.name} detail" onclick={() => (app.selectedSite = null)}>×</button>
    </div>
    <div class="sub">{site.operator} · {site.role} · {site.status.replace(/_(\d{4})_(\d{2})(?=_|$)/g, " $1/$2").replaceAll("_", " ")}</div>
    <div class="chips">
      {#each site.commodities as c}<span class="chip">{commodityLabel(c)}</span>{/each}
      {#if !site.commodities.length}<span class="chip dim">no {app.season} segregations</span>{/if}
    </div>

    <div class="row">
      <span
        >{(Math.round(view.stockT / 100) * 100).toLocaleString()} t of {capT.toLocaleString()} t {capAssumed ? "(capacity estimated)" : ""}<InfoTip
          label="the storage figure"
          text={capAssumed
            ? "Grain in storage, against storage capacity. This site's capacity is not published: it is an estimate — the unpublished upcountry storage total split between PIRSA districts by long-run receivals, then evenly within the district (ASSUMPTIONS A4)."
            : "Grain in storage, against this site's published storage capacity."}
        /></span
      >
      <span class="q" class:hot={view.queue > 15}>{view.queue} trucks queued</span>
    </div>
    <!-- the bar segments were mouse-only: their commodity split is now spelled out in the
         legend row underneath, which every reader gets (#31) -->
    <div class="stack" aria-hidden="true">
      {#each view.stockByC as t, i}
        {#if t > 500}
          <div class="seg" style="width:{Math.max(2, (100 * t) / Math.max(1, view.stockT))}%;background:{C_COLORS[i]}"></div>
        {/if}
      {/each}
    </div>
    <div class="cl">
      {#each view.stockByC as t, i}
        {#if t > 500}<span><i style="background:{C_COLORS[i]}"></i>{COMMODITIES[i]} {Math.round(t / 1000)}k t</span>{/if}
      {/each}
    </div>

    <div class="row2">delivered here this season (sim): <b>{fmtTonnes(view.cumReceivedT)}</b></div>
    {#if spark}
      <svg viewBox="0 0 220 34"><polyline points={spark} fill="none" stroke="#6fd3a0" stroke-width="1.6" /></svg>
      <div class="fine">cumulative receivals over the season (simulated)</div>
    {/if}
  </div>
{/if}

<style>
  .detail {
    position: absolute;
    right: 12px;
    top: 12px;
    width: 250px;
    background: rgba(13, 22, 34, 0.94);
    border: 1px solid #3e73b3;
    border-radius: 10px;
    padding: 10px 12px;
    color: #dfe7ef;
    font-size: 12px;
    backdrop-filter: blur(4px);
    z-index: 5;
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .name {
    font-weight: 700;
    font-size: 14px;
  }
  .x {
    background: none;
    border: none;
    color: #9db1c5;
    font-size: 16px;
    cursor: pointer;
  }
  .sub {
    color: #8fa3b8;
    font-size: 10.5px;
    margin: 2px 0 6px;
  }
  .chips {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }
  .chip {
    background: #1d3049;
    border: 1px solid #31465e;
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 10px;
  }
  .chip.dim {
    color: #708396;
  }
  .row {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: #9db1c5;
    position: relative;
  }
  /* the explanation opens from the left-hand column, which is far too narrow for it —
     float it across the whole panel instead */
  .row :global(.tip) {
    position: absolute;
    left: 0;
    right: 0;
    top: 100%;
    z-index: 2;
    border: 1px solid #31465e;
    border-left-width: 2px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.5);
  }
  .x:focus-visible {
    outline: 2px solid #7db3e8;
    outline-offset: 2px;
  }
  .q.hot {
    color: #ff8d80;
    font-weight: 700;
  }
  .stack {
    display: flex;
    height: 10px;
    border-radius: 5px;
    overflow: hidden;
    background: #17263a;
    margin: 4px 0;
  }
  .cl {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    font-size: 9.5px;
    color: #9db1c5;
  }
  .cl i {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 2px;
    margin-right: 3px;
  }
  .row2 {
    margin-top: 8px;
    font-size: 11px;
    color: #9db1c5;
  }
  svg {
    width: 100%;
    margin-top: 4px;
  }
  .fine {
    color: #64788c;
    font-size: 9.5px;
  }
</style>
