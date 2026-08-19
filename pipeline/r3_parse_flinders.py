"""R3/R8: parse Flinders Port Holdings monthly statistics workbooks.

Outputs:
  data/processed/port_shipments_monthly.parquet  - per port x month x grain commodity, tonnes (MTD)
  data/processed/port_vessel_calls_monthly.parquet - per port x month x vessel class, call count

Workbook quirks: merged cells surface as None (forward-fill Port / Reporting Group);
'Total' rows skipped; Bulk Break columns per month are
[IMPORT Tonnes, IMPORT Volume, EXPORT Tonnes, EXPORT Volume, Total Tonnes, Total Volume]
with empty import cells -> for grain rows we validate EXPORT == Total to catch shifts.
Vessel Calls sheet holds the full calendar year (month columns) -> parsed from each
December workbook + the latest workbook of the current year.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import fastexcel
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW

MONTH_MAP = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

FNAME_RE = re.compile(
    r"(?:Copy-of-)?(\d{1,2})\.?-Statistics-([A-Za-z]{3,9})-?(\d{2})(?:-V\d+)?\.xlsx", re.I
)


def to_num(c) -> float | None:
    if isinstance(c, (int, float)):
        return float(c)
    if isinstance(c, str):
        try:
            return float(c.replace(",", "").strip())
        except ValueError:
            return None
    return None


def parse_bulk_break(path: Path, year: int, month: int) -> list[dict]:
    """Handles both layouts:
    - narrow (2025+, sheet 'Bulk Break'): one month/file;
      cols 0 Port | 1 Group | 2 Commodity | 3-4 IMPORT T/V | 5-6 EXPORT T/V | 7-8 TOTAL T/V
    - wide (2022-2024, sheet 'Bulk BreakBulk'): calendar-year cumulative; month blocks of
      4 cols [(MM) Mon: IMPORT T,V, EXPORT T,V] found from the '(01) Jan' header row.
    """
    xl = fastexcel.read_excel(str(path))
    # sheet name varies across years: "Bulk Break", "Bulk BreakBulk", "Bulk Break Bulk"
    sheet = next((s for s in xl.sheet_names if re.sub(r"\s+", "", s).lower().startswith("bulkbreak")), None)
    if sheet is None:
        return []
    df = xl.load_sheet_by_name(sheet, header_row=None).to_polars()
    rows = [list(r) for r in df.iter_rows()]

    # detect wide layout: a header row containing >=2 "(NN) Mon" labels
    month_blocks: dict[int, int] = {}  # start col -> month number
    for r in rows[:8]:
        found = {}
        for j, c in enumerate(r):
            if isinstance(c, str):
                m = re.match(r"\((\d{2})\)\s+([A-Za-z]{3})", c.strip())
                if m and m.group(2).title() in MONTH_MAP:
                    found[j] = int(m.group(1))
        if len(found) >= 2:
            month_blocks = found
            break

    # 2022-2023 wide files have an extra "Pack Class" column: Port | Pack Class |
    # Reporting Group | months... (no commodity split). Later files: Port | Reporting
    # Group | Commodity | ...
    has_pack_class = any(
        isinstance(c, str) and c.strip() == "Pack Class" for r in rows[:8] for c in r
    )
    out = []
    port = group = None
    for r in rows:
        r = r + [None] * (17 - len(r))
        c0 = r[0]
        group_cell = r[2] if has_pack_class else r[1]
        commodity_cell = None if has_pack_class else r[2]
        if isinstance(c0, str) and c0.strip() and "Flinders" not in c0 and c0.strip() not in ("Port", "Total") and "Cal Yr" not in c0 and "Import/Export" not in c0:
            port = c0.strip()
        if isinstance(group_cell, str) and group_cell.strip() and group_cell.strip() not in ("Reporting Group", "Total"):
            group = group_cell.strip()
        if group != "Grain":
            continue
        if has_pack_class:
            # one row per group; only take the row where the group label itself appears
            if not (isinstance(group_cell, str) and group_cell.strip() == "Grain"):
                continue
            commodity = "(all grain)"
        else:
            commodity = commodity_cell.strip() if isinstance(commodity_cell, str) and commodity_cell.strip() else None
            if commodity is None or commodity == "Total":
                continue
        if month_blocks:
            for col, mon in month_blocks.items():
                import_t = to_num(r[col]) or 0.0
                export_t = to_num(r[col + 2]) or 0.0
                if import_t == 0.0 and export_t == 0.0:
                    continue
                out.append(
                    {"year": year, "month": mon, "port": port, "commodity": commodity,
                     "export_t": export_t, "import_t": import_t, "qa_flag": "",
                     "source_file": path.name}
                )
        else:
            import_t = to_num(r[3]) or 0.0
            export_t = to_num(r[5]) or 0.0
            total_t = to_num(r[7])
            if export_t == 0.0 and import_t == 0.0 and total_t is None:
                continue
            flag = "" if total_t is None or abs((import_t + export_t) - total_t) < 1.0 else "CHECK_COLUMNS"
            out.append(
                {"year": year, "month": month, "port": port, "commodity": commodity,
                 "export_t": export_t, "import_t": import_t, "qa_flag": flag, "source_file": path.name}
            )
    return out


def parse_vessel_calls(path: Path, year: int) -> list[dict]:
    xl = fastexcel.read_excel(str(path))
    if "Vessel Calls" not in xl.sheet_names:
        return []
    df = xl.load_sheet_by_name("Vessel Calls", header_row=None).to_polars()
    rows = list(df.iter_rows())
    header = None
    month_cols: dict[int, int] = {}
    out = []
    port = None
    for r in rows:
        cells = list(r)
        if header is None:
            for i, c in enumerate(cells):
                if isinstance(c, str) and re.match(r"\(\d{2}\)\s", c.strip()):
                    mon = c.strip().split()[-1][:3]
                    if mon in MONTH_MAP:
                        month_cols[i] = MONTH_MAP[mon]
            if month_cols and any(isinstance(c, str) and c.strip() == "Port" for c in cells):
                header = cells
            continue
        c0, c1 = cells[0], cells[1]
        if isinstance(c0, str) and c0.strip() and c0.strip() != "Total":
            port = c0.strip()
        vclass = c1.strip() if isinstance(c1, str) and c1.strip() else None
        if not vclass or vclass == "Total":
            continue
        for col, mon in month_cols.items():
            v = to_num(cells[col]) if col < len(cells) else None
            if v:
                out.append({"year": year, "month": mon, "port": port, "vessel_class": vclass,
                            "calls": int(v), "source_file": path.name})
    return out


def main():
    files = []
    for f in (RAW / "flinders_stats").glob("*.xlsx"):
        m = FNAME_RE.match(f.name)
        if m:
            mon = MONTH_MAP.get(m.group(2).title()[:3], 0)
            if mon:
                files.append((2000 + int(m.group(3)), mon, f))
        else:
            print(f"  skipped (no filename match): {f.name}")
    # dedupe by (year, month): prefer plain file over Copy-of, and -V2 over base
    def pref(f: Path) -> tuple[int, int, str]:
        v = re.search(r"-V(\d+)", f.name)
        return (0 if f.name.lower().startswith("copy-of") else 1, int(v.group(1)) if v else 1, f.name)

    by_month: dict[tuple[int, int], Path] = {}
    for year, mon, f in files:
        cur = by_month.get((year, mon))
        if cur is None or pref(f) > pref(cur):
            by_month[(year, mon)] = f
    dropped = len(files) - len(by_month)
    files = sorted((y, m, f) for (y, m), f in by_month.items())
    print(f"monthly workbooks: {len(files)} (deduped {dropped})")

    ship_rows: list[dict] = []
    for year, month, f in files:
        try:
            ship_rows += parse_bulk_break(f, year, month)
        except Exception as e:  # noqa: BLE001
            print(f"  WARN bulk-break {f.name}: {e}")
    # wide-layout files repeat earlier months of the same year -> keep the row from the
    # latest source file per (year, month, port, commodity); files iterated in date order
    ships = pl.DataFrame(ship_rows).unique(
        subset=["year", "month", "port", "commodity"], keep="last"
    )
    ships.write_parquet(PROCESSED / "port_shipments_monthly.parquet")
    flagged = ships.filter(pl.col("qa_flag") != "").height
    print(f"grain shipment rows: {ships.height} (flagged: {flagged})")

    # vessel calls: December workbook per year + last workbook of final year
    call_rows: list[dict] = []
    by_year: dict[int, list[tuple[int, Path]]] = {}
    for year, month, f in files:
        by_year.setdefault(year, []).append((month, f))
    for year, lst in sorted(by_year.items()):
        month, f = max(lst)
        try:
            call_rows += parse_vessel_calls(f, year)
        except Exception as e:  # noqa: BLE001
            print(f"  WARN vessel-calls {f.name}: {e}")
    calls = pl.DataFrame(call_rows)
    calls.write_parquet(PROCESSED / "port_vessel_calls_monthly.parquet")
    print(f"vessel call rows: {calls.height}")

    # headline QA
    pl_ships = ships.filter(pl.col("port") == "Port Lincoln")
    print("\nPort Lincoln grain exports by shipping year (Oct-Sep, tonnes):")
    sy = pl_ships.with_columns(
        pl.when(pl.col("month") >= 10).then(pl.col("year")).otherwise(pl.col("year") - 1).alias("sy")
    ).group_by("sy").agg(pl.col("export_t").sum().alias("tonnes")).sort("sy")
    print(sy)
    print("\nPort Lincoln Dry Bulk vessel calls per month (from Vessel Calls sheets):")
    plc = calls.filter((pl.col("port") == "Port Lincoln") & (pl.col("vessel_class") == "Dry Bulk"))
    with pl.Config(tbl_rows=60):
        print(plc.sort("year", "month").select("year", "month", "calls"))


if __name__ == "__main__":
    main()
