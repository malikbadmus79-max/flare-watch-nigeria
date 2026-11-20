"""Phase 0: record raw sources and check the Nigeria flaring data.

Reads the raw files in data/raw (never modifies them) and writes
outputs to data/interim. Descriptive checks only; no analysis.

Run from the project root:
    .venv/Scripts/python -m flare_watch.phase0_check   (with src on PYTHONPATH)
or
    .venv/Scripts/python src/flare_watch/phase0_check.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

SITE_FILE = RAW / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"
COUNTRY_FILE = RAW / "Flare-volume-and-intensity-estimates-2012-2025.xlsx"
GEM_FILE = RAW / "Global-Oil-and-Gas-Extraction-Tracker-March-2026.xlsx"

SITE_SHEET = "Dashboard_file"
COUNTRY_SHEET = "Flare volume"
GEM_SHEET = "Field-level main data"
COUNTRY = "Nigeria"
TOLERANCE_BCM = 0.001

EXPECTED_SITE_COLUMNS = [
    "id", "lat", "lon", "Country", "BCM", "MMSCFD", "Year", "Field type",
    "Operator", "Field name", "Location", "Flare Level", "Flaring Vol (million m3)",
]

WB_URL = "https://www.worldbank.org/en/programs/gasflaringreduction/global-flaring-data"
WB_NOTE = ("Attribution: NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR. "
           "No explicit licence stated; World Bank disclaimer applies.")
GEM_URL = "https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker"
GEM_NOTE = "Global Energy Monitor; CC BY 4.0."

DOCS = RAW / "docs"
TRACKER_PDF = DOCS / "Global-Gas-FlaringTracker-June-23-2026.pdf"
METHOD_PDF = DOCS / (
    "World-Bank-s-Global-Gas-Flaring-Reduction-Partnership-Gas-Flaring-Estimates-"
    "Methodology-for-Determining-the-Gas-Flare-Volumes-from-Satellite-Data.pdf"
)
PDF_URL = "Local copy from Downloads (URL to be recorded in Phase 4)"
TRACKER_NOTE = ("World Bank Group. Report text: reproduction for noncommercial purposes "
                "with full attribution (Rights and Permissions, PDF p.2).")
METHOD_NOTE = "World Bank GGFR. No explicit licence stated; World Bank disclaimer applies."

SOURCES = [
    (SITE_FILE, "World Bank GFMR flare volume by individual flare location", WB_URL, WB_NOTE),
    (COUNTRY_FILE, "World Bank GFMR flare volume and intensity by country", WB_URL, WB_NOTE),
    (GEM_FILE, "GEM Global Oil and Gas Extraction Tracker (March 2026)", GEM_URL, GEM_NOTE),
    (TRACKER_PDF, "World Bank GFMR Global Gas Flaring Tracker Report (June 2026)", PDF_URL, TRACKER_NOTE),
    (METHOD_PDF, "World Bank GGFR methodology note: gas flare volumes from satellite data", PDF_URL, METHOD_NOTE),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record_sources() -> pd.DataFrame:
    rows = [{
        "file": p.relative_to(RAW).as_posix(),
        "description": desc,
        "size_bytes": p.stat().st_size,
        "sha256": sha256(p),
        "source_url": url,
        "licence_note": note,
    } for p, desc, url, note in SOURCES]
    df = pd.DataFrame(rows)
    df.to_csv(INTERIM / "phase0_sources.csv", index=False)
    return df


def is_missing(s: pd.Series) -> pd.Series:
    """True where a value is empty, NaN or the literal text 'NA' (any case/whitespace)."""
    txt = s.astype("string").str.strip()
    return s.isna() | txt.eq("") | txt.str.upper().eq("NA")


def load_sites() -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_excel(SITE_FILE, sheet_name=SITE_SHEET)
    columns = list(df.columns)
    ng = df[df["Country"] == COUNTRY].copy()
    ng.to_csv(INTERIM / "ng_flare_sites_long.csv", index=False)
    return ng, columns


def site_report(ng: pd.DataFrame) -> dict:
    r: dict = {
        "rows": int(len(ng)),
        "unique_site_ids": int(ng["id"].nunique()),
        "years": sorted(int(y) for y in ng["Year"].unique()),
        "rows_per_year": {int(k): int(v) for k, v in ng.groupby("Year").size().items()},
    }
    r["missing"] = {}
    for col in ["Operator", "Field name", "Field type"]:
        m = is_missing(ng[col])
        r["missing"][col] = {
            "rows_missing": int(m.sum()),
            "sites_missing": int(ng.loc[m, "id"].nunique()),
            "of_which_literal_NA": int(ng[col].astype("string").str.strip().str.upper().eq("NA").sum()),
        }
    # Counts by category: rows and distinct sites (a site keeps one value across years if stable).
    r["counts"] = {}
    for col in ["Field type", "Location", "Flare Level"]:
        vals = ng[col].astype("string").fillna("<missing>")
        r["counts"][col] = {
            "rows": {k: int(v) for k, v in vals.value_counts().items()},
            "sites": {k: int(v) for k, v in ng.assign(_v=vals).groupby("_v")["id"].nunique().items()},
        }
    # Does each site carry one value per attribute across all years?
    r["sites_with_varying_attribute"] = {
        col: int((ng.assign(_v=ng[col].astype("string").fillna("<missing>"))
                  .groupby("id")["_v"].nunique() > 1).sum())
        for col in ["Field type", "Operator", "Field name", "Location", "Flare Level", "lat", "lon"]
    }
    r["sites_flaring_by_year"] = {
        int(k): int(v) for k, v in ng[ng["BCM"] > 0].groupby("Year")["id"].nunique().items()
    }
    r["rows_with_zero_bcm"] = int((ng["BCM"] == 0).sum())
    r["rows_with_missing_bcm"] = int(ng["BCM"].isna().sum())
    r["max_abs_diff_bcm_vs_million_m3"] = float(
        (ng["BCM"] - ng["Flaring Vol (million m3)"] / 1000).abs().max())
    r["unique_operators"] = int(ng.loc[~is_missing(ng["Operator"]), "Operator"].nunique())
    r["unique_field_names"] = int(ng.loc[~is_missing(ng["Field name"]), "Field name"].nunique())
    r["operators_with_trailing_space"] = sorted(
        o for o in ng["Operator"].dropna().unique() if str(o) != str(o).strip())
    return r


def check_site_vs_country(ng: pd.DataFrame) -> pd.DataFrame:
    c = pd.read_excel(COUNTRY_FILE, sheet_name=COUNTRY_SHEET)
    first = c.columns[0]
    row = c[c[first].astype(str).str.strip() == COUNTRY]
    if len(row) != 1:
        raise ValueError(f"Expected one '{COUNTRY}' row in '{COUNTRY_SHEET}', found {len(row)}")
    country = row.drop(columns=first).T.reset_index()
    country.columns = ["Year", "country_bcm"]
    country["Year"] = country["Year"].astype(float).astype(int)
    country["country_bcm"] = country["country_bcm"].astype(float)
    sites = ng.groupby("Year")["BCM"].sum().rename("site_total_bcm").reset_index()
    out = sites.merge(country, on="Year", how="outer").sort_values("Year")
    out["diff_bcm"] = out["site_total_bcm"] - out["country_bcm"]
    out["within_tolerance"] = out["diff_bcm"].abs() <= TOLERANCE_BCM
    out.to_csv(INTERIM / "check_site_vs_country.csv", index=False)
    return out


def load_gem() -> pd.DataFrame:
    g = pd.read_excel(GEM_FILE, sheet_name=GEM_SHEET)
    gn = g[g["Country/Area"] == COUNTRY].copy()
    gn.to_csv(INTERIM / "gem_ng_fields.csv", index=False)
    return gn


def gem_report(gn: pd.DataFrame) -> dict:
    has_coords = gn["Latitude"].notna() & gn["Longitude"].notna()
    has_op = ~is_missing(gn["Operator"])
    return {
        "fields": int(len(gn)),
        "unique_unit_ids": int(gn["Unit ID"].nunique()),
        "with_coordinates": int(has_coords.sum()),
        "with_operator": int(has_op.sum()),
        "with_both": int((has_coords & has_op).sum()),
        "status": {k: int(v) for k, v in gn["Status"].fillna("<missing>").value_counts().items()},
    }


def gem_base_name(unit_name: str) -> str:
    """Field name before the first ' Oil' or ' Gas' (e.g. 'Abana Oil and Gas Field (Nigeria)' -> 'Abana')."""
    return re.split(r" (?:Oil|Gas)\b", str(unit_name), maxsplit=1)[0].strip()


def name_match(ng: pd.DataFrame, gn: pd.DataFrame) -> dict:
    wb = ng.loc[~is_missing(ng["Field name"]), "Field name"].astype(str).str.strip()
    wb_names = set(wb.str.lower())
    gem_names = {gem_base_name(n).lower() for n in gn["Unit Name"].dropna()}
    matched = sorted(wb_names & gem_names)
    pd.DataFrame({"wb_field_name_lower": sorted(wb_names)}).assign(
        matches_gem=lambda d: d["wb_field_name_lower"].isin(gem_names)
    ).to_csv(INTERIM / "name_match_wb_gem.csv", index=False)
    return {
        "wb_unique_field_names": len(wb_names),
        "gem_unique_base_names": len(gem_names),
        "wb_names_matching_gem": len(matched),
        "wb_names_not_matching": len(wb_names) - len(matched),
    }


def main() -> dict:
    INTERIM.mkdir(parents=True, exist_ok=True)
    sources = record_sources()
    ng, columns = load_sites()
    report = {
        "sources": sources[["file", "size_bytes", "sha256"]].to_dict("records"),
        "site_file_columns": columns,
        "site_file_columns_as_expected": columns == EXPECTED_SITE_COLUMNS,
        "nigeria_sites": site_report(ng),
    }
    cmp = check_site_vs_country(ng)
    report["site_vs_country"] = {
        "years_compared": int(len(cmp)),
        "all_within_tolerance": bool(cmp["within_tolerance"].all()),
        "max_abs_diff_bcm": float(cmp["diff_bcm"].abs().max()),
        "tolerance_bcm": TOLERANCE_BCM,
    }
    gn = load_gem()
    report["gem_nigeria"] = gem_report(gn)
    report["name_match"] = name_match(ng, gn)
    (INTERIM / "phase0_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    s, v, gm, nm = report["nigeria_sites"], report["site_vs_country"], report["gem_nigeria"], report["name_match"]
    print("Phase 0 summary")
    print(f"  Site file columns as expected (13): {report['site_file_columns_as_expected']}")
    print(f"  Nigeria rows: {s['rows']}; unique site ids: {s['unique_site_ids']}; "
          f"years: {s['years'][0]}-{s['years'][-1]} ({len(s['years'])})")
    print(f"  Missing (rows): " + ", ".join(f"{k}={d['rows_missing']}" for k, d in s["missing"].items()))
    print(f"  Sites flaring (BCM>0) by year: {s['sites_flaring_by_year']}")
    print(f"  Site vs country: all {v['years_compared']} years within {TOLERANCE_BCM} bcm = "
          f"{v['all_within_tolerance']} (max |diff| {v['max_abs_diff_bcm']:.2e})")
    print(f"  GEM Nigeria fields: {gm['fields']}; with coordinates: {gm['with_coordinates']}; "
          f"with operator: {gm['with_operator']}")
    print(f"  WB field names matching a GEM name: {nm['wb_names_matching_gem']} of {nm['wb_unique_field_names']}")
    return report


if __name__ == "__main__":
    main()
