"""Phase 2b: validation (plan section 6) -> data/interim/phase2b_*.csv and docs/phase2b_validation.md.

Run from the project root, after phase2a.py:
    .venv/Scripts/python src/flare_watch/phase2b.py
It runs validation/recompute.py (independent code) as a subprocess first.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flare_watch import geo, params  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
DOC = ROOT / "docs" / "phase2b_validation.md"

TOL_BCM, TOL_SHARE, TOL_POP = 0.001, 1e-9, 1.0
DIST_FLAG_KM = 10.0


def load():
    fact = pd.read_csv(PROCESSED / "fact_site_year.csv")
    site = pd.read_csv(PROCESSED / "dim_site.csv", keep_default_na=False, na_values=[""])
    year = pd.read_csv(PROCESSED / "dim_year.csv")
    groups = pd.read_csv(PROCESSED / "population_groups.csv", keep_default_na=False)
    return fact, site, year, groups


# ---------- a. satellite vs official ----------
def satellite_vs_official(fact, year) -> pd.DataFrame:
    sat = fact.groupby("year")["bcm"].sum().rename("satellite_bcm")
    t = year.set_index("year")[["official_bcm", "official_source"]].join(sat)
    t = t[t["official_bcm"].notna()].reset_index()
    t["difference_bcm"] = t["satellite_bcm"] - t["official_bcm"]
    t["ratio_satellite_to_official"] = t["satellite_bcm"] / t["official_bcm"]
    return t[["year", "satellite_bcm", "official_bcm", "difference_bcm", "ratio_satellite_to_official", "official_source"]]


# ---------- b. recompute comparison ----------
def pipeline_values(fact, site, groups) -> pd.DataFrame:
    rows = [("national_bcm", str(y), v) for y, v in fact.groupby("year")["bcm"].sum().items()]
    rows += [("persistent_count", "10", site["persistent_10"].sum()), ("persistent_count", "12", site["persistent"].sum()),
             ("persistent_count", "14", site["persistent_14"].sum()), ("active_2025_count", "", site["active_2025"].sum()),
             ("sites", "", len(site))]
    y25 = fact[fact["year"] == 2025].sort_values(["bcm", "site_id"], ascending=[False, True])
    rows.append(("top10_site_share_2025", "", y25["bcm"].head(10).sum() / y25["bcm"].sum()))
    rows += [("sites_by_state", st, n) for st, n in site["state"].value_counts().items()]
    rows += [("pop_union", f"{r.group}|{r.state}|{r.buffer_km}", r.pop_union) for r in groups.itertuples()]
    return pd.DataFrame(rows, columns=["metric", "key", "pipeline"])


def compare(fact, site, groups) -> pd.DataFrame:
    rec = pd.read_csv(INTERIM / "recompute_results.csv", keep_default_na=False, dtype={"key": str})
    rec["key"] = rec["key"].str.replace(r"\.0$", "", regex=True)
    pipe = pipeline_values(fact, site, groups)
    m = pipe.merge(rec.rename(columns={"value": "recompute"}), on=["metric", "key"], how="outer", indicator=True)
    m["pipeline"] = m["pipeline"].astype(float)
    m["recompute"] = m["recompute"].astype(float)
    tol = m["metric"].map({"national_bcm": TOL_BCM, "top10_site_share_2025": TOL_SHARE, "pop_union": TOL_POP}).fillna(0.0)
    m["abs_diff"] = (m["pipeline"] - m["recompute"]).abs()
    m["tolerance"] = tol
    m["pass"] = (m["_merge"] == "both") & (m["abs_diff"] <= tol)
    return m.drop(columns="_merge").sort_values(["metric", "key"]).reset_index(drop=True)


# ---------- c. GEM cross-check ----------
def wb_key(name: str) -> str:
    s = re.sub(r"\([^)]*\)", " ", str(name))
    return re.sub(r"\s+", " ", s).strip().casefold()


def gem_key(unit_name: str) -> str:
    return re.split(r" (?:Oil|Gas)\b", str(unit_name), maxsplit=1)[0].strip().casefold()


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dlat, dlon = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlon / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def gem_crosscheck(site) -> pd.DataFrame:
    gem = pd.read_csv(INTERIM / "gem_ng_fields.csv")
    gem["key"] = gem["Unit Name"].map(gem_key)
    top = site.sort_values(["recent_volume_bcm", "site_id"], ascending=[False, True]).head(20).reset_index(drop=True)
    out = []
    for rank, s in enumerate(top.itertuples(), start=1):
        k = wb_key(s.field) if s.field != "Unattributed field" else None
        cand = gem[gem["key"] == k] if k else gem.iloc[0:0]
        rec = {"rank_recent_volume": rank, "site_id": s.site_id, "field_as_recorded": s.field,
               "operator_as_recorded": s.operator_clean, "location_wb": s.location, "match_key": k or "",
               "gem_candidates": int(len(cand))}
        if len(cand):
            c = cand.copy()
            c["dist_km"] = haversine_km(s.lat, s.lon, c["Latitude"], c["Longitude"])
            c = c.sort_values(["dist_km", "Unit ID"], na_position="last")
            b = c.iloc[0]
            rec.update({"gem_unit_id": b["Unit ID"], "gem_unit_name": b["Unit Name"], "gem_status": b["Status"],
                        "gem_onshore_offshore": b["Onshore/Offshore"], "gem_location_accuracy": b["Location accuracy"],
                        "distance_km": None if pd.isna(b["dist_km"]) else round(float(b["dist_km"]), 2)})
        out.append(rec)
    df = pd.DataFrame(out)
    for c in ["gem_unit_id", "gem_unit_name", "gem_status", "gem_onshore_offshore", "gem_location_accuracy", "distance_km"]:
        if c not in df:
            df[c] = None
    df["flag_no_match"] = df["gem_candidates"] == 0
    df["flag_status_not_operating"] = df["gem_status"].notna() & (df["gem_status"] != "operating")
    df["flag_distance_gt_10km"] = df["distance_km"].notna() & (df["distance_km"] > DIST_FLAG_KM)
    df["flag_no_gem_coordinates"] = (df["gem_candidates"] > 0) & df["distance_km"].isna()
    # GEM values may be e.g. "Offshore", "Onshore", "Onshore and Offshore"; flag only if the WB value is absent.
    wbl = df["location_wb"].str.casefold()
    gml = df["gem_onshore_offshore"].astype("string").str.casefold().fillna("")
    df["flag_onshore_offshore_differs"] = [bool(g) and (w not in g) for w, g in zip(wbl, gml)]
    return df


# ---------- d. flags ----------
def offshore_in_polygon(site) -> pd.DataFrame:
    adm1, _ = geo.load_boundaries()
    off = site[site["location"].str.upper() == "OFFSHORE"]
    pts = gpd.GeoDataFrame(off, geometry=gpd.points_from_xy(off["lon"], off["lat"]), crs="EPSG:4326")
    j = gpd.sjoin(pts, adm1[["shapeName", "geometry"]], how="inner", predicate="intersects")
    j = j[~j.index.duplicated()]
    return (j.rename(columns={"shapeName": "adm1_polygon"})
            [["site_id", "lat", "lon", "adm1_polygon", "operator_clean", "field", "active_years", "state"]]
            .sort_values("site_id").reset_index(drop=True))


def kaduna(site, fact) -> dict:
    s = site[site["site_id"] == "s_38320"].iloc[0]
    yrs = fact[(fact["site_id"] == "s_38320") & (fact["bcm"] > 0)]["year"].tolist()
    same = site[(site["field"] == s.field) & (site["site_id"] != s.site_id)]
    others = "; ".join(f"{o.site_id} ({o.state}, {o.lat:.4f}, {o.lon:.4f}; "
                       f"{haversine_km(s.lat, s.lon, o.lat, o.lon):.0f} km from s_38320)" for o in same.itertuples())
    gem = pd.read_csv(INTERIM / "gem_ng_fields.csv")
    gem_hit = gem[gem["Unit Name"].map(gem_key) == wb_key(s.field)]
    return {"site_id": s.site_id, "lat": s.lat, "lon": s.lon, "state": s.state, "lga": s.lga,
            "operator_as_recorded": s.operator_clean, "field_as_recorded": s.field, "field_type": s.field_type,
            "location": s.location, "years_active": yrs,
            "other_sites_with_same_field": others or "none",
            "gem_match_for_field_name": "none" if gem_hit.empty else "; ".join(gem_hit["Unit Name"])}


# ---------- e. sanity ----------
def sanity_2025(fact) -> pd.DataFrame:
    bcm = fact.loc[fact["year"] == 2025, "bcm"].sum()
    mscf = bcm * params.BCM_TO_MSCF
    mmbtu = mscf * 1000 * params.HHV_BTU_PER_SCF / 1e6
    mmbtu_alt = bcm * 1e9 * params.M3_TO_FT3 * params.HHV_BTU_PER_SCF / 1e6  # via m3 -> ft3
    rows = [
        ("national_bcm_2025", bcm, "bcm", "sum of fact_site_year"),
        ("mscf_2025", mscf, "Mscf", "bcm x 35,314,667"),
        ("co2e_mt_2025", bcm * params.CO2E_MT_PER_BCM, "MtCO2e", f"bcm x {params.CO2E_MT_PER_BCM} ({params.CO2E_LABEL})"),
        ("energy_mmbtu_2025", mmbtu, "MMBtu", "Mscf x 1,000 x 1,020 / 1e6"),
        ("energy_mmbtu_2025_alt_route", mmbtu_alt, "MMBtu", "bcm x 1e9 x 35.3146667 x 1,020 / 1e6 (cross-check)"),
        ("gas_value_low_usd_2025", mmbtu * params.PRICE_LOW, "USD", f"MMBtu x {params.PRICE_LOW}"),
        ("gas_value_central_usd_2025", mmbtu * params.PRICE_CENTRAL, "USD", f"MMBtu x {params.PRICE_CENTRAL}"),
        ("gas_value_high_usd_2025", mmbtu * params.PRICE_HIGH, "USD", f"MMBtu x {params.PRICE_HIGH}"),
        ("implied_flare_fee_low_usd_2025", mscf * params.FEE_LOW, "USD", f"Mscf x {params.FEE_LOW}"),
        ("implied_flare_fee_high_usd_2025", mscf * params.FEE_HIGH, "USD", f"Mscf x {params.FEE_HIGH}"),
    ]
    return pd.DataFrame(rows, columns=["check", "value", "unit", "formula"])


# ---------- doc ----------
def md_table(df: pd.DataFrame, floatfmt: dict | None = None) -> str:
    floatfmt = floatfmt or {}
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float) and c in floatfmt:
                cells.append(format(v, floatfmt[c]))
            elif v is None or (isinstance(v, float) and np.isnan(v)):
                cells.append("")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_doc(svo, cmp_, gem, offp, kad, san, off_all, regs_quotes) -> None:
    n_pass, n_all = int(cmp_["pass"].sum()), len(cmp_)
    summ = (cmp_.assign(group=cmp_["metric"]).groupby("group")
            .agg(items=("pass", "size"), passed=("pass", "sum"), max_abs_diff=("abs_diff", "max")).reset_index())
    flag_cols = [c for c in gem.columns if c.startswith("flag_")]
    gem_counts = {c: int(gem[c].sum()) for c in flag_cols}
    gem_show = gem[["rank_recent_volume", "site_id", "field_as_recorded", "operator_as_recorded", "location_wb",
                    "gem_unit_name", "gem_status", "gem_onshore_offshore", "distance_km"] + flag_cols].copy()
    for c in flag_cols:
        gem_show[c] = gem_show[c].map({True: "yes", False: ""})
    unused = off_all[~off_all["used"]]
    unused_summary = (unused.groupby(["original_source", "page", "unit"])["year"]
                      .agg(lambda s: f"{s.min()}–{s.max()}").reset_index().rename(columns={"year": "years"}))
    unused_summary["reason not used"] = unused.groupby(["original_source", "page", "unit"])["note"].first().values

    text = f"""# Phase 2b validation

