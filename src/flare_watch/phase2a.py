"""Phase 2a runner: sources register, cleaning, geography, population, Power BI tables.

Run from the project root:
    .venv/Scripts/python src/flare_watch/phase2a.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flare_watch import clean, geo, official, params  # noqa: E402

ROOT = clean.ROOT
RAW, INTERIM = clean.RAW, clean.INTERIM
PROCESSED = ROOT / "data" / "processed"

LOCAL_URL = "Local copy from Downloads (URL to be recorded in Phase 4)"
PHASE2_SOURCES = [
    ("worldpop/nga_pop_2025_CN_100m_R2025A_v1.tif",
     "WorldPop 2025 population count, Nigeria, 100 m, constrained (R2025A v1)",
     "https://doi.org/10.5258/SOTON/WP00839",
     "WorldPop; CC BY 4.0. DOI 10.5258/SOTON/WP00839."),
    ("boundaries/geoBoundaries-NGA-ADM1.geojson",
     "geoBoundaries Nigeria ADM1 (states), gbOpen; source GRID3 2022",
     "https://www.geoboundaries.org",
     "geoBoundaries gbOpen (from GRID3 2022); CC BY 4.0."),
    ("boundaries/geoBoundaries-NGA-ADM2.geojson",
     "geoBoundaries Nigeria ADM2 (LGAs), gbOpen; source GRID3 2022",
     "https://www.geoboundaries.org",
     "geoBoundaries gbOpen (from GRID3 2022); CC BY 4.0."),
    ("docs/SoGF.pdf",
     "BudgIT, State of Gas Flaring in Nigeria (#ZEROFLARE2030), Jan 2026",
     "https://budgit.org/wp-content/uploads/2026/01/SoGF.pdf",
     "BudgIT document; cite only, not redistributed."),
    ("docs/FLARE-GAS-PREVENTION-OF-WASTE-AND-POLLUTION-REGULATIONS-2018.pdf",
     "Templars (law firm) newsletter on the Flare Gas (Prevention of Waste and Pollution) Regulations 2018",
     "https://www.templars-law.com/wp-content/uploads/2018/09/FLARE-GAS-PREVENTION-OF-WASTE-AND-POLLUTION-REGULATIONS-2018.pdf",
     "Law-firm copy, not the official gazette. Legal commentary; cite only, not redistributed."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sources() -> pd.DataFrame:
    rows = [{"file": rel, "description": d, "size_bytes": (RAW / rel).stat().st_size,
             "sha256": sha256(RAW / rel), "source_url": u, "licence_note": n}
            for rel, d, u, n in PHASE2_SOURCES]
    df = pd.DataFrame(rows)
    df.to_csv(INTERIM / "sources_phase2.csv", index=False, encoding="utf-8")
    return df


PATH_END_YEAR = 2030  # Amendment A3: dim_year extended for the illustrative 2025-2030 path


def build_dim_year(off: pd.DataFrame) -> pd.DataFrame:
    """Years 2012-2030. is_actual is True for satellite years (2012-2025) only (Amendment A3)."""
    dim_year = pd.DataFrame({"year": list(range(clean.YEARS[0], PATH_END_YEAR + 1))})
    dim_year["is_recent"] = dim_year["year"].isin(clean.RECENT_YEARS)
    dim_year["is_actual"] = dim_year["year"].isin(clean.YEARS)
    used = official.used_by_year(off)
    dim_year["official_bcm"] = dim_year["year"].map(used["bcm"])
    dim_year["official_source"] = dim_year["year"].map(used["label"])
    return dim_year


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    report: dict = {}

    src = write_sources()
    report["sources_phase2"] = src[["file", "size_bytes", "sha256"]].to_dict("records")

    ng = clean.load_raw_sites()
    fact, sites, op_log, field_log = clean.build_sites(ng)
    op_log.to_csv(INTERIM / "operator_cleaning.csv", index=False, encoding="utf-8")
    field_log.to_csv(INTERIM / "field_cleaning.csv", index=False, encoding="utf-8")

    admin, admin_log = geo.assign_admin(sites)
    sites = sites.merge(admin, on="site_id", how="left", validate="1:1").reset_index(drop=True)
    per_site, groups, pop_meta = geo.population(sites)
    sites = sites.merge(per_site, on="site_id", how="left", validate="1:1")

    # --- Power BI tables (plan s9.1) ---
    fact.to_csv(PROCESSED / "fact_site_year.csv", index=False, encoding="utf-8")

    dim_site = sites[["site_id", "lat", "lon", "field", "operator_clean", "field_type", "location",
                      "state", "lga", "pop_2km", "pop_5km", "persistent", "persistent_10", "persistent_14",
                      "active_years", "recent_volume_bcm", "active_2025",
                      "operator_raw", "field_raw", "state_iso", "state_id", "state_method",
                      "lga_id", "lga_method"]]
    dim_site.to_csv(PROCESSED / "dim_site.csv", index=False, encoding="utf-8")

    off = official.official_volumes()
    off.to_csv(INTERIM / "official_volumes.csv", index=False, encoding="utf-8")
    build_dim_year(off).to_csv(PROCESSED / "dim_year.csv", index=False, encoding="utf-8")

    variants = (sites.groupby("operator_clean")["operator_raw"]
                .apply(lambda s: " | ".join(sorted(set(s.fillna("<missing>").astype(str))))))
    dim_operator = pd.DataFrame({"operator_clean": variants.index, "operator_raw_variants": variants.values})
    dim_operator["is_unattributed"] = dim_operator["operator_clean"].eq(clean.UNATTRIBUTED_OPERATOR)
    dim_operator["n_sites"] = dim_operator["operator_clean"].map(sites["operator_clean"].value_counts())
    dim_operator.to_csv(PROCESSED / "dim_operator.csv", index=False, encoding="utf-8")

    adm1, _ = geo.load_boundaries()
    dim_state = adm1[["shapeName", "shapeISO", "shapeID"]].rename(
        columns={"shapeName": "state", "shapeISO": "state_iso", "shapeID": "state_id"})
    dim_state["state_type"] = "ADM1"
    extra = [{"state": geo.OFFSHORE, "state_iso": "", "state_id": "", "state_type": "Offshore (plan Q8)"}]
    if (sites["state"] == geo.UNASSIGNED).any():
        extra.append({"state": geo.UNASSIGNED, "state_iso": "", "state_id": "", "state_type": "Unassigned"})
    dim_state = pd.concat([dim_state, pd.DataFrame(extra)], ignore_index=True)
    dim_state["n_sites"] = dim_state["state"].map(sites["state"].value_counts()).fillna(0).astype(int)
    dim_state = dim_state.sort_values("state").reset_index(drop=True)
    dim_state.to_csv(PROCESSED / "dim_state.csv", index=False, encoding="utf-8")

    params.param_table().to_csv(PROCESSED / "param_assumptions.csv", index=False, encoding="utf-8")
    groups.to_csv(PROCESSED / "population_groups.csv", index=False, encoding="utf-8")

    # --- facts for the results doc ---
    report["counts"] = {
        "fact_rows": int(len(fact)), "sites": int(len(sites)),
        "persistent_10": int(sites["persistent_10"].sum()), "persistent_12": int(sites["persistent"].sum()),
        "persistent_14": int(sites["persistent_14"].sum()), "active_2025": int(sites["active_2025"].sum()),
        "sites_by_state": {k: int(v) for k, v in sites["state"].value_counts().sort_index().items()},
        "lga_unassigned_onshore": int((sites["lga"] == geo.UNASSIGNED).sum()),
        "distinct_lgas_with_sites": int(sites.loc[~sites["lga"].isin([geo.OFFSHORE, geo.UNASSIGNED]), "lga_id"].nunique()),
        "operators_clean": int(sites["operator_clean"].nunique()),
        "fields_clean": int(sites["field"].nunique()),
    }
    report["admin_assignment"] = admin_log
    report["operator_cleaning"] = op_log.to_dict("records")
    report["field_cleaning"] = field_log.to_dict("records")
    report["population_method"] = pop_meta
    report["population_sites_zero"] = {f"pop_{k}km": int((sites[f'pop_{k}km'] == 0).sum()) for k in geo.BUFFERS_KM}
    (INTERIM / "phase2a_report.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report["counts"], indent=1))
    print(json.dumps(admin_log, indent=1))


if __name__ == "__main__":
    main()
