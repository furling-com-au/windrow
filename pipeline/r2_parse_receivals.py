"""R2 step 2: parse cached weekly harvest report pages -> receivals_weekly.parquet.

Input:  data/raw/viterra_reports/weekly/<slug>__<ts>.html   (Wayback snapshots)
        data/raw/bunge_news/pages/<slug>.html               (post-migration pages, if any)
Output: data/processed/receivals_weekly.parquet  (long format, one row per report x region)
        data/processed/receivals_notes.jsonl     (narrative text per report, for site mentions)
        printed QA report (row counts per season, consistency checks, unparsed files)

Parsing is deliberately tolerant: any <table> row whose first cell matches a known
region label and whose later cells contain "N,NNN tonnes" is captured. Unknown table
rows are preserved in the notes file under extra_rows, never silently dropped.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import polars as pl
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW

MONTHS = {
    m.lower(): i
    for i, m in enumerate(
        ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"], 1)
}

DATE_RE = re.compile(r"(\d{1,2})\s+(" + "|".join(MONTHS, ) + r")\s+(\d{4})", re.IGNORECASE)
NUM_RE = re.compile(r"([\d][\d,\.]*)\s*(?:tonne|mt\b|t\b)?", re.IGNORECASE)

REGION_LABELS = [
    ("total", re.compile(r"(viterra|bunge)?\s*total\s+receivals", re.I)),
    ("western", re.compile(r"western\s+region", re.I)),
    ("central", re.compile(r"central\s+region", re.I)),
    ("eastern", re.compile(r"eastern\s+region", re.I)),
]


def parse_num(cell_text: str) -> int | None:
    t = cell_text.replace("\xa0", " ").replace("*", "").strip()
    m = re.search(r"([\d][\d,]*)", t)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def week_ending_from(text: str) -> dt.date | None:
    m = DATE_RE.search(text)
    if not m:
        return None
    day, mon, year = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))
    try:
        return dt.date(year, mon, day)
    except ValueError:
        return None


def season_of(week_ending: dt.date) -> str:
    """Marketing year runs 1 Oct - 30 Sep (Bunge Port Loading Protocols)."""
    y = week_ending.year if week_ending.month >= 10 else week_ending.year - 1
    return f"{y}/{(y + 1) % 100:02d}"


def parse_report(path: Path, source: str) -> tuple[list[dict], dict] | None:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")

    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    we = week_ending_from(title) or week_ending_from(path.name.replace("-", " "))
    if we is None:
        return None
    blob = (title + " " + path.name).lower()
    if "monthly" in blob:
        report_kind = "monthly"
    elif "fortnight" in blob:
        report_kind = "fortnight"
    else:
        report_kind = "weekly"

    pub_date = None
    date_el = soup.find(string=re.compile(r"Date:\s*\d{4}/\d{2}/\d{2}"))
    if date_el:
        m = re.search(r"(\d{4})/(\d{2})/(\d{2})", str(date_el))
        if m:
            pub_date = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    rows: list[dict] = []
    extra_rows: list[list[str]] = []
    period_label = None
    for table in soup.find_all("table"):
        ths = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if len(ths) >= 2 and not period_label:
            period_label = ths[1]
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            label = cells[0]
            matched = None
            for region, rx in REGION_LABELS:
                if rx.search(label):
                    matched = region
                    break
            if matched is None:
                if any(parse_num(c) for c in cells[1:]):
                    extra_rows.append(cells)
                continue
            weekly_t = parse_num(cells[1]) if len(cells) > 1 else None
            cum_t = parse_num(cells[2]) if len(cells) > 2 else None
            rows.append(
                {
                    "season": season_of(we),
                    "week_ending": we,
                    "report_kind": report_kind,
                    "region": matched,
                    "weekly_t": weekly_t,
                    "cum_t": cum_t,
                    "period_label": period_label,
                    "title": title,
                    "pub_date": pub_date,
                    "source_file": path.name,
                    "source": source,
                }
            )

    paragraphs = [
        p.get_text(" ", strip=True)
        for p in soup.select("section p, div.text p") or soup.find_all("p")
    ]
    paragraphs = [p for p in paragraphs if len(p) > 40][:40]
    note = {
        "source_file": path.name,
        "season": season_of(we),
        "week_ending": we.isoformat(),
        "title": title,
        "narrative": paragraphs,
        "extra_rows": extra_rows,
    }
    return rows, note


def main():
    all_rows: list[dict] = []
    notes: list[dict] = []
    unparsed: list[str] = []

    sources = [(RAW / "viterra_reports" / "weekly", "wayback"), (RAW / "bunge_news" / "pages", "bunge-live")]
    for folder, source in sources:
        if not folder.exists():
            continue
        for f in sorted(folder.glob("*.html")):
            try:
                out = parse_report(f, source)
            except Exception as e:  # noqa: BLE001 - QA report catches everything
                unparsed.append(f"{f.name}: EXC {e}")
                continue
            if out is None:
                unparsed.append(f"{f.name}: no week-ending date")
                continue
            rows, note = out
            if not rows:
                unparsed.append(f"{f.name}: no region rows parsed")
            all_rows.extend(rows)
            notes.append(note)

    # dedupe: same week+region can appear from multiple snapshots -> keep wayback-latest
    df = pl.DataFrame(all_rows).unique(subset=["season", "week_ending", "region"], keep="last").sort(
        ["season", "week_ending", "region"]
    )
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.filter(pl.col("report_kind") != "monthly").write_parquet(PROCESSED / "receivals_weekly.parquet")
    df.filter(pl.col("report_kind") == "monthly").write_parquet(PROCESSED / "receivals_monthly.parquet")
    with (PROCESSED / "receivals_notes.jsonl").open("w", encoding="utf-8") as fh:
        for n in sorted(notes, key=lambda n: n["week_ending"]):
            fh.write(json.dumps(n, ensure_ascii=False) + "\n")

    print(f"rows: {df.height}  reports: {len(notes)}  unparsed: {len(unparsed)}")
    print(df.group_by("season").agg(
        pl.col("week_ending").n_unique().alias("weeks"),
        pl.col("week_ending").min().alias("first"),
        pl.col("week_ending").max().alias("last"),
    ).sort("season"))
    # season totals (max cumulative per region)
    print(df.filter(pl.col("cum_t").is_not_null()).group_by("season", "region").agg(
        pl.col("cum_t").max().alias("season_total_t")
    ).sort(["season", "region"]))
    if unparsed:
        print("\nUNPARSED:")
        for u in unparsed:
            print("  ", u)

    # weekly vs cumulative consistency
    for region in ("total", "western"):
        sub = df.filter((pl.col("region") == region) & pl.col("cum_t").is_not_null()).sort("week_ending")
        for season in sub["season"].unique().to_list():
            s = sub.filter(pl.col("season") == season)
            cums = s["cum_t"].to_list()
            weeks = s["weekly_t"].to_list()
            bad = 0
            for i in range(1, len(cums)):
                if weeks[i] is None or cums[i] is None or cums[i - 1] is None:
                    continue
                if abs((cums[i] - cums[i - 1]) - weeks[i]) > max(0.03 * max(weeks[i], 1), 2000):
                    bad += 1
            if bad:
                print(f"CONSISTENCY {region} {season}: {bad} week(s) where cum-diff != weekly (tol 3%)")


if __name__ == "__main__":
    main()
