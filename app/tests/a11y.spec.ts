import { expect, test } from "@playwright/test";

/**
 * Keyboard and assistive-technology semantics (#31).
 *
 * The audit that raised #31 found svelte-check reporting a clean bill of health over an app
 * with no working Escape handler, sliders that announced as bare numbers, and site detail
 * that a pointer was the only way to reach. A linter cannot see any of that, so this suite
 * drives the real thing: it presses real keys and asserts on accessible names and roles.
 *
 * Everything here is done with the keyboard alone, except where a click stands in for a
 * step a keyboard user can equally perform (opening Advanced, pausing the clock).
 */

/** is focus currently somewhere inside an open dialog? */
const focusInDialog = () => !!document.activeElement?.closest('[role="dialog"]');

test("the intro is a real dialog: focus moves in, Tab stays in, Escape closes it", async ({ page }) => {
  await page.goto("./");

  const intro = page.getByRole("dialog", { name: /Every spring/ });
  await expect(intro).toBeVisible({ timeout: 20000 });
  await expect(intro).toHaveAttribute("aria-modal", "true");

  // focus is moved into the dialog when it opens, rather than left on the page behind it
  expect(await page.evaluate(focusInDialog)).toBe(true);

  // Tab cycles within the dialog instead of leaking out to the map and control panel
  for (let i = 0; i < 5; i++) {
    await page.keyboard.press("Tab");
    expect(await page.evaluate(focusInDialog)).toBe(true);
  }
  await page.keyboard.press("Shift+Tab");
  expect(await page.evaluate(focusInDialog)).toBe(true);

  await page.keyboard.press("Escape");
  await expect(intro).toBeHidden();
});

test.describe("with the intro already seen", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => localStorage.setItem("windrow_intro", "1"));
    await page.goto("./");
    await expect(page.locator(".kpi").first()).toBeVisible({ timeout: 20000 });
  });

  test("the first tab stop skips the map canvas, which is named rather than silent", async ({ page }) => {
    // deck.gl makes its canvas focusable and it swallows arrow keys; at minimum it has to
    // say what it is, and there has to be a way straight past it
    await expect(page.locator("canvas")).toHaveAttribute("aria-label", /Map of the Eyre Peninsula/);

    await page.keyboard.press("Tab");
    await expect(page.locator("a.skip-link")).toBeFocused();

    await page.keyboard.press("Enter");
    expect(await page.evaluate(() => document.activeElement?.id)).toBe("controls");
  });

  test("the date scrubber announces the date, not a day index", async ({ page }) => {
    const slider = page.getByRole("slider", { name: /Date in the season/ });
    // the raw value is 0-364; what gets announced is the date on screen
    await expect(slider).toHaveAttribute("aria-valuetext", /^\d{1,2} [A-Z][a-z]{2} \d{4}$/);

    await page.getByRole("button", { name: /Pause/ }).click();
    await slider.focus();
    const before = Number(await slider.inputValue());
    await page.keyboard.press("ArrowRight");
    await expect.poll(async () => Number(await slider.inputValue())).toBe(before + 1);
  });

  test("every assumption lever names itself and announces its own units", async ({ page }) => {
    await page.getByRole("button", { name: "Advanced" }).click();
    await page.getByRole("button", { name: /Model assumptions/ }).click();

    // a sample across the three groups: what-if levers, model assumptions, dollar rates
    await expect(page.getByRole("slider", { name: "How many trucks working the harvest?" })).toHaveAttribute(
      "aria-valuetext",
      /\d+ trucks/,
    );
    await expect(page.getByRole("slider", { name: "Silo unload cycle" })).toHaveAttribute("aria-valuetext", /\d+ minutes/);
    await expect(page.getByRole("slider", { name: "Freight rate" })).toHaveAttribute(
      "aria-valuetext",
      /cents per tonne-kilometre/,
    );

    // no slider anywhere may be left without an accessible name
    const unnamed = await page.evaluate(
      () => [...document.querySelectorAll('input[type="range"]')].filter((s) => !s.getAttribute("aria-label")).length,
    );
    expect(unnamed).toBe(0);
  });

  test("About traps focus, closes on Escape, and hands focus back", async ({ page }) => {
    const opener = page.getByRole("button", { name: "About & data sources" });
    await opener.focus();
    await page.keyboard.press("Enter");

    const about = page.getByRole("dialog", { name: "About Windrow" });
    await expect(about).toBeVisible();
    await expect(about).toHaveAttribute("aria-modal", "true");
    expect(await page.evaluate(focusInDialog)).toBe(true);

    for (let i = 0; i < 4; i++) {
      await page.keyboard.press("Tab");
      expect(await page.evaluate(focusInDialog)).toBe(true);
    }

    await page.keyboard.press("Escape");
    await expect(about).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test("the tour is a dialog, steps announce themselves, and Escape closes it", async ({ page }) => {
    const opener = page.getByRole("button", { name: "Take the guided tour" });
    await opener.focus();
    await page.keyboard.press("Enter");

    const tour = page.getByRole("dialog", { name: "Welcome to Windrow" });
    await expect(tour).toBeVisible();
    expect(await page.evaluate(focusInDialog)).toBe(true);
    // the step swaps under a live region, so its text change is announced
    await expect(tour.locator("[aria-live]")).toContainText("Step 1 of 6");

    await page.keyboard.press("Escape");
    await expect(tour).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test("a site's detail can be opened without a pointer", async ({ page }) => {
    const picker = page.getByRole("combobox", { name: "Open a site's detail" });
    await picker.focus();
    // native select type-ahead: the same keys a keyboard user would actually press
    await page.keyboard.type("Cummins");

    await expect(page.getByRole("region", { name: "Site detail: Cummins" })).toBeVisible();
  });

  test("the explanations that were hover-only titles open from the keyboard", async ({ page }) => {
    const chip = page.getByRole("button", { name: "Explain million tonnes delivered" });
    await chip.focus();
    await expect(chip).toHaveAttribute("aria-expanded", "false");

    await page.keyboard.press("Enter");
    await expect(chip).toHaveAttribute("aria-expanded", "true");
    await expect(page.getByText(/Grain delivered into the main network's silos and ports/)).toBeVisible();

    // nothing load-bearing is left behind in a title="" that only a mouse can reach
    const titles = await page.evaluate(() =>
      [...document.querySelectorAll("[title]")].map((e) => e.getAttribute("title") ?? ""),
    );
    // the one survivor duplicates the "?" button's own aria-label, so it carries nothing new
    expect(titles).toEqual(["Guided tour"]);
  });
});
