"""Phase 2a tests. Run src/flare_watch/phase2a.py first; these read its outputs
and compare them with the raw World Bank site file."""
import hashlib
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
SITE_FILE = RAW / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"


@pytest.fixture(scope="module")
def raw_ng():
    """Verbatim Nigeria rows of the raw site file, via the parquet cache.

    The cache is used only if its stored source hash equals a fresh SHA-256 of
    the raw .xlsx; otherwise the raw file is read directly.
    """
    import json
    meta_p = INTERIM / "ng_sites_cache.json"
    if meta_p.exists():
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        if meta["source_sha256"] == hashlib.sha256(SITE_FILE.read_bytes()).hexdigest():
            return pd.read_parquet(INTERIM / "ng_sites_cache.parquet")
    df = pd.read_excel(SITE_FILE, sheet_name="Dashboard_file")
    return df[df["Country"] == "Nigeria"]


@pytest.fixture(scope="module")
def fact():
    return pd.read_csv(PROCESSED / "fact_site_year.csv")


@pytest.fixture(scope="module")
def site():
    return pd.read_csv(PROCESSED / "dim_site.csv", keep_default_na=False, na_values=[""])


def test_row_counts(fact, site):
    assert len(site) == 476 and site["site_id"].is_unique
    assert len(fact) == 6664
    assert not fact.duplicated(["site_id", "year"]).any()
    assert set(fact["site_id"]) == set(site["site_id"])
    assert sorted(fact["year"].unique()) == list(range(2012, 2026))


def test_national_totals_match_raw(fact, raw_ng):
    ours = fact.groupby("year")["bcm"].sum()
    raw = raw_ng.groupby("Year")["BCM"].sum()
    assert list(ours.index) == list(raw.index)
    assert ((ours - raw.values).abs() <= 1e-9).all()


def test_every_site_has_state(site):
    assert site["state"].notna().all() and (site["state"].astype(str).str.strip() != "").all()
    assert site["lga"].notna().all() and (site["lga"].astype(str).str.strip() != "").all()
    off = site["location"].str.upper() == "OFFSHORE"
    assert (site.loc[off, "state"] == "Offshore").all() and (site.loc[off, "lga"] == "Offshore").all()
    assert (site.loc[~off, "state"] != "Offshore").all()
    states = set(pd.read_csv(PROCESSED / "dim_state.csv", keep_default_na=False)["state"])
    assert set(site["state"]) <= states and "Offshore" in states


def test_persistent_flags_consistent(fact, site):
    s = site.set_index("site_id")
    active_years = fact.assign(a=fact["bcm"] > 0).groupby("site_id")["a"].sum()
    assert (s["active_years"] == active_years.reindex(s.index)).all()
    assert (s["persistent"] == (s["active_years"] >= 12)).all()
    assert (s["persistent_10"] == (s["active_years"] >= 10)).all()
    assert (s["persistent_14"] == (s["active_years"] >= 14)).all()
    assert (s["persistent_14"] <= s["persistent"]).all() and (s["persistent"] <= s["persistent_10"]).all()
    recent = fact[fact["year"].between(2023, 2025)].groupby("site_id")["bcm"].mean()
    assert ((s["recent_volume_bcm"] - recent.reindex(s.index)).abs() <= 1e-12).all()
    a25 = fact[fact["year"] == 2025].set_index("site_id")["bcm"] > 0
    assert (s["active_2025"] == a25.reindex(s.index)).all()


def test_union_population_not_above_sum():
    g = pd.read_csv(PROCESSED / "population_groups.csv", keep_default_na=False)
    assert len(g) > 0
    assert (g["pop_union"] <= g["pop_sum_of_sites"] + 1e-6).all()
    assert (g["pop_union"] >= 0).all()


def test_site_population_valid(site):
    assert (site["pop_2km"] >= 0).all() and (site["pop_5km"] >= 0).all()
    assert (site["pop_5km"] >= site["pop_2km"] - 1e-6).all()


def test_cleaning_rules(site):
    assert (site["operator_clean"] == site["operator_clean"].str.strip()).all()
    assert site["operator_clean"].notna().all()
    assert "*" not in set(site["field"])
    assert site["field"].notna().all()
    for f in ["operator_cleaning.csv", "field_cleaning.csv"]:
        assert (INTERIM / f).exists()


def test_sources_registers():
    p0 = pd.read_csv(INTERIM / "phase0_sources.csv")
    assert len(p0) == 5
    p2 = pd.read_csv(INTERIM / "sources_phase2.csv")
    assert len(p2) == 5
    for _, r in p2.iterrows():
        path = RAW / r["file"]
        assert path.stat().st_size == r["size_bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == r["sha256"]
