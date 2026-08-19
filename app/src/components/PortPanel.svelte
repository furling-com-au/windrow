<script lang="ts">
  import type { BundleSite, Snapshot } from "@windrow/sim";

  let { snap, sites, plBerthedByDay = [] }: { snap: Snapshot | null; sites: BundleSite[]; plBerthedByDay?: number[] } = $props();

  let occSpark = $derived.by(() => {
    if (plBerthedByDay.length < 2) return "";
    const W = 240, H = 18;
    return plBerthedByDay
      .map((v, i) => `${((i / Math.max(1, plBerthedByDay.length - 1)) * W).toFixed(1)},${(H - (Math.min(2, v) / 2) * H).toFixed(1)}`)
      .join(" ");
  });

  let ports = $derived.by(() => {
    if (!snap) return [];
    const out: {
      name: string;
      short: string;
      stockT: number;
      berthed: { name: string; pct: number; loadedT: number; targetT: number }[];
      waiting: number;
    }[] = [];
    for (const s of sites) {
      if (s.role !== "port") continue;
      const sv = snap.sites[s.id];
      const berthed = snap.vessels
        .filter((v) => v.port === s.id && v.state === 2)
        .map((v) => ({
          name: v.name ?? `vessel #${v.id}`,
          pct: v.targetT ? Math.min(100, (100 * v.loadedT) / v.targetT) : 0,
          loadedT: v.loadedT,
          targetT: v.targetT,
        }));
      const waiting = snap.vessels.filter((v) => v.port === s.id && v.state === 1).length;
      out.push({
        name: s.name,
        short: s.name.replace(" (T-Ports port)", ""),
        stockT: sv?.stockT ?? 0,
        berthed,
        waiting,
      });
    }
    // Port Lincoln first
    out.sort((a, b) => (a.name.includes("Lincoln") ? -1 : b.name.includes("Lincoln") ? 1 : 0));
    return out;
  });
</script>

{#if snap && ports.length}
  <div class="portpanel">
    {#each ports as p, i}
      <div class="port" class:major={i === 0}>
        <div class="phead">
          <span class="pname">{p.short}</span>
          <span class="pstock">{(p.stockT / 1000).toFixed(0)} kt stored</span>
          {#if p.waiting > 0}<span class="wait">{p.waiting} at anchor</span>{/if}
        </div>
        {#each p.berthed as v}
          <div class="vessel">
            <span class="vname">{v.name}</span>
            <div class="bar"><div class="fill" style="width:{v.pct}%"></div></div>
            <span class="vt">{(v.loadedT / 1000).toFixed(0)}/{(v.targetT / 1000).toFixed(0)} kt</span>
          </div>
        {:else}
          <div class="idle">berth idle</div>
        {/each}
        {#if i === 0 && occSpark}
          <svg class="occ" viewBox="0 0 240 18"><polyline points={occSpark} fill="none" stroke="#50dca0" stroke-width="1.2" /></svg>
          <div class="occl">berths occupied over the season (0–2)</div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

<style>
  .portpanel {
    position: absolute;
    right: 12px;
    bottom: 12px;
    width: 270px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 12px;
    color: #dfe7ef;
  }
  .port {
    background: rgba(13, 22, 34, 0.92);
    border: 1px solid #2a3b50;
    border-radius: 10px;
    padding: 8px 10px;
    backdrop-filter: blur(4px);
  }
  .port.major {
    border-color: #3e73b3;
  }
  .phead {
    display: flex;
    gap: 8px;
    align-items: baseline;
    margin-bottom: 4px;
  }
  .pname {
    font-weight: 700;
  }
  .pstock {
    color: #8fa3b8;
    font-size: 10.5px;
    margin-left: auto;
  }
  .wait {
    color: #e8c568;
    font-size: 10.5px;
  }
  .vessel {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 3px;
  }
  .vname {
    width: 88px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 11px;
  }
  .bar {
    flex: 1;
    height: 7px;
    background: #17263a;
    border-radius: 4px;
    overflow: hidden;
  }
  .fill {
    height: 100%;
    background: #50dca0;
  }
  .vt {
    font-size: 10px;
    color: #9db1c5;
    font-variant-numeric: tabular-nums;
  }
  .idle {
    color: #708396;
    font-size: 11px;
  }
  .occ {
    width: 100%;
    margin-top: 5px;
    background: #0d1826;
    border-radius: 4px;
  }
  .occl {
    color: #64788c;
    font-size: 9px;
  }
</style>
