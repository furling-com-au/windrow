<script lang="ts">
  import { DEMURRAGE_PER_DAY, FARMGATE_PER_T, FREIGHT_PER_T_KM, fmtMoney } from "../lib/economics";
  import { DEFAULT_LEVERS, SCENARIOS, app } from "../state.svelte";

  let { onchange }: { onchange: () => void } = $props();

  function set<K extends keyof typeof app.levers>(k: K, v: (typeof app.levers)[K]) {
    app.levers = { ...app.levers, [k]: v };
    app.scenario = "custom";
    onchange();
  }

  function reset() {
    app.levers = { ...DEFAULT_LEVERS };
    app.scenario = "baseline";
    onchange();
  }

  let story = $derived(
    SCENARIOS.find((s) => s.id === app.scenario)?.story ??
      "Custom what-if — you moved the levers. The takeaways below compare your version of the season against the normal one.",
  );

  interface Takeaway {
    text: string;
    money?: string;
    dir: "up" | "down" | "flat";
  }

  /** raw deltas vs the baseline run at the same simulated day */
  let deltas = $derived.by(() => {
    const s = app.snap;
    const b = app.baseline;
    if (!s || !b || b.receivedByDay.length === 0) return null;
    const i = Math.max(0, Math.min(s.day - 1, b.receivedByDay.length - 1));
    const baseRec = b.receivedByDay[i] ?? 0;
    const dRec = s.kpi.receivedT - baseRec;
    const dLb = s.kpi.receivedLbT - (b.lbByDay[i] ?? 0);
    const dShip = s.kpi.shippedT - (b.shippedByDay[i] ?? 0);
    const dTkm = s.kpi.tonneKm - (b.tonneKmByDay[i] ?? 0);
    const freight = dTkm * FREIGHT_PER_T_KM;
    const baseQ = b.queueByDay[i] ?? 0;
    const dQrel = baseQ > 20 ? (s.kpi.peakQueue - baseQ) / baseQ : 0;
    const waitDays = (s.kpi.meanWaitH * s.kpi.vesselsArrived) / 24;
    const baseWaitDays = ((b.waitByDay[i] ?? 0) * (b.arrivedByDay[i] ?? 0)) / 24;
    const demurrage = (waitDays - baseWaitDays) * DEMURRAGE_PER_DAY;
    let farmgate = 0;
    if (app.levers.productionScale !== 1.0 && app.observed) {
      const prod = Object.values(app.observed.district_production_t ?? {}).reduce((a, v) => a + v, 0);
      farmgate = (app.levers.productionScale - 1) * prod * (FARMGATE_PER_T[app.season] ?? 380);
    }
    return { i, baseRec, dRec, relRec: baseRec > 50000 ? dRec / baseRec : 0, dLb, dShip, dTkm, freight, baseQ, dQrel, demurrage, farmgate, waitNow: s.kpi.meanWaitH, waitBase: b.waitByDay[i] ?? 0 };
  });

  const tonnes = (t: number) => {
    const a = Math.abs(t);
    if (a >= 950000) return `${(a / 1e6).toFixed(1)} million tonnes`;
    return `${(Math.round(a / 1000) * 1000).toLocaleString()} tonnes`;
  };
  const pct = (f: number) => `${Math.abs(f * 100).toFixed(Math.abs(f) < 0.02 ? 1 : 0)}%`;

  /** plain-English sentences for Simple mode, most important first */
  let sentences = $derived.by((): { verdict: string; lines: string[] } | null => {
    const d = deltas;
    if (!d || app.scenario === "baseline") return null;
    const lines: string[] = [];

    if (d.farmgate !== 0) {
      lines.push(
        `A crop ${pct(app.levers.productionScale - 1)} ${app.levers.productionScale > 1 ? "bigger" : "smaller"} is worth about ${fmtMoney(Math.abs(d.farmgate))} ${d.farmgate > 0 ? "more" : "less"} to farmers at the gate.`,
      );
    }
    if (Math.abs(d.relRec) >= 0.02 && Math.abs(d.dRec) > 20000) {
      lines.push(`${tonnes(d.dRec)} ${d.dRec > 0 ? "more" : "less"} grain reaches the silos and ports (${d.dRec > 0 ? "+" : "−"}${pct(d.relRec)}).`);
    }
    if (Math.abs(d.dLb) > 10000) {
      lines.push(
        d.dLb > 0
          ? `${tonnes(d.dLb)} of deliveries shift to the rival Lucky Bay port instead.`
          : `${tonnes(d.dLb)} of deliveries shift away from Lucky Bay back to the main network.`,
      );
    }
    if (Math.abs(d.freight) > 300000) {
      lines.push(`Trucks travel ${d.freight > 0 ? "further" : "less"} overall — roughly ${fmtMoney(Math.abs(d.freight))} ${d.freight > 0 ? "extra" : "saved"} in freight.`);
    }
    if (Math.abs(d.dQrel) >= 0.15) {
      lines.push(`Queues at the busiest silo peak about ${pct(d.dQrel)} ${d.dQrel > 0 ? "longer" : "shorter"} than the real season.`);
    }
    if (Math.abs(d.demurrage) > 500000) {
      lines.push(
        `Ships wait about ${Math.round(d.waitNow)} hours each at anchor (normally ~${Math.round(d.waitBase)}) — roughly ${fmtMoney(Math.abs(d.demurrage))} in ${d.demurrage > 0 ? "extra" : "avoided"} waiting costs.`,
      );
    }
    if (Math.abs(d.dShip) > 50000) {
      lines.push(`${tonnes(d.dShip)} ${d.dShip > 0 ? "more" : "less"} grain gets shipped out by season's end.`);
    }

    // verdict: lead with the shape of the outcome, not a number
    let verdict: string;
    if (d.farmgate !== 0) {
      verdict =
        app.levers.productionScale > 1
          ? "A bigger crop gets through — but watch the queues and where the surplus goes."
          : "A smaller crop: the pain is in what farmers don't harvest, not in moving it.";
    } else if (Math.abs(d.relRec) < 0.02) {
      const costs: string[] = [];
      if (d.dQrel >= 0.15) costs.push("longer queues");
      if (d.freight > 300000) costs.push("extra trucking");
      if (d.demurrage > 500000) costs.push("ships waiting");
      verdict = costs.length
        ? `The system absorbs this: almost the same grain gets through — the price is ${costs.join(" and ")}.`
        : "Barely any difference from the real season.";
    } else if (d.relRec <= -0.02) {
      verdict = `The main network handles ${pct(d.relRec)} less grain${d.dLb > 10000 ? " — much of it goes to Lucky Bay instead" : ""}.`;
    } else {
      verdict = `The network handles ${pct(d.relRec)} more grain than the real season.`;
    }
    return { verdict, lines: lines.slice(0, 4) };
  });

  /** compact metric rows for Advanced mode */
  let takeaways = $derived.by((): Takeaway[] => {
    const d = deltas;
    if (!d) return [];
    const out: Takeaway[] = [];
    const kt = (t: number) => `${t > 0 ? "+" : "−"}${Math.abs(t / 1000).toFixed(0)} kt`;
    if (Math.abs(d.dRec) > 20000) out.push({ text: `Grain delivered ${kt(d.dRec)} vs baseline`, dir: d.dRec > 0 ? "up" : "down" });
    if (Math.abs(d.dLb) > 10000) out.push({ text: `Lucky Bay (T-Ports) intake ${kt(d.dLb)}`, dir: d.dLb > 0 ? "up" : "down" });
    if (Math.abs(d.dShip) > 20000) out.push({ text: `Shipped out ${kt(d.dShip)}`, dir: d.dShip > 0 ? "up" : "down" });
    if (Math.abs(d.freight) > 150000)
      out.push({
        text: `Trucking task ${d.dTkm > 0 ? "+" : "−"}${Math.abs(d.dTkm / 1e6).toFixed(1)}M tonne-km`,
        money: `${d.freight > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.freight))} freight`,
        dir: d.freight > 0 ? "up" : "down",
      });
    if (app.snap && Math.abs(app.snap.kpi.peakQueue - d.baseQ) > 15)
      out.push({ text: `Peak site queue ${app.snap.kpi.peakQueue} vs ${d.baseQ} trucks`, dir: app.snap.kpi.peakQueue > d.baseQ ? "up" : "down" });
    if (Math.abs(d.demurrage) > 200000)
      out.push({
        text: `Vessel wait ${Math.round(d.waitNow)} h vs ${Math.round(d.waitBase)} h`,
        money: `${d.demurrage > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.demurrage))} demurrage-equiv.`,
        dir: d.demurrage > 0 ? "up" : "down",
      });
    if (d.farmgate !== 0)
      out.push({
        text: `Crop ${app.levers.productionScale > 1 ? "+" : "−"}${pct(app.levers.productionScale - 1)}`,
        money: `${d.farmgate > 0 ? "+" : "−"}${fmtMoney(Math.abs(d.farmgate))} farm-gate`,
        dir: d.farmgate > 0 ? "up" : "down",
      });
    return out;
  });
