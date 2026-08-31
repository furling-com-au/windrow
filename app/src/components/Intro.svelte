<script lang="ts">
  import { app } from "../state.svelte";
  import { dialog } from "../lib/a11y";

  let { onwatch }: { onwatch: () => void } = $props();

  function watch() {
    localStorage.setItem("windrow_intro", "1");
    onwatch();
  }

  function tour() {
    localStorage.setItem("windrow_intro", "1");
    app.tourStep = 0;
    app.showTour = true;
    onwatch();
  }
</script>

<div class="backdrop">
  <!-- Escape does the same as "Watch the season": dismiss and start watching. It does not
       silently skip the intro without recording it, so a keyboard user gets the same
       "don't show this again" behaviour the buttons give. -->
  <div
    class="card"
    role="dialog"
    aria-modal="true"
    aria-labelledby="intro-title"
    tabindex="-1"
    use:dialog={{ onclose: watch }}
  >
    <div class="kicker">A living map of a real harvest</div>
    <h2 id="intro-title">Every spring, South Australia's Eyre Peninsula strips 2–3 million tonnes of grain.</h2>
    <p>
      It moves entirely by truck — paddock to country silo, silo to port — and then ships to
      the world from Port Lincoln. <strong>Windrow rebuilds that whole system as a working
      simulation</strong>: every paddock, truck, silo and ship, driven by real weather, and
      checked against what farmers actually delivered each week.
    </p>
    <p>
      Watch a season unfold. Then change it — a drought, the port closed for a week, the old
      railway brought back — and see what it costs.
    </p>
    <div class="btns">
      <button class="go" onclick={watch}>▶ Watch the season</button>
      <button class="alt" onclick={tour}>Take the 1-minute tour</button>
    </div>
    <div class="fine">Built from public data only · a simulation, not operational data</div>
  </div>
</div>

<style>
  .backdrop {
    position: absolute;
    inset: 0;
    background: rgba(5, 10, 17, 0.72);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 25;
    backdrop-filter: blur(3px);
  }
  .card {
    width: min(520px, 92vw);
    max-height: 90vh;
    overflow-y: auto;
    background: #101c2c;
    border: 1px solid #3e73b3;
    border-radius: 14px;
    padding: 26px 30px;
    color: #dfe7ef;
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6);
  }
  .kicker {
    color: #7db3e8;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
  }
  h2 {
    margin: 0 0 10px;
    font-size: 19px;
    line-height: 1.35;
  }
  p {
    margin: 0 0 10px;
    font-size: 13.5px;
    line-height: 1.55;
    color: #b9c7d6;
  }
  .btns {
    display: flex;
    gap: 10px;
    margin: 16px 0 10px;
    flex-wrap: wrap;
  }
  .go {
    background: #2b6a45;
    border: 1px solid #3d8a5c;
    color: #fff;
    font-size: 14px;
    font-weight: 700;
    border-radius: 8px;
    padding: 10px 18px;
    cursor: pointer;
  }
  .go:hover {
    background: #347a51;
  }
  .card:focus {
    outline: none;
  }
  .card:focus-visible {
    outline: 2px solid #7db3e8;
    outline-offset: 3px;
  }
  .btns button:focus-visible {
    outline: 2px solid #7db3e8;
    outline-offset: 2px;
  }
  .alt {
    background: #17263a;
    border: 1px solid #31465e;
    color: #b9c7d6;
    border-radius: 8px;
    padding: 10px 14px;
    cursor: pointer;
    font-size: 13px;
  }
  .fine {
    color: #64788c;
    font-size: 10.5px;
  }

  /* mobile (#30): 12px text floor and 4.5:1 on #64788c (3.76:1 before) */
  @media (max-width: 800px) {
    .card {
      max-height: 88vh;
      overflow-y: auto;
      padding: 22px 20px;
    }
    .kicker {
      font-size: 12px;
    }
    .fine {
      font-size: 12px;
      color: #7d90a4;
    }
    .btns .go,
    .btns .alt {
      flex: 1 1 100%;
    }
  }
</style>