Date: 2026-11-20. Plan: [analysis_plan.md](analysis_plan.md), frozen v1.0. The plan hash was checked against [plan_freeze.md](plan_freeze.md) before this phase and matched. Amendment in force: A1.

Generated by `src/flare_watch/phase2b.py`. Independent recompute: `validation/recompute.py`. Machine-readable outputs: `data/interim/phase2b_*.csv`.

This document records checks. It does not interpret or explain them. Satellite figures are **estimates** (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).

## Assumptions verified or set in this phase

### Flare fee rates (Amendment A2: formerly "penalty")

Source: `docs/FLARE-GAS-PREVENTION-OF-WASTE-AND-POLLUTION-REGULATIONS-2018.pdf`. This is a Templars law-firm newsletter summarising the Regulations; it is **not the official gazette**.

{regs_quotes}

**Status:** both rates match the plan (US$0.50 and US$2.00 per Mscf). They are set as "verified (law-firm copy)" in `param_assumptions.csv`. Results always label them "{params.FEE_LABEL}" (Amendment A2).

**Check against a KPMG copy of the Regulations: not done.** The file supplied as the KPMG copy (`Flare-Gas-Prevention-of-Waste-and-Pollution-Regulations-2018.pdf`) is not in `Downloads`. The only file there with that name (Windows ignores case in filenames) is byte-identical to the Templars newsletter: same SHA-256, `ca2c8295…`, and "www.templars-law.com" on PDF p.1. The status therefore stays "verified (law-firm copy)". The KPMG copy also has the same name as the Templars file, apart from case, so it must be stored in a separate folder (e.g. `data/raw/docs/kpmg/`) or the registered Templars file would be overwritten.

