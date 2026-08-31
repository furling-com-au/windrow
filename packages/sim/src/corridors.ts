/**
 * Closed-corridor geometry for the road-closure scenario (#28).
 *
 * A corridor is a stretch of highway, not a straight line between two towns. Each entry
 * below is a polyline traced along the road's ACTUAL alignment on the OSM network: it is
 * the routed site→port polyline the pipeline already exports to `paths.json`, simplified
 * (Douglas–Peucker, ~0.015°) down to the handful of vertices that carry the shape.
 *
 * Why not the two-point axis the scenario used before: the Tod Highway bows up to 0.18°
 * (~18 km) east of the straight line through Cummins and Wudinna. Containing the real
 * road with a straight axis therefore needed a ~18 km tolerance, which is wide enough to
 * sweep in roads that are nowhere near it — while the test it fed (does the leg's
 * straight-line MIDPOINT sit inside that tolerance?) still missed legs that run the
 * corridor end to end but whose midpoint happens to fall outside. Tracing the road
 * instead lets the tolerance drop to ~5 km and makes the test a length measurement
 * rather than a single-point lottery.
 *
 * Reference routes used (see pipeline/p2_build_matrix.py → app/public/data/paths.json):
 *   tod       Port Lincoln → Wudinna       (Tod Hwy, the peninsula's central spine)
 *   lincoln   Port Lincoln → Cowell        (Lincoln Hwy, the east-coast trunk)
 *   flinders  Port Lincoln → Streaky Bay   (Flinders Hwy, the west-coast trunk)
 *   birdseye  Lock → Cowell                (Birdseye Hwy, the east–west link)
 */

export type CorridorId = "lincoln" | "tod" | "flinders" | "birdseye";

/** [lon, lat] vertices, in order along the highway. */
export const CORRIDORS: Record<CorridorId, readonly (readonly [number, number])[]> = {
  tod: [
    [135.866, -34.722], [135.689, -34.637], [135.66, -34.549], [135.684, -34.516],
    [135.728, -34.26], [135.715, -33.754], [135.693, -33.695], [135.758, -33.562],
    [135.673, -33.497], [135.644, -33.423], [135.649, -33.359], [135.559, -33.14],
    [135.46, -33.047],
  ],
  lincoln: [
    [135.866, -34.722], [135.859, -34.637], [135.926, -34.488], [136.19, -34.263],
    [136.386, -34.026], [136.564, -33.908], [136.741, -33.796], [136.857, -33.678],
  ],
  flinders: [
    [135.866, -34.722], [135.653, -34.606], [135.482, -34.551], [135.455, -34.435],
    [135.468, -34.358], [135.365, -34.119], [135.277, -34.024], [135.269, -33.92],
    [135.219, -33.816], [134.878, -33.631], [134.87, -33.6], [134.924, -33.481],
    [134.877, -33.318], [134.754, -33.25], [134.71, -33.178], [134.611, -33.114],
    [134.436, -32.915], [134.221, -32.794],
  ],
  birdseye: [
    [135.761, -33.571], [135.93, -33.645], [136.221, -33.666], [136.308, -33.701],
    [136.449, -33.691], [136.638, -33.717], [136.793, -33.672], [136.921, -33.682],
  ],
};

/**
 * Half-width of the closed corridor, in degrees (~5 km). It has to absorb the ~1.5 km
 * simplification error above plus the pipeline's own 0.004° path simplification, and be
 * generous enough that a route sitting on the highway's service side still counts. The
 * result is not knife-edge: sweeping this from 0.035 to 0.07 moves the affected share of
 * a Tod-corridor line-haul leg by only a few points, and leaves every "runs the corridor
 * end to end" leg at a share of 1.0 and every unrelated leg below 0.1.
 */
export const CORRIDOR_BAND_DEG = 0.05;

/** sampling step when walking a route, degrees (~2 km) */
const STEP_DEG = 0.02;

function distToSegment(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax,
    dy = by - ay;
  const l2 = dx * dx + dy * dy;
  const t = l2 === 0 ? 0 : Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / l2));
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function distToCorridor(px: number, py: number, corridor: readonly (readonly [number, number])[]): number {
  let best = Infinity;
  for (let i = 0; i < corridor.length - 1; i++) {
    const a = corridor[i]!,
      b = corridor[i + 1]!;
    const d = distToSegment(px, py, a[0], a[1], b[0], b[1]);
    if (d < best) best = d;
  }
  return best;
}

/**
 * What share (0..1) of `route`'s length runs inside the closed corridor.
 *
 * `route` is a [lon, lat] polyline — the real routed path where the bundle carries one,
 * otherwise the straight line between the two endpoints. Lengths are measured in degrees
 * with longitude scaled by cos(lat); only the ratio is used, so no projection is needed.
 *
 * A leg that runs the corridor for its whole length returns 1 (the scenario's full
 * factor applies, as it did before #28); a leg that merely crosses the closed road, or
 * touches it at a junction, returns a few percent. That distinction is the point: a
 * single "is this leg near the corridor?" boolean has to choose between scaling a 350 km
 * haul by 2.5× because it grazed the closure and not scaling it at all.
 */
export function corridorShare(
  route: readonly (readonly [number, number])[] | readonly number[][],
  corridor: readonly (readonly [number, number])[],
): number {
  if (!route || route.length < 2 || corridor.length < 2) return 0;
  // corridor bounding box, padded by the band: a leg wholly outside it cannot touch the
  // closure, which skips the per-sample work for most of the ~3.4k candidate legs
  let cx0 = Infinity,
    cy0 = Infinity,
    cx1 = -Infinity,
    cy1 = -Infinity;
  for (const p of corridor) {
    if (p[0]! < cx0) cx0 = p[0]!;
    if (p[0]! > cx1) cx1 = p[0]!;
    if (p[1]! < cy0) cy0 = p[1]!;
    if (p[1]! > cy1) cy1 = p[1]!;
  }
  cx0 -= CORRIDOR_BAND_DEG;
  cy0 -= CORRIDOR_BAND_DEG;
  cx1 += CORRIDOR_BAND_DEG;
  cy1 += CORRIDOR_BAND_DEG;

  let total = 0,
    inside = 0;
  for (let i = 0; i < route.length - 1; i++) {
    const a = route[i]!,
      b = route[i + 1]!;
    const ax = a[0]!,
      ay = a[1]!,
      bx = b[0]!,
      by = b[1]!;
    const kx = Math.cos((((ay + by) / 2) * Math.PI) / 180);
    const len = Math.hypot((bx - ax) * kx, by - ay);
    if (len === 0) continue;
    total += len;
    if (Math.max(ax, bx) < cx0 || Math.min(ax, bx) > cx1) continue;
    if (Math.max(ay, by) < cy0 || Math.min(ay, by) > cy1) continue;
    const n = Math.max(1, Math.ceil(len / STEP_DEG));
    const sub = len / n;
    for (let k = 0; k < n; k++) {
      const t = (k + 0.5) / n;
      if (distToCorridor(ax + (bx - ax) * t, ay + (by - ay) * t, corridor) < CORRIDOR_BAND_DEG) inside += sub;
    }
  }
  return total > 0 ? inside / total : 0;
}
