# Data Sources Register — Windrow

Every dataset used by Windrow gets an entry here. Raw downloads are cached immutably under
`data/raw/` (git-ignored; integrity manifest in `data/raw/MANIFEST.sha256`). Nothing in
`data/raw/` is ever edited in place.

Entry format:

```
## <source-id>
- **What**:
- **URL**:
- **Retrieved**: YYYY-MM-DD
- **Licence**:
- **Update cadence**:
- **Format**:
- **Restrictions / notes**:
- **Local cache**: data/raw/<path>
```

---

## viterra-domain-migration (context note, not a dataset)
- **What**: The former Viterra Australia website has been migrated to the Bunge domain.
  `https://www.viterra.com.au/media/Receivals-reports` returns 302 → `https://www.bunge.com.au/Media/News`.
  Historical Viterra URLs must be resolved via the live Bunge site or the Wayback Machine.
- **Checked**: 2026-08-19
- **Notes**: `viterra.com.au/robots.txt` = allow all. Bunge acquisition of Viterra completed 2025-07-02.
