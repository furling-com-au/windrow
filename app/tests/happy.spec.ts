import { expect, test } from "@playwright/test";

/**
 * Happy path (spec Phase 4 CI): load app -> auto-plays -> KPIs update -> pause works.
 * Runs against `vite preview` (see playwright.config.ts).
 */
test("loads, auto-plays, KPIs move, pause works", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/");
  await expect(page).toHaveTitle(/Windrow/);

  // first visit: intro card appears; start watching
  await expect(page.getByText("A living map of a real harvest")).toBeVisible({ timeout: 20000 });
  await page.getByRole("button", { name: /Watch the season/ }).click();

  // the narrator bar explains what's happening
  await expect(page.locator(".narrator")).toBeVisible({ timeout: 20000 });

  // the sim auto-plays at 1 d/s: the date advances past the season start
  await expect(page.locator(".date")).not.toHaveText("1 Oct 2025", { timeout: 30000 });

  // speed up and let harvest begin
  await page.getByRole("button", { name: "3 d/s" }).click();
  await expect(page.locator(".date")).toHaveText(/(Nov|Dec) 2025|2026/, { timeout: 30000 });

  // pause and check KPIs moved
  await page.getByRole("button", { name: /Pause/ }).click();
  const received = await page.locator(".kpi .v").first().textContent();
  expect(received).not.toBe("0.00 Mt");

  // mode toggle exists and switches to Advanced (levers appear)
  await page.getByRole("button", { name: "Advanced" }).click();
  await expect(page.getByText("Truck fleet")).toBeVisible();

  expect(errors).toEqual([]);
});