### Gas prices

Prices are for 2025 and are applied to all years. Results are labelled "{params.PRICE_LABEL}" and described as "{params.VALUE_LABEL}".

| Case | US$/MMBtu | Source |
|---|---:|---|
| Low | {params.PRICE_LOW} | NMDPRA domestic base price effective 1 Apr 2025 (TheCable, accessed 2026-11-20) |
| Central | {params.PRICE_CENTRAL} | US Henry Hub 2025, as used in the World Bank Tracker (PDF p.19 fn xx) |
| High | {params.PRICE_HIGH} | The lower of the Tracker's two conflicting TTF/Asia LNG 2025 figures (PDF p.8 fn iv; p.19 fn xx); chosen to avoid resolving the inconsistency |

### Official volumes (`data/interim/official_volumes.csv`)

Conversion: 1 MMscf = {params.MMSCF_TO_M3:,} m3, and 1 billion scf = 1,000 MMscf.

Used (they fill `dim_year.official_bcm`):

{md_table(off_all[off_all['used']][['year', 'value', 'unit', 'bcm', 'label', 'page']], {'bcm': '.4f'})}

The SoGF 2021–2024 values total 817,434 MMscf, which matches the total stated in the same table.

Stated in SoGF but **not used**:

{md_table(unused_summary)}

