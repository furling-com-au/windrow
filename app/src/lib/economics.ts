/**
 * Indicative unit economics for the takeaways panel. Every figure is either derived
 * from a cited publication or registered as an assumption in data/ASSUMPTIONS.md.
 * All outputs are labelled "indicative" in the UI — this is a what-if lens, not a
 * costing model.
 */
import { defaultParams } from "@windrow/sim";
import priceSummary from "../../../data/processed/cash_prices/summary.json";

/** A$/tonne-km road grain freight (A18). Sanity: x ~144 km avg site->port haul
 *  ≈ A$14/t cartage, consistent with published $60-75/t whole-of-chain at 200 km
 *  (AEGIC via ESCOSA 2019) of which cartage is roughly a quarter to a third. */
export const FREIGHT_PER_T_KM = 0.10; // range 0.07-0.13

/** A$/vessel-day at anchor (A19): handy-to-panamax demurrage-equivalent,
 *  ~US$15-25k/day => ~A$30k/day mid-range. */
export const DEMURRAGE_PER_DAY = 30000;

/** A$ per tonne per day for harvested grain waiting on farm (A22): financing only —
 *  ~$380/t at ~9% p.a. agricultural overdraft ≈ 9c/t/day. Weather, insect and quality
 *  risk of on-farm holding are real but not publicly priceable, so NOT included. */
export const HOLDING_PER_T_DAY = 0.09;

/** A$/t farm-gate value by season, computed from PIRSA published farm-gate totals
 *  divided by production (2022/23 $4.8B/12.79Mt; 2023/24 $3.3B/8.70Mt;
 *  2024/25 $2.1B/5.17Mt). 2025/26 + live season: recent-mean, flagged assumed. */
export const FARMGATE_PER_T: Record<string, number> = {
  "2022/23": 375,
  "2023/24": 379,
  "2024/25": 406,
  "2025/26": 380,
  "2026/27": 380,
};

/** Most recent day's posted cash bids from the operator's public board (site-level
 *  "active purchase options", mobilews API — see SOURCES.md operator-cash-prices-api).
 *  Captured daily by .github/workflows/prices.yml into data/processed/cash_prices/ and
 *  baked in here at build time, so the weekly redeploy refreshes the levels shown.
 *  epBids = bids at Eyre Peninsula sites: 0 off-season; buyers post there at harvest. */
export const CASH_BIDS = (() => {
  const days = Object.entries(priceSummary.days).filter(([, d]) => d.bids > 0);
  const last = days[days.length - 1];
  if (!last) return null;
  const [date, d] = last;
  return { date, bids: d.bids, sites: d.sites, epBids: d.epBids, medianPerT: d.medianPerT as Record<string, number> };
})();

/** A23: express a Lucky Bay attractiveness multiplier as an equivalent cash premium.
 *  Site choice is weight = attract / cost^β (β = calibrated choiceBeta), so multiplying
 *  attract by m shrinks a farm's generalized cost by the fraction 1 − m^(−1/β); that
 *  saving is priced with the A18 freight rate over a representative eastern-peninsula
 *  haul (90 generalized minutes at 80 km/h). Indicative — the sim itself has no money. */
export const REP_HAUL_MIN = 90;
export const REP_SPEED_KMH = 80;
export function biasToPremiumPerT(mult: number, freightPerTKm: number): number {
  if (mult <= 0) return -Infinity;
  const beta = defaultParams().choiceBeta;
  const minutesSaved = REP_HAUL_MIN * (1 - Math.pow(mult, -1 / beta));
  return minutesSaved * (REP_SPEED_KMH / 60) * freightPerTKm;
}

/** Rounds to 2 significant figures, e.g. 441.9 -> "440", 7.9 -> "7.9", 25.3 -> "25". */
function round2sf(x: number): string {
  if (x === 0) return "0";
  const mag = Math.pow(10, Math.floor(Math.log10(x)) - 1);
  const rounded = Math.round(x / mag) * mag;
  return rounded < 10 ? rounded.toFixed(1) : Math.round(rounded).toString();
}

// The panel calls every dollar figure a "rough, order-of-magnitude estimate" two lines
// away from a number rendered to 4 significant figures ("$441.9m") — false precision
// the reader has no way to know is false (F35). $m/$b figures now round to 2 s.f. with a
// leading "~"; $k and under are already coarse enough that 2 s.f. would just be noisy.
export function fmtMoney(aud: number): string {
  const a = Math.abs(aud);
  const sign = aud < 0 ? "−" : "";
  if (a >= 1e9) return `${sign}~$${round2sf(a / 1e9)}b`;
  if (a >= 1e6) return `${sign}~$${round2sf(a / 1e6)}m`;
  if (a >= 1e3) return `${sign}$${(a / 1e3).toFixed(0)}k`;
  return `${sign}$${a.toFixed(0)}`;
}

// One tonnage convention for the whole app instead of five (F35): "2.23 million t",
// "35k t", "824 t" depending on scale, always rounded — never the raw exact tonne count
// a display like this can't actually be more precise than its inputs support.
export function fmtTonnes(t: number): string {
  const a = Math.abs(t);
  const sign = t < 0 ? "−" : "";
  if (a >= 950000) return `${sign}${(a / 1e6).toFixed(2)} million t`;
  if (a >= 1000) return `${sign}${Math.round(a / 1000).toLocaleString()}k t`;
  return `${sign}${Math.round(a).toLocaleString()} t`;
}
