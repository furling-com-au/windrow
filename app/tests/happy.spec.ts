import { expect, test } from "@playwright/test";

/**
 * Happy path (spec Phase 4 CI): load app -> run ~1 sim week -> KPIs update.
 * Runs against `vite preview` (see playwright.config.ts).
 */
test("loads, runs a week, KPIs move", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/");
  await expect(page).toHaveTitle(/Windrow/);

  // bundle loaded: play button enabled and date shows season start
  const play = page.getByRole("button", { name: /Play/ });
  await expect(play).toBeEnabled({ timeout: 20000 });
  await expect(page.locator(".date")).toHaveText(/2025-10-01/);

  // fastest speed, then play
  await page.getByRole("button", { name: "3 d/s" }).click();
  await play.click();

  // within ~20 s of real time the sim should pass mid-November (weeks of sim time)
  await expect(page.locator(".date")).toHaveText(/2025-1[12]-|2026-/, { timeout: 30000 });

  // pause and check KPIs moved
  await page.getByRole("button", { name: /Pause/ }).click();
  const received = await page.locator(".kpi .v").first().textContent();
  expect(received).not.toBe("0.00 Mt");
  expect(errors).toEqual([]);
});
