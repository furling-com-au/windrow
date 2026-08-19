"""Shared helpers for the Windrow data pipeline.

Provenance discipline:
- every download lands under data/raw/ and is never edited in place;
- downloads are skipped if the destination already exists (immutable cache);
- polite fetching: >= 2 s between requests to the same host, honest UA.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

UA = "WindrowResearch/0.1 (non-commercial grain supply chain research; polite crawler, >=2s interval)"
HOST_INTERVAL = 2.0  # seconds between requests to the same host

_last_hit: dict[str, float] = {}


def _politeness_wait(host: str, interval: float = HOST_INTERVAL) -> None:
    now = time.monotonic()
    last = _last_hit.get(host)
    if last is not None:
        wait = interval - (now - last)
        if wait > 0:
            time.sleep(wait)
    _last_hit[host] = time.monotonic()


def fetch(
    url: str,
    dest: Path | None = None,
    *,
    timeout: float = 120.0,
    retries: int = 4,
    interval: float = HOST_INTERVAL,
    client: httpx.Client | None = None,
) -> bytes | None:
    """GET url politely. If dest given and exists (non-empty), return None (cached).

    Returns response bytes (also written to dest if given). Raises on final failure,
    except 404 which returns b"" so callers can record the gap.
    """
    if dest is not None and dest.exists() and dest.stat().st_size > 0:
        return None
    own_client = client is None
    if own_client:
        client = httpx.Client(follow_redirects=True, headers={"User-Agent": UA}, timeout=timeout)
    try:
        host = httpx.URL(url).host
        backoff = 5.0
        for attempt in range(retries):
            _politeness_wait(host, interval)
            try:
                r = client.get(url)
            except httpx.HTTPError as e:
                if attempt == retries - 1:
                    raise
                time.sleep(backoff)
                backoff *= 2
                continue
            if r.status_code == 200:
                data = r.content
                if dest is not None:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dest.with_suffix(dest.suffix + ".part")
                    tmp.write_bytes(data)
                    tmp.replace(dest)
                return data
            if r.status_code == 404:
                return b""
            if r.status_code in (429, 503, 502, 500):
                ra = r.headers.get("Retry-After")
                delay = float(ra) if ra and ra.isdigit() else backoff
                time.sleep(min(delay, 120))
                backoff *= 2
                continue
            # other status: give up loudly
            r.raise_for_status()
        raise RuntimeError(f"exhausted retries for {url}")
    finally:
        if own_client:
            client.close()


def cdx_query(url_pattern: str, **params) -> list[list[str]]:
    """Query the Wayback CDX API. Returns rows (first row = header). Cached by caller if needed."""
    q = {
        "url": url_pattern,
        "output": "json",
        **params,
    }
    qs = "&".join(f"{k}={httpx.QueryParams({k: str(v)})[k]}" if False else f"{k}={v}" for k, v in q.items())
    full = f"https://web.archive.org/cdx/search/cdx?{qs}"
    data = fetch(full, timeout=180.0)
    if not data:
        return []
    return json.loads(data)


def wayback_snapshot_url(timestamp: str, original: str) -> str:
    """Raw-content snapshot URL (id_ = no Wayback chrome)."""
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def update_manifest(new_files: list[Path]) -> None:
    """Append sha256 lines for files not yet in data/raw/MANIFEST.sha256 (relative paths)."""
    manifest = RAW / "MANIFEST.sha256"
    existing: set[str] = set()
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split("  ", 1)
            if len(parts) == 2:
                existing.add(parts[1])
    lines = []
    for f in sorted(set(new_files)):
        rel = f.relative_to(RAW).as_posix()
        if rel in existing or not f.exists():
            continue
        h = hashlib.sha256()
        with f.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        lines.append(f"{h.hexdigest()}  {rel}")
    if lines:
        with manifest.open("a", encoding="utf-8", newline="\n") as fh:
            for line in lines:
                fh.write(line + "\n")


def slugify(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")
