"""Phase 2 (best-effort): vessel names from archived shipping-stem PDFs -> vessels_*.json.

Parses the Pt Lincoln section of every cached stem snapshot, extracts
(vessel, volume, commodity, dates), dedupes, and attaches a name candidate to each
AIS berth visit when a stem entry's dates fall within +/-6 days of the visit.
Names are garnish for the UI; unmatched visits keep their anonymous craft id.
Output: data/processed/stem_entries.parquet + names patched into app bundle files.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pdfplumber
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW, ROOT

APP_DATA = ROOT / "app" / "public" / "data"
COMMODITIES = ["Wheat", "Barley", "Canola", "Lentils", "Beans", "Peas", "Oats", "Lupins", "Chickpeas", "Sorghum", "Durum"]
ROW_RE = re.compile(r"^\s*\d{6,12}\s+LIN\s+(.+)$")
DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
VOL_RE = re.compile(r"([\d,]{4,})")

SECTION_STARTS = ("PT LINCOLN", "PORT LINCOLN")
SECTION_ENDS = ("THEVENARD", "WALLAROO", "PT GILES", "PORT GILES", "OUTER HARBOR", "INNER HARB")


def parse_stem(path: Path) -> list[dict]:
    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception:
        return []
    if not text:
        return []
    up = text.upper()
    start = -1
    for s in SECTION_STARTS:
        start = up.find(s)
        if start >= 0:
            break
    if start < 0:
        return []
    end = len(text)
    for e in SECTION_ENDS:
        i = up.find(e, start + 12)
        if i > 0:
            end = min(end, i)
    section = text[start:end]
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", path.name)
    snap = date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
    out = []
    for ln in section.splitlines():
        mm = ROW_RE.match(ln)
        if not mm:
            continue
        rest = mm.group(1)
        vol = None
        vm = VOL_RE.search(rest)
        name = rest
        if vm:
            name = rest[: vm.start()].strip()
            try:
                vol = int(vm.group(1).replace(",", ""))
            except ValueError:
                vol = None
        name = re.sub(r"\s+", " ", name).strip(" -")
        if not name or len(name) < 3 or name.upper() in ("TBA", "TBN", "VESSEL TBA"):
            continue
        commodity = next((c for c in COMMODITIES if c.lower() in rest.lower()), None)
        dates = []
        for dm in DATE_RE.finditer(ln):
            try:
                dates.append(date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1))))
            except ValueError:
                pass
        out.append(
            {
                "snapshot": snap.isoformat() if snap else None,
                "vessel": name.title(),
                "volume_t": vol,
                "commodity": commodity,
                "date_min": min(dates).isoformat() if dates else None,
                "date_max": max(dates).isoformat() if dates else None,
                "source_file": path.name,
            }
        )
    return out


def main():
    rows = []
    for f in sorted((RAW / "stems" / "wayback").glob("*.pdf")) + sorted((RAW / "stems" / "current").glob("*shipping-stem*.pdf")):
        rows += parse_stem(f)
    df = pl.DataFrame(rows)
    if df.height == 0:
        print("no stem rows parsed")
        return
    df.write_parquet(PROCESSED / "stem_entries.parquet")
    print(f"stem rows: {df.height} from {df['source_file'].n_unique()} snapshots; vessels: {df['vessel'].n_unique()}")

    # entries with a usable window
    ent = df.filter(pl.col("date_min").is_not_null()).with_columns(
        pl.col("date_min").str.to_date(), pl.col("date_max").str.to_date()
    )
    # dedupe by vessel + rough month. Both the sort and maintain_order matter: polars'
    # unique() does not preserve order by default, and the greedy match below resolves
    # ties by iteration order — without a total order over the candidates the published
    # name_candidate labels shuffle between identical builds.
    ent = (
        ent.with_columns(pl.col("date_min").dt.strftime("%Y-%m").alias("mon"))
        .sort(["vessel", "mon", "date_min", "date_max", "source_file"])
        .unique(subset=["vessel", "mon"], keep="first", maintain_order=True)
    )

    for season in ("2023-24", "2024-25", "2025-26"):
        fpath = APP_DATA / f"vessels_{season}.json"
        vj = json.loads(fpath.read_text(encoding="utf-8"))
        matched = 0
        used: set[tuple[str, str]] = set()
        # Idempotent: drop any names a previous run left, or a visit that no longer matches
        # keeps a stale candidate forever (one did, until 2026-09-06).
        for visit in vj["port_lincoln_berth_visits"]:
            for k in ("name_candidate", "stem_volume_t", "stem_commodity"):
                visit.pop(k, None)
        for visit in vj["port_lincoln_berth_visits"]:
            t0 = datetime.fromisoformat(visit["arrive"]).date()
            best = None
            for e in ent.iter_rows(named=True):
                if (e["vessel"], e["mon"]) in used:
                    continue
                lo = e["date_min"] - timedelta(days=6)
                hi = e["date_max"] + timedelta(days=6)
                if lo <= t0 <= hi:
                    # (day gap, vessel, month) is a total order, so equal-gap candidates
                    # resolve the same way on every run.
                    score = (abs((e["date_min"] - t0).days), e["vessel"], e["mon"])
                    if best is None or score < best[0]:
                        best = (score, e)
            if best:
                e = best[1]
                visit["name_candidate"] = e["vessel"]
                visit["stem_volume_t"] = e["volume_t"]
                visit["stem_commodity"] = e["commodity"]
                used.add((e["vessel"], e["mon"]))
                matched += 1
        vj["name_note"] = "name_candidate joined from archived shipping-stem snapshots by date window (+/-6 d); heuristic, may be wrong for overlapping calls"
        fpath.write_text(json.dumps(vj), encoding="utf-8")
        print(f"{fpath.name}: {matched}/{len(vj['port_lincoln_berth_visits'])} visits named")


if __name__ == "__main__":
    main()
