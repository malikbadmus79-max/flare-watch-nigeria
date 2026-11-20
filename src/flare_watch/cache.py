"""Parquet cache of the Nigeria rows of the raw World Bank site file.

The cache stores the rows verbatim (no cleaning). A sidecar JSON records the
SHA-256 of the source .xlsx; the cache is rebuilt only if that hash changes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

SITE_FILE = RAW / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"
SITE_SHEET = "Dashboard_file"
COUNTRY = "Nigeria"
CACHE = INTERIM / "ng_sites_cache.parquet"
CACHE_META = INTERIM / "ng_sites_cache.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_is_current(source_hash: str | None = None) -> bool:
    if not (CACHE.exists() and CACHE_META.exists()):
        return False
    meta = json.loads(CACHE_META.read_text(encoding="utf-8"))
    return meta.get("source_sha256") == (source_hash or sha256(SITE_FILE))


def load_ng_sites() -> pd.DataFrame:
    """Nigeria rows of the raw site file, via the cache (rebuilt if the source hash changed)."""
    h = sha256(SITE_FILE)
    if not cache_is_current(h):
        df = pd.read_excel(SITE_FILE, sheet_name=SITE_SHEET)
        ng = df[df["Country"] == COUNTRY].reset_index(drop=True)
        ng.to_parquet(CACHE, index=False)
        CACHE_META.write_text(json.dumps({
            "source_file": SITE_FILE.name, "source_sha256": h, "sheet": SITE_SHEET,
            "filter": f"Country == {COUNTRY!r}", "rows": int(len(ng)),
        }, indent=2), encoding="utf-8")
    return pd.read_parquet(CACHE)
