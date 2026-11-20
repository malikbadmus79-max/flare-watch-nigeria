"""Phase 2a: assign state/LGA and count nearby residents.

Plan v1.0, Q8:
- State and LGA by point-in-polygon on geoBoundaries ADM1/ADM2.
- Location == OFFSHORE -> state and lga "Offshore".
- Onshore points outside every polygon -> nearest polygon within 2 km,
  else "Unassigned".
- 2 km and 5 km buffers built in EPSG:32632 (UTM 32N), then reprojected to
  the raster CRS. WorldPop 2025 summed inside each buffer (pixel counted if
  its centre lies inside the buffer; nodata treated as 0). Union-of-buffer
  totals count each person once.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

ADM1_FILE = RAW / "boundaries" / "geoBoundaries-NGA-ADM1.geojson"
ADM2_FILE = RAW / "boundaries" / "geoBoundaries-NGA-ADM2.geojson"
POP_FILE = RAW / "worldpop" / "nga_pop_2025_CN_100m_R2025A_v1.tif"

METRIC_CRS = "EPSG:32632"
NEAREST_MAX_M = 2000.0
BUFFERS_KM = (2, 5)
BUFFER_RESOLUTION = 32  # segments per quarter circle
OFFSHORE = "Offshore"
UNASSIGNED = "Unassigned"


def load_boundaries() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    adm1 = gpd.read_file(ADM1_FILE)[["shapeName", "shapeISO", "shapeID", "geometry"]]
    adm2 = gpd.read_file(ADM2_FILE)[["shapeName", "shapeID", "geometry"]]
    return adm1.sort_values("shapeID").reset_index(drop=True), adm2.sort_values("shapeID").reset_index(drop=True)


def _assign(points: gpd.GeoDataFrame, polys: gpd.GeoDataFrame, prefix: str) -> tuple[pd.DataFrame, dict]:
    """Point-in-polygon, then nearest-within-2-km fallback. Returns name/id/method per site."""
    hit = gpd.sjoin(points, polys, how="left", predicate="intersects")
    n_multi = int(hit.index.duplicated().sum())
    hit = hit[~hit.index.duplicated(keep="first")]  # polys pre-sorted by shapeID -> deterministic
    out = pd.DataFrame({f"{prefix}": hit["shapeName"], f"{prefix}_id": hit["shapeID"]}, index=points.index)
    out[f"{prefix}_method"] = np.where(out[f"{prefix}_id"].notna(), "within", None)

    missing = out[f"{prefix}_id"].isna()
    n_near = 0
    if missing.any():
        pm = points[missing].to_crs(METRIC_CRS)
        near = gpd.sjoin_nearest(pm, polys.to_crs(METRIC_CRS), how="left",
                                 max_distance=NEAREST_MAX_M, distance_col="_dist")
        near = near[~near.index.duplicated(keep="first")]
        ok = near["shapeID"].notna()
        idx = near.index[ok]
        out.loc[idx, prefix] = near.loc[idx, "shapeName"]
        out.loc[idx, f"{prefix}_id"] = near.loc[idx, "shapeID"]
        out.loc[idx, f"{prefix}_method"] = "nearest<=2km"
        n_near = int(ok.sum())
    still = out[f"{prefix}_id"].isna()
    out.loc[still, prefix] = UNASSIGNED
    out.loc[still, f"{prefix}_method"] = "unassigned"
    return out, {"points": int(len(points)), "within": int((out[f"{prefix}_method"] == "within").sum()),
                 "nearest_within_2km": n_near, "unassigned": int(still.sum()),
                 "points_on_shared_boundary": n_multi}


def assign_admin(sites: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    adm1, adm2 = load_boundaries()
    pts = gpd.GeoDataFrame(sites[["site_id", "location"]].copy(),
                           geometry=gpd.points_from_xy(sites["lon"], sites["lat"]), crs="EPSG:4326")
    offshore = pts["location"].str.upper().eq("OFFSHORE")
    on = pts[~offshore]

    s1, log1 = _assign(on, adm1, "state")
    s2, log2 = _assign(on, adm2, "lga")
    iso = adm1.set_index("shapeID")["shapeISO"]

    res = pd.DataFrame(index=pts.index)
    res["site_id"] = pts["site_id"]
    res["state"], res["state_id"], res["state_method"] = OFFSHORE, None, "offshore"
    res["lga"], res["lga_id"], res["lga_method"] = OFFSHORE, None, "offshore"
    for col in ["state", "state_id", "state_method"]:
        res.loc[s1.index, col] = s1[col]
    for col in ["lga", "lga_id", "lga_method"]:
        res.loc[s2.index, col] = s2[col]
    res["state_iso"] = res["state_id"].map(iso)

    # QA: does each assigned LGA lie in the assigned state? (LGA parent = ADM1 containing its representative point)
    rep = adm2.copy()
    rep["geometry"] = adm2.representative_point()
    parent = gpd.sjoin(rep, adm1.rename(columns={"shapeName": "parent", "shapeID": "parent_id"})[["parent", "parent_id", "geometry"]],
                       how="left", predicate="intersects")
    parent = parent[~parent.index.duplicated()].set_index("shapeID")["parent_id"]
    both = res["state_id"].notna() & res["lga_id"].notna()
    mismatch = int((res.loc[both, "lga_id"].map(parent) != res.loc[both, "state_id"]).sum())

    # Informational: how many OFFSHORE-labelled sites fall inside a land polygon.
    off_in_poly = int(gpd.sjoin(pts[offshore], adm1, how="inner", predicate="intersects").index.unique().size)

    log = {"offshore_sites": int(offshore.sum()), "onshore_sites": int((~offshore).sum()),
           "state": log1, "lga": log2, "lga_state_mismatch": mismatch,
           "offshore_sites_inside_adm1_polygon": off_in_poly}
    return res.drop(columns=[]).reset_index(drop=True), log


def buffers(sites: pd.DataFrame, km: float, raster_crs) -> gpd.GeoSeries:
    pts = gpd.GeoSeries(gpd.points_from_xy(sites["lon"], sites["lat"]), crs="EPSG:4326", index=sites.index)
    return pts.to_crs(METRIC_CRS).buffer(km * 1000.0, quad_segs=BUFFER_RESOLUTION)


def zonal_sum(src: rasterio.io.DatasetReader, geom) -> float:
    """Sum of raster values inside geom (raster CRS); nodata, NaN and negatives -> 0."""
    if geom is None or geom.is_empty:
        return 0.0
    try:
        arr, _ = rio_mask(src, [mapping(geom)], crop=True, all_touched=False, filled=True, nodata=src.nodata)
    except ValueError:  # geometry does not overlap the raster at all
        return 0.0
    a = arr[0].astype("float64")
    bad = ~np.isfinite(a) | (a < 0)
    if src.nodata is not None:
        bad |= a == src.nodata
    a[bad] = 0.0
    return float(a.sum())


def population(sites: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Per-site pop_2km/pop_5km and union-of-buffer group totals.

    `sites` must have site_id, lat, lon, state, active_2025, persistent.
    """
    per_site = pd.DataFrame({"site_id": sites["site_id"].values})
    groups = []
    with rasterio.open(POP_FILE) as src:
        meta = {"raster": POP_FILE.name, "raster_crs": str(src.crs), "pixel_deg": list(src.res),
                "nodata": src.nodata, "pixel_rule": "pixel centre inside buffer (all_touched=False)",
                "buffer_crs": METRIC_CRS, "buffer_segments_per_quarter": BUFFER_RESOLUTION}
        for km in BUFFERS_KM:
            buf_m = buffers(sites, km, src.crs)
            buf_r = buf_m.to_crs(src.crs)
            per_site[f"pop_{km}km"] = [zonal_sum(src, g) for g in buf_r]
            for gname, gmask in [("active_2025", sites["active_2025"].astype(bool)),
                                 ("persistent", sites["persistent"].astype(bool))]:
                sub = sites[gmask]
                scopes = [("All", sub.index)] + [(st, sub.index[sub["state"] == st]) for st in sorted(sub["state"].unique())]
                for scope, idx in scopes:
                    u = gpd.GeoSeries([unary_union(list(buf_m.loc[idx]))], crs=METRIC_CRS).to_crs(src.crs).iloc[0]
                    groups.append({"group": gname, "state": scope, "buffer_km": km, "n_sites": int(len(idx)),
                                   "pop_union": zonal_sum(src, u),
                                   "pop_sum_of_sites": float(per_site.loc[idx, f"pop_{km}km"].sum())})
    return per_site, pd.DataFrame(groups), meta
