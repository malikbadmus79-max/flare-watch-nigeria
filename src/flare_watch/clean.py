"""Phase 2a: clean World Bank site attributes and derive per-site flags.

Rules follow the frozen plan (docs/analysis_plan.md v1.0):
- Operator (Q2): trim spaces and fix case only; no merging of near-variants.
  Missing -> "Unattributed" (Q1). Every change is logged.
- Field name (Q1, Q10): missing or "*" -> "Unattributed field". Field type
  missing -> "Unattributed". Every change is logged.
- Flags (section 3): active, active_years, persistent (>=12/14),
  persistent_10, persistent_14, recent_volume_bcm (mean 2023-2025, zeros
  count), active_2025.

Raw files are read only, never modified.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

SITE_FILE = RAW / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"
SITE_SHEET = "Dashboard_file"
COUNTRY = "Nigeria"

YEARS = list(range(2012, 2026))
N_YEARS = len(YEARS)
RECENT_YEARS = [2023, 2024, 2025]
PERSIST_MAIN, PERSIST_LOW, PERSIST_HIGH = 12, 10, 14

UNATTRIBUTED_OPERATOR = "Unattributed"
UNATTRIBUTED_FIELD = "Unattributed field"
UNATTRIBUTED_FIELD_TYPE = "Unattributed"


def load_raw_sites() -> pd.DataFrame:
    """Nigeria rows of the World Bank site file (verbatim), via the hash-checked parquet cache."""
    from flare_watch.cache import load_ng_sites
    return load_ng_sites()


def _missing(s: pd.Series) -> pd.Series:
    txt = s.astype("string").str.strip()
    return s.isna() | txt.eq("") | txt.str.upper().eq("NA")


def _case_map(values: pd.Series) -> dict[str, str]:
    """Map each trimmed value to the most frequent spelling among case-only variants.

    Ties are broken alphabetically so the result is deterministic.
    """
    counts = values.value_counts()
    out: dict[str, str] = {}
    for _, grp in counts.groupby(counts.index.str.casefold()):
        best = sorted(grp.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        for v in grp.index:
            out[v] = best
    return out


def clean_operator(ng: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    raw = ng["Operator"]
    miss = _missing(raw)
    trimmed = raw.where(miss, raw.astype("string").str.strip())
    cmap = _case_map(trimmed[~miss].astype(str))
    clean = trimmed.where(miss, trimmed[~miss].astype(str).map(cmap))
    clean = clean.where(~miss, UNATTRIBUTED_OPERATOR).astype(str)

    log_rows = []
    for (r, c), grp in ng.assign(_raw=raw.astype("string").fillna("<missing>"), _clean=clean).groupby(["_raw", "_clean"]):
        if r == c:
            continue
        if r == "<missing>" or r.strip() == "" or r.strip().upper() == "NA":
            rule = "missing -> Unattributed (plan Q1)"
        elif r.strip() != r and r.strip() == c:
            rule = "trim leading/trailing spaces (plan Q2)"
        else:
            rule = "trim and case-only harmonisation (plan Q2)"
        log_rows.append({"column": "Operator", "raw_value": r, "clean_value": c, "rule": rule,
                         "n_sites": int(grp["id"].nunique()), "n_rows": int(len(grp))})
    log = pd.DataFrame(log_rows, columns=["column", "raw_value", "clean_value", "rule", "n_sites", "n_rows"])
    return clean, log


def clean_field(ng: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    rows = []
    fn_raw = ng["Field name"]
    fn_miss = _missing(fn_raw)
    fn_star = fn_raw.astype("string").str.strip().eq("*").fillna(False)
    field = fn_raw.astype("string").str.strip()
    field = field.mask(fn_miss | fn_star, UNATTRIBUTED_FIELD).astype(str)

    ft_raw = ng["Field type"]
    ft_miss = _missing(ft_raw)
    ftype = ft_raw.astype("string").str.strip().mask(ft_miss, UNATTRIBUTED_FIELD_TYPE).astype(str)

    for col, mask, raw_label, clean_value, rule in [
        ("Field name", fn_miss, "<missing>", UNATTRIBUTED_FIELD, "missing -> Unattributed field (plan Q1)"),
        ("Field name", fn_star, "*", UNATTRIBUTED_FIELD, "'*' -> Unattributed field (plan Q10)"),
        ("Field type", ft_miss, "<missing>", UNATTRIBUTED_FIELD_TYPE, "missing -> Unattributed (plan Q1)"),
    ]:
        if mask.any():
            rows.append({"column": col, "raw_value": raw_label, "clean_value": clean_value, "rule": rule,
                         "n_sites": int(ng.loc[mask, "id"].nunique()), "n_rows": int(mask.sum())})
    # Any other change (e.g. whitespace) on field names is logged too.
    other = (~fn_miss) & (~fn_star) & (fn_raw.astype("string") != field)
    for (r, c), grp in ng[other].assign(_c=field[other]).groupby(["Field name", "_c"]):
        rows.append({"column": "Field name", "raw_value": r, "clean_value": c,
                     "rule": "trim leading/trailing spaces", "n_sites": int(grp["id"].nunique()),
                     "n_rows": int(len(grp))})
    log = pd.DataFrame(rows, columns=["column", "raw_value", "clean_value", "rule", "n_sites", "n_rows"])
    return field, ftype, log


def build_fact(ng: pd.DataFrame) -> pd.DataFrame:
    fact = pd.DataFrame({
        "site_id": ng["id"].astype(str),
        "year": ng["Year"].astype(int),
        "bcm": ng["BCM"].astype(float),
        "mmscfd": ng["MMSCFD"].astype(float),
        "flare_level": ng["Flare Level"].astype(str),
    })
    fact["active"] = fact["bcm"] > 0
    return fact.sort_values(["site_id", "year"]).reset_index(drop=True)


def site_flags(fact: pd.DataFrame) -> pd.DataFrame:
    g = fact.groupby("site_id")
    flags = pd.DataFrame({"active_years": g["active"].sum().astype(int)})
    flags["persistent"] = flags["active_years"] >= PERSIST_MAIN
    flags["persistent_10"] = flags["active_years"] >= PERSIST_LOW
    flags["persistent_14"] = flags["active_years"] >= PERSIST_HIGH
    recent = fact[fact["year"].isin(RECENT_YEARS)]
    n_recent = recent.groupby("site_id")["year"].nunique()
    if (n_recent != len(RECENT_YEARS)).any():
        raise ValueError("Some sites lack a row for every recent year; mean would be biased.")
    flags["recent_volume_bcm"] = recent.groupby("site_id")["bcm"].mean()  # zeros count
    flags["active_2025"] = fact[fact["year"] == 2025].set_index("site_id")["active"]
    return flags.reset_index()


def build_sites(ng: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (fact_site_year, site attributes + flags, operator log, field log)."""
    op_clean, op_log = clean_operator(ng)
    field, ftype, field_log = clean_field(ng)
    attrs = pd.DataFrame({
        "site_id": ng["id"].astype(str),
        "lat": ng["lat"].astype(float),
        "lon": ng["lon"].astype(float),
        "field": field.values,
        "field_raw": ng["Field name"].astype("string").values,
        "operator_clean": op_clean.values,
        "operator_raw": ng["Operator"].astype("string").values,
        "field_type": ftype.values,
        "location": ng["Location"].astype(str).str.strip().values,
    })
    # Phase 0 showed these attributes are constant per site; enforce it.
    per_site = attrs.astype(str).groupby("site_id").nunique()
    if (per_site > 1).any().any():
        raise ValueError("Site attributes vary across years; plan assumes they do not.")
    sites = attrs.drop_duplicates("site_id").sort_values("site_id").reset_index(drop=True)
    fact = build_fact(ng)
    sites = sites.merge(site_flags(fact), on="site_id", how="left", validate="1:1")
    return fact, sites, op_log, field_log


def main() -> None:
    ng = load_raw_sites()
    fact, sites, op_log, field_log = build_sites(ng)
    op_log.to_csv(INTERIM / "operator_cleaning.csv", index=False, encoding="utf-8")
    field_log.to_csv(INTERIM / "field_cleaning.csv", index=False, encoding="utf-8")
    print(f"fact rows {len(fact)}, sites {len(sites)}; operator changes {len(op_log)}, field changes {len(field_log)}")


if __name__ == "__main__":
    main()
