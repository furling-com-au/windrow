/**
 * Indicative unit economics for the takeaways panel. Every figure is either derived
 * from a cited publication or registered as an assumption in data/ASSUMPTIONS.md.
 * All outputs are labelled "indicative" in the UI — this is a what-if lens, not a
 * costing model.
 */

/** A$/tonne-km road grain freight (A18). Sanity: x ~144 km avg site->port haul
 *  ≈ A$14/t cartage, consistent with published $60-75/t whole-of-chain at 200 km
 *  (AEGIC via ESCOSA 2019) of which cartage is roughly a quarter to a third. */
export const FREIGHT_PER_T_KM = 0.10; // range 0.07-0.13

/** A$/vessel-day at anchor (A19): handy-to-panamax demurrage-equivalent,
 *  ~US$15-25k/day => ~A$30k/day mid-range. */
export const DEMURRAGE_PER_DAY = 30000;

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

export function fmtMoney(aud: number): string {
  const a = Math.abs(aud);
  const sign = aud < 0 ? "−" : "";
  if (a >= 1e9) return `${sign}$${(a / 1e9).toFixed(1)}b`;
  if (a >= 1e6) return `${sign}$${(a / 1e6).toFixed(1)}m`;
  if (a >= 1e3) return `${sign}$${(a / 1e3).toFixed(0)}k`;
  return `${sign}$${a.toFixed(0)}`;
}
