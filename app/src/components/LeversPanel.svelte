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

  let story = $derived(SCENARIOS.find((s) => s.id === app.scenario)?.story ?? "Custom what-if — you moved the levers. Deltas below compare against the calibrated baseline.");

  interface Takeaway {
    text: string;
    money?: string;
    dir: "up" | "down" | "flat";
  }

  let takeaways = $derived.by((): Takeaway[] => {
    const s = app.snap;
    const b = app.baseline;
    if (!s || !b || b.receivedByDay.length === 0) return [];
    const i = Math.max(0, Math.min(s.day - 1, b.receivedByDay.length - 1));
    const out: Takeaway[] = [];
    const kt = (t: number) => `${t > 0 ? "+" : "−"}${Math.abs(t / 1000).toFixed(0)} kt`;

    const dRec = s.kpi.receivedT - (b.receivedByDay[i] ?? 0);
    if (Math.abs(dRec) > 20000)
      out.push({ text: `Bunge receivals ${kt(dRec)} vs baseline`, dir: dRec > 0 ? "up" : "down" });

    const dLb = s.kpi.receivedLbT - (b.lbByDay[i] ?? 0);
    if (Math.abs(dLb) > 10000)
      out.push({ text: `T-Ports intake ${kt(dLb)}`, dir: dLb > 0 ? "up" : "down" });

    const dShip = s.kpi.shippedT - (b.shippedByDay[i] ?? 0);
    if (Math.abs(dShip) > 20000)
      out.push({ text: `Shipped ${kt(dShip)}`, dir: dShip > 0 ? "up" : "down" });

    const dTkm = s.kpi.tonneKm - (b.tonneKmByDay[i] ?? 0);
    const freight = dTkm * FREIGHT_PER_T_KM;
    if (Math.abs(freight) > 150000)
      out.push({
        text: `Road cartage ${dTkm > 0 ? "+" : "−"}${Math.abs(dTkm / 1e6).toFixed(1)}M t·km`,
        money: `${freight > 0 ? "+" : "−"}${fmtMoney(Math.abs(freight))} freight`,
        dir: freight > 0 ? "up" : "down",
      });

    const q0 = b.queueByDay[i] ?? 0;
    if (Math.abs(s.kpi.peakQueue - q0) > 15)
      out.push({ text: `Worst site queue ${s.kpi.peakQueue} vs ${q0} trucks`, dir: s.kpi.peakQueue > q0 ? "up" : "down" });

    const waitDays = (s.kpi.meanWaitH * s.kpi.vesselsArrived) / 24;
    const baseWaitDays = ((b.waitByDay[i] ?? 0) * (b.arrivedByDay[i] ?? 0)) / 24;
    const demurrage = (waitDays - baseWaitDays) * DEMURRAGE_PER_DAY;
    if (Math.abs(demurrage) > 200000)
      out.push({
        text: `Vessel waiting ${s.kpi.meanWaitH.toFixed(0)} h/ship vs ${(b.waitByDay[i] ?? 0).toFixed(0)} h`,
        money: `${demurrage > 0 ? "+" : "−"}${fmtMoney(Math.abs(demurrage))} demurrage-equiv.`,
        dir: demurrage > 0 ? "up" : "down",
      });

    if (app.levers.productionScale !== 1.0 && app.observed) {
      const prod = Object.values(app.observed.district_production_t ?? {}).reduce((a, v) => a + v, 0);
      if (prod > 0) {
        const dv = (app.levers.productionScale - 1) * prod * (FARMGATE_PER_T[app.season] ?? 380);
        out.push({
          text: `Crop ${app.levers.productionScale > 1 ? "+" : "−"}${Math.abs((app.levers.productionScale - 1) * 100).toFixed(0)}%`,
          money: `${dv > 0 ? "+" : "−"}${fmtMoney(Math.abs(dv))} farm-gate value`,
          dir: dv > 0 ? "up" : "down",
        });
      }
    }
    return out;
  });
</script>

<div class="levers">
  <div class="head">
    <span class="t">What-if levers</span>
    <button class="reset" onclick={reset}>reset</button>
  </div>
  <p class="story">{story}</p>

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
    <span>Lucky Bay pull <b>{app.levers.luckyBayBias.toFixed(1)}×</b></span>
    <input type="range" min="0.2" max="3" step="0.1" value={app.levers.luckyBayBias}
      oninput={(e) => set("luckyBayBias", parseFloat(e.currentTarget.value))} />
  </label>
  <label>
    <span>Direct-to-port pull <b>{app.levers.portAttractBias.toFixed(1)}×</b></span>
    <input type="range" min="0.4" max="2.5" step="0.1" value={app.levers.portAttractBias}
      oninput={(e) => set("portAttractBias", parseFloat(e.currentTarget.value))} />
  </label>
  <div class="toggles">
    <button class:on={app.levers.rail} onclick={() => set("rail", !app.levers.rail)}>rail</button>
    <button class:on={app.levers.outage} onclick={() => set("outage", !app.levers.outage)}>PL outage</button>
    <button class:on={app.levers.roadClosure} onclick={() => set("roadClosure", !app.levers.roadClosure)}>Tod Hwy closed</button>
  </div>

  {#if takeaways.length}
    <div class="tk">
      <div class="tkt">Key takeaways vs baseline{app.snap && app.snap.day < 360 ? ` (to ${app.snap.dateIso})` : ""}</div>
      {#each takeaways as t}
        <div class="row {t.dir}">
          <span>{t.text}</span>
          {#if t.money}<span class="money">{t.money}</span>{/if}
        </div>
      {/each}
      <div class="fine">Indicative: 10¢/t·km cartage, ~A$30k/vessel-day, ~$380/t farm-gate (assumptions A18–A19).</div>
    </div>
  {:else if app.baseline}
    <div class="tk"><div class="fine">Run or scrub the season — deltas vs baseline appear here.</div></div>
  {:else}
    <div class="tk"><div class="fine">Computing baseline…</div></div>
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
</style>
