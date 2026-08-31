<script lang="ts">
  import type { ObservedFile } from "@windrow/sim";
  import InfoTip from "./InfoTip.svelte";

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

  const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dayLabel = (d: number) => {
    const dt = new Date(Date.UTC(parseInt(season.slice(0, 4)), 9, 1) + d * 86400000);
    return `${dt.getUTCDate()} ${MON[dt.getUTCMonth()]}`;
  };

  /** The chart is an SVG of two lines: nothing in it is readable without sight, and the
   *  marker labels were reachable only by hovering an SVG <title> (#31). This is the same
   *  information as one sentence, used as the image's accessible description. */
  let chartSummary = $derived.by(() => {
    const sim = dailyReceived.length ? (dailyReceived[Math.min(day, dailyReceived.length - 1)] ?? 0) : 0;
    const lastObs = obsPts.length ? obsPts[obsPts.length - 1]! : null;
    const parts = [
      `Line chart of cumulative grain delivered from October to mid-February, in million tonnes.`,
      `Simulated: ${(sim / 1e6).toFixed(2)} million tonnes by ${dayLabel(day)}.`,
    ];
    if (lastObs) parts.push(`Actual reported: ${(lastObs.cum / 1e6).toFixed(2)} million tonnes by ${dayLabel(lastObs.d)}.`);
    return parts.join(" ");
  });

  let annList = $derived(
    (observed?.annotations ?? [])
      .filter((a) => a.day >= 0 && a.day <= X_DAYS)
      .sort((a, b) => a.day - b.day)
      .map((a) => `${a.label} (${dayLabel(a.day)})`)
      .join(" · "),
  );
</script>

<div class="chart">
  <div class="title">
    Grain delivered — <span class="sim">simulated</span> vs <span class="obs">actual</span>
    <span class="unit">million tonnes</span><InfoTip
      label="what this chart plots"
      text="Cumulative grain delivered into the network's Eyre Peninsula sites, season to date. The solid line is the simulation; the dashed gold line is the operator's published weekly receivals."
    />
  </div>
  <svg viewBox="0 0 {W} {H}" role="img" aria-label={chartSummary}>
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
    {#each observed?.annotations ?? [] as a}
      {#if a.day >= 0 && a.day <= X_DAYS}
        <g class="ann {a.kind}">
          <line x1={x(a.day)} x2={x(a.day)} y1={PAD.t} y2={H - PAD.b} />
          <circle cx={x(a.day)} cy={PAD.t + 3} r="2.6" />
          <title>{a.label}</title>
        </g>
      {/if}
    {/each}
    {#if day <= X_DAYS}<line x1={x(day)} x2={x(day)} y1={PAD.t} y2={H - PAD.b} class="now" />{/if}
  </svg>
  <div class="annkey">
    <span class="k first">●</span> first delivery
    <span class="k record">●</span> record week
    <span class="k rain">●</span> rain event{#if annList}<InfoTip label="what the markers on the chart say" text={annList} />{/if}
  </div>
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
  .title .unit {
    float: right;
    color: #64788c;
    font-size: 9px;
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
  .ann line {
    stroke-width: 0.8;
    opacity: 0.45;
  }
  .ann.first line, .ann.first circle {
    stroke: #7dd3a8;
    fill: #7dd3a8;
  }
  .ann.record line, .ann.record circle {
    stroke: #e8c568;
    fill: #e8c568;
  }
  .ann.rain line, .ann.rain circle {
    stroke: #6aa9e8;
    fill: #6aa9e8;
  }
  .annkey {
    font-size: 9px;
    color: #708396;
    margin-top: 2px;
  }
  .annkey .k.first { color: #7dd3a8; }
  .annkey .k.record { color: #e8c568; }
  .annkey .k.rain { color: #6aa9e8; }

  /* mobile (#30): 12px floor, and 4.5:1 on the two faint greys. The axis labels are
     SVG user units scaled by the viewBox — the chart renders ~1.16x its 300-unit
     width inside the sheet, so 10.5/11 land just over 12 CSS px. */
  @media (max-width: 800px) {
    .title {
      font-size: 12px;
    }
    .title .unit {
      font-size: 12px;
      color: #7d90a4;
    }
    .annkey {
      font-size: 12px;
      color: #7d90a4;
      line-height: 1.5;
    }
    .ylab,
    .xlab {
      font-size: 11px;
      fill: #8fa3b8;
    }
  }
</style>