</script>

<div class="levers">
  <div class="head">
    <span class="t">{app.viewMode === "advanced" ? "What-if levers" : "What-if"}</span>
    {#if app.scenario !== "baseline"}<button class="reset" onclick={reset}>back to normal</button>{/if}
  </div>
  <p class="story">{story}</p>

  {#if app.viewMode === "advanced"}
    <label>
      <span>Crop size <b>{Math.round(app.levers.productionScale * 100)}%</b> of actual</span>
      <input type="range" min="0.5" max="1.4" step="0.05" value={app.levers.productionScale}
        oninput={(e) => set("productionScale", parseFloat(e.currentTarget.value))} />
    </label>
    <label>
      <span>Truck fleet <b>{Math.round(app.levers.fleetTrucks)}</b> trucks</span>
      <input type="range" min="300" max="800" step="10" value={app.levers.fleetTrucks}
        oninput={(e) => set("fleetTrucks", parseFloat(e.currentTarget.value))} />
    </label>
    <label>
      <span>Grain drawn to Lucky Bay <b>{app.levers.luckyBayBias.toFixed(1)}×</b></span>
      <input type="range" min="0.2" max="3" step="0.1" value={app.levers.luckyBayBias}
        oninput={(e) => set("luckyBayBias", parseFloat(e.currentTarget.value))} />
    </label>
    <label>
      <span>Farmers carting straight to port <b>{app.levers.portAttractBias.toFixed(1)}×</b></span>
      <input type="range" min="0.4" max="2.5" step="0.1" value={app.levers.portAttractBias}
        oninput={(e) => set("portAttractBias", parseFloat(e.currentTarget.value))} />
    </label>
    <div class="toggles">
      <button class:on={app.levers.rail} onclick={() => set("rail", !app.levers.rail)}>trains</button>
      <button class:on={app.levers.outage} onclick={() => set("outage", !app.levers.outage)}>port closed 1 wk</button>
      <button class:on={app.levers.roadClosure} onclick={() => set("roadClosure", !app.levers.roadClosure)}>Tod Hwy closed</button>
    </div>
  {:else}
    <div class="fine hint">Pick a scenario above to change the season — or switch to <b>Advanced</b> (top of panel) to drag the levers yourself.</div>
  {/if}

  {#if app.viewMode === "simple"}
    {#if sentences && (sentences.lines.length || sentences.verdict)}
      <div class="tk">
        <div class="tkt">What this changes</div>
        <p class="verdict">{sentences.verdict}</p>
        <ul class="plain">
          {#each sentences.lines as l}<li>{l}</li>{/each}
        </ul>
        <div class="fine">Dollar figures are rough, order-of-magnitude estimates — see “About” for how they're worked out.</div>
      </div>
    {:else if app.scenario !== "baseline" && app.baseline}
      <div class="tk"><div class="fine">Let the season play — what this scenario changes will be summed up here.</div></div>
    {/if}
  {:else if takeaways.length}
    <div class="tk">
      <div class="tkt">What changed{app.snap && app.snap.day < 360 ? ` (to ${app.snap.dateIso})` : ""}</div>
      {#each takeaways as t}
        <div class="row {t.dir}">
          <span>{t.text}</span>
          {#if t.money}<span class="money">{t.money}</span>{/if}
        </div>
      {/each}
      <div class="fine">Indicative dollars: 10¢/t·km cartage, ~A$30k per ship-day waiting, ~$380/t farm-gate (assumptions A18–A19).</div>
    </div>
  {:else if app.scenario !== "baseline" && app.baseline}
    <div class="tk"><div class="fine">Play the season — deltas vs baseline appear here.</div></div>
  {/if}
</div>

<style>
  .levers {
    margin-top: 10px;
    background: #101c2c;
    border: 1px solid #223650;
    border-radius: 8px;
    padding: 8px 10px;
  }
  .head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .t {
    font-weight: 700;
    font-size: 12px;
  }
  .reset {
    background: none;
    border: 1px solid #31465e;
    color: #9db1c5;
    border-radius: 5px;
    font-size: 10px;
    padding: 2px 7px;
    cursor: pointer;
  }
  .story {
    color: #8fa3b8;
    font-size: 11px;
    margin: 6px 0 8px;
    line-height: 1.4;
  }
  label {
    display: block;
    margin-top: 6px;
    font-size: 11px;
    color: #9db1c5;
  }
  label b {
    color: #dfe7ef;
  }
  label input {
    width: 100%;
    margin-top: 2px;
  }
  .toggles {
    display: flex;
    gap: 6px;
    margin-top: 8px;
  }
  .toggles button {
    flex: 1;
    background: #17263a;
    border: 1px solid #31465e;
    color: #9db1c5;
    border-radius: 6px;
    padding: 4px 0;
    font-size: 11px;
    cursor: pointer;
  }
  .toggles button.on {
    background: #7a4a1d;
    border-color: #b06f2c;
    color: #ffe3bd;
  }
  .tk {
    margin-top: 10px;
    border-top: 1px solid #223650;
    padding-top: 7px;
  }
  .tkt {
    font-size: 11px;
    font-weight: 700;
    color: #cfdbe8;
    margin-bottom: 4px;
  }
  .row {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 11.5px;
    padding: 2px 0;
  }
  .row.up {
    color: #f0b46a;
  }
  .row.down {
    color: #7dd3a8;
  }
  .row .money {
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
  .fine {
    color: #64788c;
    font-size: 9.5px;
    margin-top: 5px;
    line-height: 1.35;
  }
  .hint b {
    color: #9db1c5;
  }
  .verdict {
    margin: 2px 0 6px;
    font-size: 12.5px;
    line-height: 1.45;
    color: #ffe9c2;
    font-weight: 600;
  }
  ul.plain {
    margin: 0;
    padding-left: 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  ul.plain li {
    font-size: 11.5px;
    line-height: 1.45;
    color: #c8d4e0;
  }
</style>
