"""R4: EP district production estimates -> data/processed/production_districts.parquet.

Values transcribed from PIRSA Crop and Pasture Report "TABLE 1 CROP ESTIMATES BY DISTRICT"
(PDFs cached under data/raw/pirsa/). Every season is spot-verified below by searching the
PDF's extracted text for the three district grain totals; a failed check fails the build.

Districts: WEP = Western Eyre Peninsula, LEP = Lower Eyre Peninsula, EEP = Eastern Eyre
Peninsula. Production = grain tonnes (hay excluded, per PIRSA table convention).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import PROCESSED, RAW

# (season, pdf, publication) -> {district: {crop: (area_ha, production_t)}}
DATA = {
    ("2022/23", "crop_pasture_2022-23_final.pdf", "2023-03"): {
        "WEP": {"wheat": (433200, 1170000), "barley": (81700, 205000), "oats": (14100, 35500),
                "triticale": (400, 600), "peas": (2800, 2800), "lupins": (1500, 1950),
                "beans": (400, 800), "chickpeas": (0, 0), "lentils": (2000, 5000),
                "vetch": (2400, 4800), "canola": (5100, 7650), "TOTAL": (543600, 1434100)},
        "LEP": {"wheat": (145200, 655000), "barley": (69600, 315000), "oats": (3200, 11200),
                "triticale": (500, 1750), "peas": (2300, 5500), "lupins": (10500, 31500),
                "beans": (7700, 27000), "chickpeas": (400, 1000), "lentils": (9000, 18000),
                "vetch": (3600, 7200), "canola": (79200, 240000), "TOTAL": (331200, 1313150)},
        "EEP": {"wheat": (362200, 1115000), "barley": (77900, 235000), "oats": (4600, 11500),
                "triticale": (500, 1250), "peas": (4200, 6250), "lupins": (4800, 9500),
                "beans": (400, 1000), "chickpeas": (200, 500), "lentils": (2200, 5500),
                "vetch": (2000, 4000), "canola": (8000, 12750), "TOTAL": (467000, 1402250)},
        "SA_TOTAL": {"TOTAL": (3933455, 12787600)},
    },
    ("2023/24", "crop_pasture_2023-24_final.pdf", "2024-03"): {
        "WEP": {"wheat": (450000, 585000), "barley": (75000, 105000), "oats": (14100, 14100),
                "triticale": (400, 400), "peas": (2800, 2240), "lupins": (0, 0),
                "beans": (400, 320), "chickpeas": (0, 0), "lentils": (20000, 16000),
                "vetch": (2400, 1200), "canola": (5100, 5100), "TOTAL": (570200, 729360)},
        "LEP": {"wheat": (145000, 551000), "barley": (67000, 261300), "oats": (0, 0),
                "triticale": (0, 0), "peas": (1500, 3000), "lupins": (10500, 21000),
                "beans": (10000, 25000), "chickpeas": (0, 0), "lentils": (10000, 22000),
                "vetch": (0, 0), "canola": (80000, 200000), "TOTAL": (324000, 1083300)},
        "EEP": {"wheat": (371000, 593600), "barley": (74000, 133200), "oats": (4600, 6440),
                "triticale": (500, 800), "peas": (4200, 3360), "lupins": (4800, 4800),
                "beans": (400, 400), "chickpeas": (200, 200), "lentils": (20000, 22000),
                "vetch": (2000, 2000), "canola": (9000, 9000), "TOTAL": (490700, 775800)},
        "SA_TOTAL": {"TOTAL": (4010600, 8703465)},
    },
    ("2024/25", "crop_pasture_2024-25_final.pdf", "2025-03"): {
        "WEP": {"wheat": (350000, 315000), "barley": (60000, 60000), "oats": (12000, 6000),
                "triticale": (0, 0), "peas": (2800, 1960), "lupins": (0, 0),
                "beans": (0, 0), "chickpeas": (0, 0), "lentils": (45000, 22500),
                "vetch": (2400, 1309), "canola": (2000, 1600), "TOTAL": (474200, 408369)},
        "LEP": {"wheat": (141000, 451200), "barley": (60000, 180000), "oats": (0, 0),
                "triticale": (0, 0), "peas": (1500, 2700), "lupins": (8500, 13600),
                "beans": (8500, 17000), "chickpeas": (0, 0), "lentils": (35000, 63000),
                "vetch": (0, 0), "canola": (75000, 180000), "TOTAL": (329500, 907500)},
        "EEP": {"wheat": (360000, 432000), "barley": (60000, 78000), "oats": (4600, 4600),
                "triticale": (0, 0), "peas": (4000, 3200), "lupins": (4800, 2880),
                "beans": (400, 320), "chickpeas": (0, 0), "lentils": (65000, 48750),
                "vetch": (0, 0), "canola": (6000, 3600), "TOTAL": (504800, 573350)},
        "SA_TOTAL": {"TOTAL": (3859640, 5169688)},
    },
    ("2025/26", "crop_pasture_2025-26_final.pdf", "2026-01"): {
        "WEP": {"wheat": (380000, 532000), "barley": (70000, 112000), "oats": (12000, 14400),
                "triticale": (0, 0), "peas": (2500, 2250), "lupins": (1500, 1375),
                "beans": (0, 0), "chickpeas": (0, 0), "lentils": (75000, 67500),
                "vetch": (2000, 1083), "canola": (4000, 3200), "TOTAL": (547000, 733808)},
        "LEP": {"wheat": (145000, 551000), "barley": (50000, 200000), "oats": (0, 0),
                "triticale": (0, 0), "peas": (1500, 3000), "lupins": (8500, 17000),
                "beans": (8000, 19200), "chickpeas": (0, 0), "lentils": (55000, 137500),
                "vetch": (4000, 8000), "canola": (80000, 208000), "TOTAL": (352000, 1143700)},
        "EEP": {"wheat": (370000, 740000), "barley": (70000, 168000), "oats": (3000, 5400),
                "triticale": (0, 0), "peas": (2500, 2375), "lupins": (5000, 6000),
                "beans": (400, 400), "chickpeas": (0, 0), "lentils": (80000, 96000),
                "vetch": (0, 0), "canola": (9000, 11250), "TOTAL": (539900, 1029425)},
        "SA_TOTAL": {"TOTAL": (4068790, 8863172)},
    },
}


def pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def fmt(n: int) -> str:
    return f"{n:,}"


def main():
    rows = []
    problems = []
    for (season, pdf_name, pub), districts in DATA.items():
        path = RAW / "pirsa" / pdf_name
        text = pdf_text(path).replace(" ", " ") if path.exists() else ""
        if not text:
            problems.append(f"{season}: PDF missing or unreadable: {pdf_name}")
        # spot-verify the three district grain totals + SA total appear in the PDF text
        for dist in ("WEP", "LEP", "EEP", "SA_TOTAL"):
            tot = districts[dist]["TOTAL"][1]
            if text and fmt(tot) not in text:
                problems.append(f"{season} {dist}: total {fmt(tot)} not found in {pdf_name}")
        for dist, crops in districts.items():
            for crop, (area, prod) in crops.items():
                if crop == "TOTAL":
                    continue
                rows.append(
                    {"season": season, "district": dist, "crop": crop,
                     "area_ha": area, "production_t": prod,
                     "source_pdf": pdf_name, "published": pub,
                     "provenance": "PIRSA Crop and Pasture Report, Table 1 (transcribed + spot-verified)"}
                )
            if dist != "SA_TOTAL":
                a, p = districts[dist]["TOTAL"]
                rows.append(
                    {"season": season, "district": dist, "crop": "TOTAL",
                     "area_ha": a, "production_t": p, "source_pdf": pdf_name,
                     "published": pub, "provenance": "PIRSA Table 1 district total"}
                )
    df = pl.DataFrame(rows)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.write_parquet(PROCESSED / "production_districts.parquet")
    print(f"rows: {df.height}; seasons: {df['season'].n_unique()}")
    print(df.filter(pl.col("crop") == "TOTAL").pivot(values="production_t", index="season", on="district"))
    if problems:
        print("\nVERIFICATION PROBLEMS:")
        for p in problems:
            print("  ", p)
        sys.exit(1)
    print("\nall spot-checks passed (district totals found verbatim in PDF text)")


if __name__ == "__main__":
    main()
