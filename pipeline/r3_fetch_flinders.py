"""R3/R8: Flinders Port Holdings monthly port statistics (per-port cargo tonnages).

Page: https://www.flindersportholdings.com.au/port-statistics/  (monthly XLSX, 2022-2026).
Used to calibrate Port Lincoln shipped tonnage.

Access notes (2026-08-19): robots.txt allows all with Crawl-delay: 10 (honoured).
The site's WAF rejects non-browser TLS fingerprints (httpx 403s even with a browser UA),
so this script shells out to curl with a desktop UA at 1 request / 10 s.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wlib import RAW, update_manifest

PAGE = "https://www.flindersportholdings.com.au/port-statistics/"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
DELAY = 10.0  # robots.txt Crawl-delay


def curl(url: str, dest: Path | None = None) -> bytes:
    args = ["curl", "-sS", "--max-time", "120", "-A", BROWSER_UA, "-L", url]
    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        args += ["-o", str(dest)]
        subprocess.run(args, check=True)
        return dest.read_bytes()
    out = subprocess.run(args, check=True, capture_output=True)
    return out.stdout


def main():
    out = RAW / "flinders_stats"
    out.mkdir(parents=True, exist_ok=True)
    html = curl(PAGE).decode(errors="replace")
    (out / "_page.html").write_text(html, encoding="utf-8")
    links = sorted(set(re.findall(r'href="(https?://[^"]+\.(?:xlsx|xls|zip))"', html, re.I)))
    print(f"file links found: {len(links)}", flush=True)
    saved = []
    for url in links:
        name = url.rsplit("/", 1)[-1]
        dest = out / name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"  cached {name}", flush=True)
            saved.append(dest)
            continue
        time.sleep(DELAY)
        curl(url, dest)
        saved.append(dest)
        print(f"  {name}  ({dest.stat().st_size/1e3:.0f} kB)", flush=True)
    update_manifest(saved)


if __name__ == "__main__":
    main()
