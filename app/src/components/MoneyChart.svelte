<script lang="ts">
  import type { ObservedFile } from "@windrow/sim";

  let { dailyReceived, observed, season, day }: {
    dailyReceived: number[];
    observed: ObservedFile | null;
    season: string;
    day: number;
  } = $props();

  const W = 300;
  const H = 120;
  const PAD = { l: 34, r: 6, t: 8, b: 16 };
  const X_DAYS = 140; // Oct 1 -> mid Feb

  let obsPts = $derived.by(() => {
    if (!observed) return [] as { d: number; cum: number }[];
    const start = Date.UTC(parseInt(season.slice(0, 4)), 9, 1);
    return observed.weekly_receivals
      .filter((w) => w.western?.cum_t != null)
      .map((w) => ({
        d: Math.round((Date.parse(w.week_ending + "T00:00:00Z") - start) / 86400000),
        cum: w.western!.cum_t!,
      }))
      .filter((p) => p.d >= 0 && p.d <= X_DAYS);
  });

  let maxY = $derived(Math.max(500000, ...obsPts.map((p) => p.cum), ...(dailyReceived.length ? [dailyReceived[dailyReceived.length - 1] ?? 0] : [])) * 1.08);

  const x = (d: number) => PAD.l + (d / X_DAYS) * (W - PAD.l - PAD.r);
  let y = $derived((v: number) => H - PAD.b - (v / maxY) * (H - PAD.t - PAD.b));

  let simPath = $derived.by(() => {
    if (!dailyReceived.length) return "";
    let p = "";
    for (let d = 0; d < Math.min(dailyReceived.length, X_DAYS + 1); d++) {
      const v = dailyReceived[d];
      if (v == null) continue;
      p += (p ? "L" : "M") + x(d).toFixed(1) + "," + y(v).toFixed(1);
    }
    return p;
  });

  let obsPath = $derived.by(() => {
    let p = "";
    for (const pt of obsPts) p += (p ? "L" : "M") + x(pt.d).toFixed(1) + "," + y(pt.cum).toFixed(1);
    return p;
  });

  const months = [
    { d: 0, l: "Oct" },
    { d: 31, l: "Nov" },
    { d: 61, l: "Dec" },
    { d: 92, l: "Jan" },
    { d: 123, l: "Feb" },
  ];
</script>

<div class="chart">
  <div class="title">
    Western region receivals — <span class="sim">sim</span> vs <span class="obs">observed</span> (cumulative)
  </div>
  <svg viewBox="0 0 {W} {H}">
    {#each [0.25, 0.5, 0.75, 1] as g}
      <line x1={PAD.l} x2={W - PAD.r} y1={y(maxY * g)} y2={y(maxY * g)} class="grid" />
      <text x={PAD.l - 3} y={y(maxY * g) + 3} class="ylab">{(maxY * g / 1e6).toFixed(1)}</text>
    {/each}
    {#each months as m}
      <text x={x(m.d)} y={H - 3} class="xlab">{m.l}</text>
    {/each}
    {#if obsPath}<path d={obsPath} class="obs-line" />{/if}
    {#each obsPts as pt}<circle cx={x(pt.d)} cy={y(pt.cum)} r="2" class="obs-dot" />{/each}
    {#if simPath}<path d={simPath} class="sim-line" />{/if}
    {#if day <= X_DAYS}<line x1={x(day)} x2={x(day)} y1={PAD.t} y2={H - PAD.b} class="now" />{/if}
  </svg>
</div>

<style>
  .chart {
    margin-top: 10px;
    background: #101c2c;
    border: 1px solid #223650;
    border-radius: 8px;
    padding: 8px;
  }
  .title {
    font-size: 11px;
    color: #9db1c5;
    margin-bottom: 4px;
  }
  .title .sim {
    color: #6fd3a0;
    font-weight: 600;
  }
  .title .obs {
    color: #e8c568;
    font-weight: 600;
  }
  svg {
    width: 100%;
    display: block;
  }
  .grid {
    stroke: #223650;
    stroke-width: 0.5;
  }
  .ylab {
    fill: #708396;
    font-size: 7px;
    text-anchor: end;
  }
  .xlab {
    fill: #708396;
    font-size: 7.5px;
    text-anchor: middle;
  }
  .sim-line {
    stroke: #6fd3a0;
    stroke-width: 1.8;
    fill: none;
  }
  .obs-line {
    stroke: #e8c568;
    stroke-width: 1.4;
    fill: none;
    stroke-dasharray: 3 2;
  }
  .obs-dot {
    fill: #e8c568;
  }
  .now {
    stroke: #7db3e8;
    stroke-width: 1;
    stroke-dasharray: 2 2;
  }
</style>
