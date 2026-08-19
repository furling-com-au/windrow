/**
 * Pure deck.gl map (no tile server): bundled Natural Earth land + OSM roads render
 * as the basemap; sim state renders as overlays. Self-contained => works offline and
 * on any static host (Cloudflare Pages) with only ODbL/NE attribution.
 */
import { Deck, MapView } from "@deck.gl/core";
import { PathLayer, PolygonLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import type { BundleSite, Snapshot } from "@windrow/sim";

export interface StaticData {
  basemap: { land: number[][][] };
  roads: { lines: { class: string; path: [number, number][] }[] };
  paths: { cluster_site: Record<string, [number, number][]>; site_port: Record<string, [number, number][]> };
  parcels: { id: number; lon: number; lat: number; cropping_ha: number }[];
  sites: BundleSite[];
}

const PORT_GEO: Record<string, { berth: [number, number]; anchor: [number, number] }> = {
  "Port Lincoln": { berth: [135.87, -34.7155], anchor: [135.96, -34.76] },
  Thevenard: { berth: [133.6404, -32.1494], anchor: [133.69, -32.23] },
  "Lucky Bay (T-Ports port)": { berth: [137.0442, -33.7057], anchor: [137.1, -33.66] },
};

const ROAD_COLORS: Record<string, [number, number, number, number]> = {
  trunk: [136, 156, 178, 200],
  primary: [120, 140, 162, 180],
  secondary: [95, 114, 136, 150],
  tertiary: [78, 96, 116, 120],
};

const COMMODITY_COLORS: [number, number, number][] = [
  [235, 200, 90], // wheat
  [214, 168, 100], // barley
  [250, 220, 40], // canola
  [200, 90, 80], // lentils
  [150, 180, 90], // beans
  [170, 170, 170], // other
];

interface PathCache {
  pts: [number, number][];
  cum: number[];
  len: number;
}

export class DeckMap {
  private deck: Deck<MapView>;
  private data: StaticData;
  private pathCache = new Map<string, PathCache>();
  private onSiteClick?: (siteId: number) => void;

  constructor(container: HTMLDivElement, data: StaticData, onSiteClick?: (siteId: number) => void) {
    this.data = data;
    this.onSiteClick = onSiteClick;
    this.deck = new Deck<MapView>({
      parent: container,
      views: new MapView({ repeat: false, controller: { dragRotate: false, touchRotate: false } }),
      initialViewState: {
        longitude: 135.6,
        latitude: -33.6,
        zoom: 6.4,
        minZoom: 4.5,
        maxZoom: 13,
      },
      layers: [],
      getTooltip: ({ object, layer }) => {
        if (!object || !layer) return null;
        const t = (object as { __tip?: string }).__tip;
        return t ? { text: t } : null;
      },
    });
  }

  destroy() {
    this.deck.finalize();
  }

  private path(key: string, kind: "farm" | "linehaul"): PathCache | null {
    const cacheKey = kind + ":" + key;
    let pc = this.pathCache.get(cacheKey);
    if (pc) return pc;
    const raw = kind === "farm" ? this.data.paths.cluster_site[key] : this.data.paths.site_port[key];
    if (!raw || raw.length < 2) return null;
    const cum = [0];
    for (let i = 1; i < raw.length; i++) {
      const dx = raw[i]![0] - raw[i - 1]![0];
      const dy = raw[i]![1] - raw[i - 1]![1];
      cum.push(cum[i - 1]! + Math.hypot(dx, dy));
    }
    pc = { pts: raw, cum, len: cum[cum.length - 1]! };
    this.pathCache.set(cacheKey, pc);
    return pc;
  }

  /** position along a path; paths run site->cluster (farm) or port->site (linehaul), so
   *  a truck travelling TOWARD the site/port moves from the far end back to index 0. */
  private posOn(pc: PathCache, progress: number, towardEnd0: boolean): [number, number] {
    const t = towardEnd0 ? 1 - progress : progress;
    const d = t * pc.len;
    let lo = 0,
      hi = pc.cum.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (pc.cum[mid]! < d) lo = mid + 1;
      else hi = mid;
    }
    const i = Math.max(1, lo);
    const seg = pc.cum[i]! - pc.cum[i - 1]! || 1e-9;
    const f = (d - pc.cum[i - 1]!) / seg;
    const a = pc.pts[i - 1]!;
    const b = pc.pts[i]!;
    return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
  }

  update(snap: Snapshot | null, heatmap: Record<string, number> | null = null) {
    const d = this.data;
    const layers: unknown[] = [
      new PolygonLayer({
        id: "land",
        data: d.basemap.land.map((ring) => ({ ring })),
        getPolygon: (o: { ring: number[][] }) => o.ring,
        getFillColor: [26, 36, 50, 255],
        getLineColor: [70, 90, 110, 255],
        getLineWidth: 1,
        lineWidthUnits: "pixels",
        pickable: false,
      }),
      new PathLayer({
        id: "roads",
        data: d.roads.lines,
        getPath: (o: { path: [number, number][] }) => o.path,
        getColor: (o: { class: string }) => ROAD_COLORS[o.class] ?? [78, 96, 116, 90],
        getWidth: (o: { class: string }) => (o.class === "trunk" || o.class === "primary" ? 2 : 1),
        widthUnits: "pixels",
        pickable: false,
      }),
    ];

    // corridor truck-flow heatmap: cumulative loaded tonnes per route
    if (heatmap) {
      const heatData: { path: [number, number][]; t: number }[] = [];
      let maxT = 1;
      for (const [key, t] of Object.entries(heatmap)) {
        const [kind, rest] = [key.slice(0, 2), key.slice(2)];
        const poly = kind === "c:" ? this.data.paths.cluster_site[rest] : this.data.paths.site_port[rest];
        if (poly && t > 0) {
          heatData.push({ path: poly, t });
          maxT = Math.max(maxT, t);
        }
      }
      layers.push(
        new PathLayer({
          id: "truckflow",
          data: heatData,
          getPath: (o: { path: [number, number][] }) => o.path,
          getWidth: (o: { t: number }) => 1.5 + 9 * Math.sqrt(o.t / maxT),
          widthUnits: "pixels",
          getColor: (o: { t: number }) => {
            const f = Math.sqrt(o.t / maxT);
            return [255, 200 - 140 * f, 60, 60 + 150 * f] as [number, number, number, number];
          },
          capRounded: true,
          jointRounded: true,
          pickable: false,
        }),
      );
    }

    if (snap) {
      const frac = snap.parcelHarvestFrac;
      layers.push(
        new ScatterplotLayer({
          id: "parcels",
          data: d.parcels.map((p, i) => ({ ...p, f: frac[i] ?? 0 })),
          getPosition: (p: { lon: number; lat: number }) => [p.lon, p.lat],
          getRadius: 1250,
          radiusUnits: "meters",
          getFillColor: (p: { f: number; cropping_ha: number }) => {
            const f = p.f;
            // unharvested crop green -> harvested stubble gold (kept muted so the
            // infrastructure layer reads on top)
            const r = 58 + (172 - 58) * f;
            const g = 104 + (146 - 104) * f;
            const b = 58 + (84 - 58) * f;
            const alpha = Math.min(150, 30 + p.cropping_ha / 3.5);
            return [r, g, b, alpha] as [number, number, number, number];
          },
          updateTriggers: { getFillColor: snap.tick },
          pickable: false,
        }),
      );

      // trucks (cap render at 2000; sim remains authoritative)
      const trucks: { pos: [number, number]; kind: string; commodity: number }[] = [];
      for (const t of snap.trucks) {
        if (trucks.length >= 2000) break;
        if (!t.pathKey) continue;
        const pc = this.path(t.pathKey, t.kind);
        if (!pc) continue;
        // farm paths are stored site->cluster: toward site == toward index 0 when forward
        const towardEnd0 = t.kind === "farm" ? t.forward : t.forward;
        const pos = this.posOn(pc, t.progress, towardEnd0);
        trucks.push({ pos, kind: t.kind, commodity: t.commodity });
      }
      layers.push(
        new ScatterplotLayer({
          id: "trucks",
          data: trucks,
          getPosition: (t: { pos: [number, number] }) => t.pos,
          getRadius: (t: { kind: string }) => (t.kind === "farm" ? 420 : 620),
          radiusUnits: "meters",
          radiusMinPixels: 1.2,
          radiusMaxPixels: 6,
          getFillColor: (t: { kind: string; commodity: number }) =>
            t.kind === "linehaul" ? [90, 200, 235, 235] : [...(COMMODITY_COLORS[t.commodity] ?? [200, 200, 200]), 235] as [number, number, number, number],
          updateTriggers: { getPosition: snap.tick },
          pickable: false,
        }),
      );

      // sites
      const siteData = d.sites.map((s) => {
        const sv = snap.sites[s.id];
        const stock = sv?.stockT ?? 0;
        const queue = sv?.queue ?? 0;
        const cap = s.capacity_t ?? 120000;
        return {
          ...s,
          stock,
          queue,
          fill: Math.min(1, stock / cap),
          __tip: `${s.name}\nstock ${Math.round(stock / 1000)} kt / ${Math.round(cap / 1000)} kt\nqueue ${queue} trucks`,
        };
      });
      layers.push(
        new ScatterplotLayer({
          id: "sites",
          data: siteData,
          getPosition: (s: BundleSite) => [s.lon, s.lat],
          getRadius: (s: { role: string }) => (s.role === "port" ? 3400 : 2500),
          radiusUnits: "meters",
          radiusMinPixels: 6,
          radiusMaxPixels: 22,
          stroked: true,
          getLineWidth: 2.5,
          lineWidthUnits: "pixels",
          getLineColor: (s: { queue: number }) =>
            s.queue > 20 ? [255, 80, 70, 255] : s.queue > 8 ? [255, 180, 60, 255] : [238, 244, 250, 235],
          getFillColor: (s: { fill: number; role: string; status: string }) => {
            if (s.status !== "active_2025_26" && s.status !== "active") return [58, 68, 82, 210];
            // storage fill: deep slate (empty) -> bright cyan (full) — pops against the gold
            const f = s.fill;
            return [22 + 55 * f, 52 + 160 * f, 76 + 178 * f, 250] as [number, number, number, number];
          },
          updateTriggers: { getFillColor: snap.tick, getLineColor: snap.tick },
          pickable: true,
          onClick: (info: { object?: { id?: number } }) => {
            if (info.object?.id != null) this.onSiteClick?.(info.object.id);
          },
        }),
        new TextLayer({
          id: "site-labels",
          data: siteData,
          getPosition: (s: BundleSite) => [s.lon, s.lat],
          getText: (s: { name: string; queue: number }) => (s.queue > 0 ? `${short(s.name)} (${s.queue})` : short(s.name)),
          getSize: (s: { role: string }) => (s.role === "port" ? 16 : 13),
          getColor: [255, 255, 255, 245],
          getPixelOffset: [0, -20],
          fontFamily: "system-ui, sans-serif",
          fontWeight: 700,
          outlineWidth: 4,
          outlineColor: [6, 11, 18, 245],
          fontSettings: { sdf: true },
          updateTriggers: { getText: snap.tick },
          pickable: false,
        }),
      );

      // vessels at berth/anchor per port + approach tracks
      const vesselDots: { pos: [number, number]; state: number; __tip: string }[] = [];
      const portCounts: Record<string, { anchor: number; berth: number }> = {};
      for (const v of snap.vessels) {
        const site = d.sites[v.port];
        if (!site) continue;
        const geo = PORT_GEO[site.name] ?? PORT_GEO[Object.keys(PORT_GEO).find((k) => site.name.includes(k.split(" ")[0]!)) ?? ""];
        if (!geo) continue;
        const pc = (portCounts[site.name] ??= { anchor: 0, berth: 0 });
        const isBerth = v.state === 2;
        const n = isBerth ? pc.berth++ : pc.anchor++;
        const base = isBerth ? geo.berth : geo.anchor;
        const pos: [number, number] = [base[0] + (n % 4) * 0.012, base[1] - Math.floor(n / 4) * 0.01];
        vesselDots.push({
          pos,
          state: v.state,
          __tip: `${v.name ?? "vessel #" + v.id}\n${isBerth ? "loading" : v.state === 3 ? "departed" : "at anchor"} ${Math.round(v.loadedT / 1000)}/${Math.round(v.targetT / 1000)} kt`,
        });
      }
      layers.push(
        new PathLayer({
          id: "approach",
          data: Object.values(PORT_GEO).map((g) => ({ path: [g.anchor, g.berth] })),
          getPath: (o: { path: [number, number][] }) => o.path,
          getColor: [90, 130, 160, 90],
          getWidth: 1.5,
          widthUnits: "pixels",
        }),
        new ScatterplotLayer({
          id: "vessels",
          data: vesselDots,
          getPosition: (v: { pos: [number, number] }) => v.pos,
          getRadius: 900,
          radiusUnits: "meters",
          radiusMinPixels: 4,
          radiusMaxPixels: 12,
          getFillColor: (v: { state: number }) =>
            v.state === 2 ? [80, 220, 160, 245] : v.state === 3 ? [120, 130, 145, 200] : [240, 200, 80, 245],
          stroked: true,
          getLineColor: [15, 25, 35, 255],
          getLineWidth: 1.5,
          lineWidthUnits: "pixels",
          updateTriggers: { getPosition: snap.tick, getFillColor: snap.tick },
          pickable: true,
        }),
      );
    }

    this.deck.setProps({ layers: layers as never[] });
  }
}

function short(name: string): string {
  return name.replace(" (T-Ports port)", "").replace(" (T-Ports bunker)", " (TP)").replace(" (closed)", "");
}
