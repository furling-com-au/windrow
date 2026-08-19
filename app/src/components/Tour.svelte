<script lang="ts">
  import { app } from "../state.svelte";

  const STEPS = [
    {
      title: "Welcome to Windrow",
      text: "This is a working simulation of how grain moves across the Eyre Peninsula each harvest — from paddocks, by truck to country silos, then to Port Lincoln and onto ships. It's built only from public data, and everything modelled is checked against what really happened.",
    },
    {
      title: "The map",
      text: "Green cells are unharvested crop; they turn gold as headers move through. Small moving dots are trucks (cyan ones shuttle silo-to-port). Circles are receival sites — they fill as grain arrives, and their ring turns red when trucks queue. Ships wait gold at anchor, turn green while loading. Click any site for detail.",
    },
    {
      title: "Time controls",
      text: "The season is already playing at one day per second — harvest gets going from mid-October. Pause any time, change speed, or drag the date slider to jump anywhere; the simulation replays to that exact day.",
    },
    {
      title: "Simulated vs actual",
      text: "The chart overlays the simulation (green) on what farmers actually delivered each week (gold dashed, from the operator's published reports). Markers show the first delivery, record weeks and rain events. The gap between the lines is the honest measure of the model.",
    },
    {
      title: "What-ifs",
      text: "Pick a scenario — a bumper year, a drought, the port closed for a week, the trains brought back. 'What changed' translates the difference into plain terms — tonnes, queues, ships waiting — and indicative dollars. Switch to Advanced (top of the panel) to drag the underlying levers yourself, light up the truck-flow heatmap, or export CSV.",
    },
    {
      title: "Trust and limits",
      text: "Simulation, not operational data: queues and stocks are modelled, and some inputs (site capacities, truck cycle times) are documented assumptions. 'About & data sources' lists every source, licence and assumption — and the whole project is open at github.com/furling-com-au/windrow.",
    },
  ];

  function close() {
    app.showTour = false;
    localStorage.setItem("windrow_tour", "1");
  }
</script>

{#if app.showTour}
  <div class="wrap">
    <div class="card">
      <div class="step">{app.tourStep + 1} / {STEPS.length}</div>
      <h3>{STEPS[app.tourStep]!.title}</h3>
      <p>{STEPS[app.tourStep]!.text}</p>
      <div class="btns">
        <button class="skip" onclick={close}>Skip</button>
        <div>
          {#if app.tourStep > 0}<button onclick={() => app.tourStep--}>Back</button>{/if}
          {#if app.tourStep < STEPS.length - 1}
            <button class="next" onclick={() => app.tourStep++}>Next</button>
          {:else}
            <button class="next" onclick={close}>Start exploring</button>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .wrap {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    padding-bottom: 60px;
    pointer-events: none;
    z-index: 15;
  }
  .card {
    pointer-events: auto;
    width: min(430px, 92vw);
    background: #101c2c;
    border: 1px solid #3e73b3;
    border-radius: 12px;
    padding: 14px 18px;
    color: #dfe7ef;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  }
  .step {
    color: #64788c;
    font-size: 10px;
  }
  h3 {
    margin: 4px 0 6px;
    font-size: 15px;
  }
  p {
    margin: 0 0 12px;
    font-size: 12.5px;
    line-height: 1.5;
    color: #b9c7d6;
  }
  .btns {
    display: flex;
    justify-content: space-between;
  }
  button {
    background: #17263a;
    color: #dfe7ef;
    border: 1px solid #31465e;
    border-radius: 6px;
    padding: 5px 12px;
    cursor: pointer;
    font-size: 12px;
    margin-left: 6px;
  }
  .next {
    background: #2b578a;
    border-color: #3e73b3;
  }
  .skip {
    background: none;
    border: none;
    color: #708396;
    margin-left: 0;
  }
</style>