## a. Satellite vs official national volumes

{md_table(svo, {'satellite_bcm': '.3f', 'official_bcm': '.3f', 'difference_bcm': '+.3f', 'ratio_satellite_to_official': '.3f'})}

- `difference_bcm` = satellite − official.
- `ratio` = satellite ÷ official.
- The 2025 official figure is the "NUPRC figure as reported in the press" (Amendment A1).
- Description only:
  - The satellite estimate is above the official figure in {int((svo['difference_bcm'] > 0).sum())} of {len(svo)} years and below it in {int((svo['difference_bcm'] < 0).sum())}.
  - The ratio ranges from {svo['ratio_satellite_to_official'].min():.3f} to {svo['ratio_satellite_to_official'].max():.3f}.
  - No explanation of the gap is offered (plan section 7).

## b. Independent recompute

`validation/recompute.py` does not import any project module and does not read the pipeline outputs. It uses:
- DuckDB SQL on the raw Nigeria rows. These come from the parquet cache, whose source hash it re-checks against the raw .xlsx.
- shapely point-in-polygon for state assignment.
- pyproj and shapely to build the buffers.
- `rasterio.features.geometry_mask` for the raster sums.

Tolerances: volumes 0.001 bcm; counts exact; top-10 share 1e-9; population within 1 person.

**Result: {n_pass} of {n_all} items pass{' — PASS' if n_pass == n_all else ' — FAIL'}.**

{md_table(summ, {'max_abs_diff': '.3g'})}

Full item list: `data/interim/phase2b_recompute_comparison.csv`.

## c. GEM cross-check: top 20 sites by recent volume

- Sites are ordered by recent volume (mean bcm 2023–2025), with ties broken by site_id. This order is used only to select sites for the check; it is not a finding.
- Name rule (logged here as a plan Q7 rule):
  - World Bank field name: bracketed qualifiers removed, spaces collapsed, case ignored.
  - GEM unit name: cut before " Oil" or " Gas", case ignored.
  - Exact equality only. Where several GEM units match, the nearest one with coordinates is used.
- Distances are great-circle distances from the World Bank site to the GEM field point.
- Mismatches are listed, not corrected. GEM changes no World Bank value.

Flag counts (top 20):
{chr(10).join(f'- `{k}`: {v}' for k, v in gem_counts.items())}

{md_table(gem_show)}

The {DIST_FLAG_KM:.0f} km distance flag is a screening threshold for this check only. A GEM field point is a single point for a whole field, so distance alone does not show an error.

## d. Data flags, kept as recorded

### OFFSHORE-labelled sites inside a state polygon ({len(offp)})

These sites keep `state = "Offshore"` under the plan. The polygon they fall in is shown for information.

{md_table(offp, {'lat': '.5f', 'lon': '.5f'})}

### Kaduna site

| Item | Value |
|---|---|
{chr(10).join(f'| {k} | {v} |' for k, v in kad.items())}

It is kept as recorded.

## Known data issues

