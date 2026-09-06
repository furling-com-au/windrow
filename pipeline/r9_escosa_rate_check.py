"""A18: verify HOW ESCOSA's published marginal trucking schedule is applied.

Tier 1 (published fact). No simulation, no fitted parameter, no calibrated knob.
This script reads nothing from the repo except the cached ESCOSA PDF; the four case-study
distances and dollar results below are transcribed from that PDF and re-checked against it
at runtime, so a bad transcription fails loudly instead of quietly.

The schedule (ESCOSA, Inquiry into the South Australian bulk grain export supply chain
costs - Final Report, 29 January 2019, Box 5.2, p. 91), verbatim:

    "Only the marginal freight cost has been used, $0.12 ($/tonne-km) for up to 50
     kilometres and $0.11 ($/tonne-km) for 50 to 250 kilometres."

The rates are quotable on their own. What is NOT stated in prose - and what changes any
derived figure by up to a factor of two - is how they are applied. ESCOSA publishes both
the four road distances it used and the four $/t results it got, so the application rule
is recoverable by arithmetic rather than by assumption. Three candidate rules are tested:

  ONE_WAY_FLAT   rate chosen by the WHOLE distance, applied once to the one-way distance
  ROUND_TRIP     the same, doubled for the empty return leg
  TIERED         cumulative bands: first 50 km at $0.12, the remainder at $0.11

Result: ONE_WAY_FLAT reproduces all four published figures exactly and the other two do
not. Yongala (53.0 km) is the discriminating case - it is the only distance that crosses
the 50 km band edge, and it prices at 53.0 x $0.11, not 50 x $0.12 + 3 x $0.11.

What this establishes: the rate is applied to LOADED ONE-WAY kilometres, with the band
selected by total distance and no cumulative tiering, and the empty return leg is not
added on top.

What this does NOT establish: whether AEGIC's underlying cost line was itself built on a
round-trip cycle. ESCOSA is silent on that (the full report text contains no "return leg",
"backload", "round trip" or "empty run"), and it is worth a factor of two. See A18.

Run:  .venv/Scripts/python.exe pipeline/r9_escosa_rate_check.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PDF = REPO / "data" / "raw" / "reference" / "escosa_grain_supply_chain_2019.pdf"

# The schedule, as published. Bands are (upper_km_inclusive, A$ per tonne-km), 2018-19 A$.
BANDS: list[tuple[float, float]] = [(50.0, 0.12), (250.0, 0.11)]

# ESCOSA Box 5.2, p. 91: the four road distances it used (Google Maps, site -> Gladstone)
# and the four incremental freight costs it published for them.
CASES: list[tuple[str, float, float]] = [
    ("Caltowie", 16.3, 1.96),
    ("Yongala", 53.0, 5.83),
    ("Gulnare", 31.7, 3.80),
    ("Jamestown", 28.5, 3.42),
]


def rate_for(km: float) -> float:
    """The single band rate that applies to a haul of this total length."""
    for upper, rate in BANDS:
        if km <= upper:
            return rate
    raise ValueError(
        f"{km} km is beyond the published schedule's 250 km ceiling; "
        "extrapolating past it is not a citation (see A18)."
    )


def one_way_flat(km: float) -> float:
    return km * rate_for(km)


def round_trip(km: float) -> float:
    return 2.0 * km * rate_for(km)


def tiered(km: float) -> float:
    if km > 250.0:
        raise ValueError("beyond the published 250 km ceiling")
    return min(km, 50.0) * 0.12 + max(0.0, km - 50.0) * 0.11


RULES = {
    "ONE_WAY_FLAT": one_way_flat,
    "ROUND_TRIP": round_trip,
    "TIERED": tiered,
}


def pdf_text() -> str:
    """Extract the cached PDF's text, so the transcription above is checked, not trusted."""
    if not PDF.exists():
        print(f"MISSING: {PDF}", file=sys.stderr)
        print("The cached reference PDF is required; see data/SOURCES.md ->", file=sys.stderr)
        print("escosa-marginal-trucking-rate-2019.", file=sys.stderr)
        sys.exit(2)
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", str(PDF), "-"],
            capture_output=True,
            check=True,
        )
    except FileNotFoundError:
        print("pdftotext not on PATH; cannot verify the transcription.", file=sys.stderr)
        sys.exit(2)
    return out.stdout.decode("utf-8", errors="replace")


