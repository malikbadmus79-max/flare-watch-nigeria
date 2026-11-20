"""Independent recompute of key Phase 2 figures (plan section 6, item 3).

Deliberately does NOT import any flare_watch module and does NOT read any
pipeline output in data/processed. Inputs:
- data/interim/ng_sites_cache.parquet: verbatim Nigeria rows of the raw site
  file. Its stored source hash is checked here against a fresh SHA-256 of the
  raw .xlsx before use.
- data/raw/boundaries/geoBoundaries-NGA-ADM1.geojson
- data/raw/worldpop/nga_pop_2025_CN_100m_R2025A_v1.tif

Method differences from the pipeline:
- Volumes, flags and shares: DuckDB SQL on the raw rows.
- State: shapely point-in-polygon (STRtree), not geopandas.sjoin.
- Buffers: pyproj Transformer + shapely, not geopandas.to_crs.
- Raster sum: rasterio.features.geometry_mask on a window, not rasterio.mask.

Output: data/interim/recompute_results.csv (metric, key, value)

Run: .venv/Scripts/python validation/recompute.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
import shapely
from shapely import STRtree
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW_XLSX = ROOT / "data" / "raw" / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"
CACHE = ROOT / "data" / "interim" / "ng_sites_cache.parquet"
CACHE_META = ROOT / "data" / "interim" / "ng_sites_cache.json"
ADM1 = ROOT / "data" / "raw" / "boundaries" / "geoBoundaries-NGA-ADM1.geojson"
POP = ROOT / "data" / "raw" / "worldpop" / "nga_pop_2025_CN_100m_R2025A_v1.tif"
OUT = ROOT / "data" / "interim" / "recompute_results.csv"


def check_cache() -> None:
    h = hashlib.sha256(RAW_XLSX.read_bytes()).hexdigest()
    meta = json.loads(CACHE_META.read_text(encoding="utf-8"))
    if meta["source_sha256"] != h:
        raise SystemExit("Cache was built from a different raw file; rebuild it first.")


def sql_metrics(con) -> tuple[list[tuple], pd.DataFrame]:
    con.execute(f"CREATE VIEW r AS SELECT * FROM read_parquet('{CACHE.as_posix()}')")
    out: list[tuple] = []
    for y, v in con.execute("SELECT Year, SUM(BCM) FROM r GROUP BY Year ORDER BY Year").fetchall():
        out.append(("national_bcm", int(y), float(v)))
    sites = con.execute("""
        SELECT id, MIN(lat) AS lat, MIN(lon) AS lon, MIN(Location) AS location,
               SUM(CASE WHEN BCM > 0 THEN 1 ELSE 0 END) AS active_years,
               MAX(CASE WHEN Year = 2025 AND BCM > 0 THEN 1 ELSE 0 END) AS active_2025
        FROM r GROUP BY id ORDER BY id""").df()
    for k in (10, 12, 14):
        out.append(("persistent_count", k, int((sites["active_years"] >= k).sum())))
    out.append(("active_2025_count", "", int(sites["active_2025"].sum())))
    share = con.execute("""
        WITH y AS (SELECT id, BCM FROM r WHERE Year = 2025),
             t AS (SELECT id, BCM FROM y ORDER BY BCM DESC, id ASC LIMIT 10)
        SELECT (SELECT SUM(BCM) FROM t) / (SELECT SUM(BCM) FROM y)""").fetchone()[0]
    out.append(("top10_site_share_2025", "", float(share)))
    out.append(("sites", "", int(len(sites))))
    return out, sites


def assign_state(sites: pd.DataFrame) -> pd.Series:
    gj = json.loads(ADM1.read_text(encoding="utf-8"))
    polys = [shape(f["geometry"]) for f in gj["features"]]
    names = [f["properties"]["shapeName"] for f in gj["features"]]
    tree = STRtree(polys)
    states = []
    for _, s in sites.iterrows():
        if str(s["location"]).strip().upper() == "OFFSHORE":
            states.append("Offshore")
            continue
        p = Point(s["lon"], s["lat"])
        hits = sorted(names[i] for i in tree.query(p, predicate="intersects"))
        states.append(hits[0] if hits else "Unassigned")
    return pd.Series(states, index=sites.index)


def raster_sum(src, geom) -> float:
    left, bottom, right, top = geom.bounds
    rb = src.bounds
    left, bottom = max(left, rb.left), max(bottom, rb.bottom)
    right, top = min(right, rb.right), min(top, rb.top)
    if left >= right or bottom >= top:
        return 0.0
    # Pad to whole pixels outward (floor offsets, ceil far edge, +1) so no edge pixel is cut off.
    w = from_bounds(left, bottom, right, top, transform=src.transform)
    c0, r0 = int(np.floor(w.col_off)) - 1, int(np.floor(w.row_off)) - 1
    c1, r1 = int(np.ceil(w.col_off + w.width)) + 1, int(np.ceil(w.row_off + w.height)) + 1
    win = rasterio.windows.Window(c0, r0, c1 - c0, r1 - r0).intersection(
        rasterio.windows.Window(0, 0, src.width, src.height))
    a = src.read(1, window=win).astype("float64")
    inside = geometry_mask([geom], out_shape=a.shape, transform=src.window_transform(win),
                           invert=True, all_touched=False)
    a[~np.isfinite(a) | (a < 0) | (a == src.nodata)] = 0.0
    return float(a[inside].sum())


def population(sites: pd.DataFrame) -> list[tuple]:
    fwd = Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)
    inv = Transformer.from_crs("EPSG:32632", "EPSG:4326", always_xy=True)

    def reproject(geom, tr):
        return shapely.transform(geom, lambda xy: np.column_stack(tr.transform(xy[:, 0], xy[:, 1])))

    pts = [reproject(Point(lon, lat), fwd) for lon, lat in zip(sites["lon"], sites["lat"])]
    out = []
    with rasterio.open(POP) as src:
        for km in (2, 5):
            bufs = [p.buffer(km * 1000.0, quad_segs=32) for p in pts]
            for gname, col in (("active_2025", "active_2025"), ("persistent", "persistent")):
                sub = sites[sites[col].astype(bool)]
                scopes = [("All", sub.index)] + [(st, sub.index[sub["state"] == st]) for st in sorted(sub["state"].unique())]
                for scope, idx in scopes:
                    u = reproject(unary_union([bufs[i] for i in idx]), inv)
                    out.append(("pop_union", f"{gname}|{scope}|{km}", raster_sum(src, u)))
    return out


def main() -> None:
    check_cache()
    con = duckdb.connect()
    rows, sites = sql_metrics(con)
    sites["persistent"] = sites["active_years"] >= 12
    sites["state"] = assign_state(sites)
    for st, n in sites["state"].value_counts().sort_index().items():
        rows.append(("sites_by_state", st, int(n)))
    rows += population(sites)
    pd.DataFrame(rows, columns=["metric", "key", "value"]).to_csv(OUT, index=False, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
