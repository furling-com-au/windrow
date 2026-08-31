<script module lang="ts">
  let seq = 0;
</script>

<script lang="ts">
  /**
   * A "?" chip that reveals an explanation (#31).
   *
   * These explanations used to live in `title="..."` attributes: real, load-bearing content
   * (what a KPI counts, which figures are fitted vs published, which assumption number a
   * lever moves) that only ever appeared on mouse hover — invisible on touch, unreachable by
   * keyboard. This is the same text behind a real button: focusable, activated by click or
   * Enter/Space, closed by Escape, and announced as an expandable disclosure.
   *
   * The text expands in normal flow rather than floating, so it can't be clipped by the
   * control panel's own scroll container and needs no positioning maths on a narrow screen.
   */
  let { text, label }: { text: string; label: string } = $props();

  const id = `infotip-${++seq}`;
  let open = $state(false);

  function toggle(e: MouseEvent) {
    // these chips sit inside <label> elements — without this, the browser forwards the
    // click on to the label's slider and drags it while opening the explanation
    e.preventDefault();
    e.stopPropagation();
    open = !open;
  }
</script>

<button
  type="button"
  class="q"
  aria-expanded={open}
  aria-controls={id}
  aria-label="Explain {label}"
  onclick={toggle}
  onkeydown={(e) => {
    if (e.key === "Escape" && open) {
      e.stopPropagation();
      open = false;
    }
  }}>?</button
>
{#if open}
  <span class="tip" {id} role="note">{text}</span>
{/if}

<style>
  .q {
    display: inline-block;
    margin-left: 4px;
    width: 13px;
    height: 13px;
    line-height: 11px;
    padding: 0;
    text-align: center;
    border-radius: 50%;
    background: #223650;
    border: 1px solid #31465e;
    color: #9db1c5;
    font-size: 9px;
    font-weight: 700;
    vertical-align: 1px;
    cursor: help;
  }
  .q:hover {
    background: #2d4568;
  }
  .q[aria-expanded="true"] {
    background: #2b578a;
    border-color: #3e73b3;
    color: #fff;
  }
  .q:focus-visible {
    outline: 2px solid #7db3e8;
    outline-offset: 2px;
  }
  .tip {
    display: block;
    margin: 4px 0 2px;
    background: #16273c;
    border-left: 2px solid #3e73b3;
    border-radius: 4px;
    padding: 5px 7px;
    color: #a9bccf;
    font-size: 10.5px;
    font-weight: 400;
    line-height: 1.4;
    white-space: normal;
  }
</style>