def check_transcription(text: str) -> bool:
    """Confirm the quoted rates and every case-study number are actually in the PDF."""
    flat = re.sub(r"\s+", " ", text)
    ok = True

    quote = (
        "Only the marginal freight cost has been used, $0.12 ($/tonne-km) for up to 50 "
        "kilometres and $0.11 ($/tonne-km) for 50 to 250 kilometres."
    )
    if quote in flat:
        print("  quote        OK  schedule sentence found verbatim in the cached PDF")
    else:
        ok = False
        print("  quote      FAIL  schedule sentence NOT found - transcription is stale")

    for name, km, dollars in CASES:
        has_km = f"{km:g} kilometres" in flat or f"{km:.1f} kilometres" in flat
        has_dollars = f"${dollars:.2f} per tonne" in flat
        mark = "OK  " if (has_km and has_dollars) else "FAIL"
        if not (has_km and has_dollars):
            ok = False
        print(
            f"  {name:<10s} {mark}  {km:.1f} km in PDF: {has_km}; "
            f"${dollars:.2f}/t in PDF: {has_dollars}"
        )
    return ok


def main() -> int:
    print("ESCOSA 2019 marginal trucking schedule - application rule check")
    print("PDF:", PDF)
    print()

    print("1. Transcription check (is what this script asserts actually in the document?)")
    transcription_ok = check_transcription(pdf_text())
    print()

    print("2. Which application rule reproduces ESCOSA's own published $/t results?")
    header = f"  {'case':<10s} {'km':>6s} {'published':>10s} " + " ".join(
        f"{name:>13s}" for name in RULES
    )
    print(header)
    matches = {name: 0 for name in RULES}
    for name, km, published in CASES:
        cells = []
        for rule_name, fn in RULES.items():
            got = fn(km)
            hit = abs(round(got, 2) - published) < 0.005
            matches[rule_name] += int(hit)
            cells.append(f"{got:>10.2f} {'=' if hit else 'x'}")
        print(f"  {name:<10s} {km:>6.1f} {published:>10.2f} " + " ".join(cells))
    print()
    for rule_name in RULES:
        verdict = "REPRODUCES ALL 4" if matches[rule_name] == len(CASES) else "ruled out"
        print(f"  {rule_name:<13s} {matches[rule_name]}/{len(CASES)}  {verdict}")
    print()

    print("3. Discriminating case: Yongala, 53.0 km, the only distance crossing 50 km")
    print(f"  flat band (whole distance at $0.11): 53.0 x 0.11 = ${one_way_flat(53.0):.2f}")
    print(f"  cumulative tier (50 @ 0.12 + 3 @ 0.11): ${tiered(53.0):.2f}")
    print("  ESCOSA published:                       $5.83  -> the bands are FLAT, not tiered")
    print()

    print("4. What the marginal rate leaves out, at EP's ~144 km average site->port haul")
    print(f"  ESCOSA marginal    144 x $0.11                = ${one_way_flat(144.0):>6.2f}/t")
    print(f"  ACH 2026 full      $16.50 + 134 x $0.10       = ${16.50 + 134 * 0.10:>6.2f}/t")
    print("  SAGIT 2026 budget  cereal grains, delivered   = $ 35.00/t")
    print("  The gap is the fixed and time cost the marginal rate deliberately excludes.")
    print("  ACH and SAGIT are 2026 nominal; the ESCOSA figure is 2018-19 A$. Not indexed.")
    print()

    all_ok = transcription_ok and matches["ONE_WAY_FLAT"] == len(CASES)
    print("VERDICT:", "PASS" if all_ok else "FAIL")
    print(
        "Rate is applied to LOADED ONE-WAY km, band chosen by total distance, no tiering,"
        "\nempty return NOT added. Whether AEGIC's cost line embeds a return leg is"
        "\nunresolved and unresolvable from this document - see A18."
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