These issues are **kept as recorded**. No value is changed, dropped or reassigned. They are listed so that dashboard users can see them.

| No. | Site(s) | Issue (facts only) | Handling |
|---|---|---|---|
| K1 | {kad['site_id']} | The only onshore site outside the Niger Delta states: {kad['state']} / {kad['lga']} ({kad['lat']:.4f}, {kad['lon']:.4f}). Recorded field "{kad['field_as_recorded']}", operator as recorded "{kad['operator_as_recorded']}", field type {kad['field_type']}. Active only in {', '.join(str(y) for y in kad['years_active'])}. Other site(s) with the same field name: {kad['other_sites_with_same_field']}. GEM match for the field name: {kad['gem_match_for_field_name']}. | Kept as recorded in every table and total. Flagged on the Methods/Validation page. |
| K2 | {len(offp)} sites (section d) | Labelled OFFSHORE in the World Bank file, but the point falls inside an ADM1 land polygon. | Kept as `state = "Offshore"` under plan Q8. |

## e. Formula sanity check, 2025 only

These figures confirm that the formulas and constants work. **They are checks, not findings.** The labels that apply are:
- CO2e: "{params.CO2E_LABEL}";
- value: "{params.VALUE_LABEL}", "{params.PRICE_LABEL}";
- flare fees: "{params.FEE_LABEL}" (never owed, unpaid, due or evaded; no comparison with amounts collected).

{md_table(san.assign(value=san['value'].map(lambda v: f'{v:,.4f}' if abs(v) < 1000 else f'{v:,.0f}')))}

Cross-check: the two energy routes differ by {abs(san.set_index('check').loc['energy_mmbtu_2025', 'value'] - san.set_index('check').loc['energy_mmbtu_2025_alt_route', 'value']):.3g} MMBtu, because 35,314,667 Mscf/bcm is a rounded constant.
"""
    DOC.write_text(text, encoding="utf-8")


REGS_QUOTES = """- PDF p.7: "Producers producing 10,000 or more barrels of oil a day, shall be liable to the Federal Government for flare fee payment of USD2.00 per 28.317 standard cubic metres of gas flared". 28.317 m3 = 1 Mscf.
- PDF p.7: "The fee reduces to USD0.50/Mscf where the field produces less than 10,000 barrels of oil a day."
- PDF p.7: the USD2.00 rate applies "irrespective of whether the flaring is routine or non-routine flaring except where the flaring occurs as a result of events or phenomena beyond the producer's reasonable control".
- **Basis:** daily oil output of the producer or field (10,000 barrels per day threshold). Output is not in the satellite data, so both rates are shown as a low–high range (plan 5.3).
- Not used: PDF p.8–9 describe a separate fine of USD2.50/Mscf for breaches of reporting and metering obligations. It is outside plan 5.3."""


def main() -> None:
    r = subprocess.run([sys.executable, "-I", str(ROOT / "validation" / "recompute.py")], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(r.stderr)
    fact, site, year, groups = load()
    off_all = pd.read_csv(INTERIM / "official_volumes.csv")
    svo = satellite_vs_official(fact, year)
    cmp_ = compare(fact, site, groups)
    gem = gem_crosscheck(site)
    offp = offshore_in_polygon(site)
    kad = kaduna(site, fact)
    san = sanity_2025(fact)

    svo.to_csv(INTERIM / "phase2b_satellite_vs_official.csv", index=False, encoding="utf-8")
    cmp_.to_csv(INTERIM / "phase2b_recompute_comparison.csv", index=False, encoding="utf-8")
    gem.to_csv(INTERIM / "phase2b_gem_crosscheck_top20.csv", index=False, encoding="utf-8")
    offp.to_csv(INTERIM / "phase2b_flag_offshore_in_polygon.csv", index=False, encoding="utf-8")
    san.to_csv(INTERIM / "phase2b_sanity_2025.csv", index=False, encoding="utf-8")
    (INTERIM / "phase2b_flag_kaduna.json").write_text(json.dumps(kad, indent=2, default=str), encoding="utf-8")
    write_doc(svo, cmp_, gem, offp, kad, san, off_all, REGS_QUOTES)

    print(svo.round(3).to_string(index=False))
    print(f"recompute: {int(cmp_['pass'].sum())}/{len(cmp_)} pass")
    print(cmp_[~cmp_["pass"]].to_string(index=False) if (~cmp_["pass"]).any() else "no recompute failures")
    print({c: int(gem[c].sum()) for c in gem.columns if c.startswith("flag_")})
    print(f"offshore in polygon: {len(offp)}")


if __name__ == "__main__":
    main()
