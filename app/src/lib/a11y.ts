/**
 * Shared accessibility behaviour for the app's dialogs (#31).
 *
 * Every modal here previously relied on a pointer: the About modal's Escape handler sat on
 * a backdrop <div tabindex="-1"> that never actually received focus, so Escape did nothing,
 * and the intro and tour had no dialog semantics at all. This action is the one place that
 * behaviour now lives, so all three behave the same way:
 *
 *   - focus moves into the dialog when it opens (the dialog box itself by default, so a
 *     screen reader reads the title and body from the top; mark a control [data-autofocus]
 *     to start there instead),
 *   - Tab and Shift+Tab cycle within the dialog rather than leaking to the page behind it,
 *   - Escape closes,
 *   - focus returns to whatever opened the dialog when it closes.
 *
 * Apply it to the element that carries role="dialog" (which therefore needs tabindex="-1").
 */

const FOCUSABLE = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

const isVisible = (el: HTMLElement) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);

export interface DialogParams {
  /** called on Escape; should be the same close the dialog's own button performs */
  onclose?: () => void;
}

export function dialog(node: HTMLElement, params: DialogParams = {}) {
  let onclose = params.onclose;
  const opener = document.activeElement as HTMLElement | null;

  const focusables = () => [...node.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(isVisible);

  // The dialog box itself is the default landing spot: the About modal's only control is a
  // Close button at the very end, and starting there would skip past everything it says.
  const autofocus = node.querySelector<HTMLElement>("[data-autofocus]");
  (autofocus ?? node).focus({ preventScroll: true });

  function onKeydown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      onclose?.();
      return;
    }
    if (e.key !== "Tab") return;
    const items = focusables();
    if (items.length === 0) {
      e.preventDefault(); // nothing to move to — keep focus on the dialog
      return;
    }
    const first = items[0]!;
    const last = items[items.length - 1]!;
    const active = document.activeElement;
    if (e.shiftKey && (active === first || active === node)) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && (active === last || active === node)) {
      e.preventDefault();
      first.focus();
    }
  }

  node.addEventListener("keydown", onKeydown);

  return {
    update(p: DialogParams) {
      onclose = p.onclose;
    },
    destroy() {
      node.removeEventListener("keydown", onKeydown);
      // The opener is often gone by the time the dialog closes (the intro's own button
      // opens the tour, then the intro unmounts), and on a cold load it is just <body> —
      // restoring focus to body would yank it away from whatever opened next. Only give
      // focus back to a real, still-present control.
      if (opener && opener !== document.body && document.contains(opener) && typeof opener.focus === "function") {
        opener.focus({ preventScroll: true });
      }
    },
  };
}
