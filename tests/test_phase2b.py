"""Phase 2b tests. Run phase2a.py then phase2b.py first."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flare_watch import cache, params  # noqa: E402

INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"


# ---------- unit conversions ----------
def test_mscf_per_bcm_consistent_with_m3_to_ft3():
    assert params.BCM_TO_MSCF == pytest.approx(1e9 * params.M3_TO_FT3 / 1000, abs=1)


def test_bcf_per_bcm():
    assert params.BCM_TO_BCF == pytest.approx(params.M3_TO_FT3, abs=5e-5)


def test_mmscf_to_m3_is_inverse_of_m3_to_ft3():
    assert params.MMSCF_TO_M3 == pytest.approx(1e6 / params.M3_TO_FT3, rel=1e-8)


def test_mmbtu_per_bcm():
    assert params.mmbtu_per_bcm() == pytest.approx(35_314_667 * 1.020, rel=1e-12)


def test_param_table_values():
    p = pd.read_csv(PROCESSED / "param_assumptions.csv").set_index("parameter")
    assert p.loc["co2e_mt_per_bcm", "value"] == pytest.approx(429 / 167, abs=5e-4)
    assert p.loc["flare_fee_low_usd_per_mscf", "value"] == 0.50
    assert p.loc["flare_fee_high_usd_per_mscf", "value"] == 2.00
    assert (p.loc[["flare_fee_low_usd_per_mscf", "flare_fee_high_usd_per_mscf"], "status"] == "verified (law-firm copy)").all()
    assert list(p.loc[["price_low_usd_per_mmbtu", "price_central_usd_per_mmbtu", "price_high_usd_per_mmbtu"], "value"]) == [2.13, 3.52, 13.4]
    assert p["value"].notna().all()


# ---------- official volumes ----------
@pytest.fixture(scope="module")
def official():
    return pd.read_csv(INTERIM / "official_volumes.csv")


@pytest.mark.parametrize("year,mmscf,bcm", [
    (2021, 252_579, 252_579 * 28_316.8466 / 1e9),
    (2022, 188_442, 5.336083),
    (2023, 183_526, 5.196878),
    (2024, 192_887, 5.461952),
    (2025, 203_900, 5.773805),
])
def test_official_conversion(official, year, mmscf, bcm):
    r = official[(official["year"] == year) & official["used"]].iloc[0]
    assert r["mmscf"] == pytest.approx(mmscf)
    assert r["bcm"] == pytest.approx(bcm, abs=1e-6)


def test_official_sogf_total_matches_stated_total(official):
    u = official[official["used"] & official["year"].between(2021, 2024)]
    assert u["value"].sum() == 817_434  # SoGF PDF p.18 total


def test_dim_year_official(official):
    y = pd.read_csv(PROCESSED / "dim_year.csv").set_index("year")
    assert y.loc[2012:2020, "official_bcm"].isna().all()
    assert y.loc[2021:2025, "official_bcm"].notna().all()
    assert y.loc[2025, "official_source"] == "NUPRC figure as reported in the press"
    used = official[official["used"]].set_index("year")["bcm"]
    assert (y.loc[2021:2025, "official_bcm"] - used).abs().max() < 1e-12
    assert not official.loc[official["used"], "year"].duplicated().any()


def test_dim_year_extended_to_2030():  # Amendment A3
    y = pd.read_csv(PROCESSED / "dim_year.csv").set_index("year")
    assert list(y.index) == list(range(2012, 2031))
    assert list(y.columns) == ["is_recent", "is_actual", "official_bcm", "official_source"]
    assert y.loc[2012:2025, "is_actual"].all() and not y.loc[2026:2030, "is_actual"].any()
    assert not y.loc[2026:2030, "is_recent"].any()
    assert y.loc[2026:2030, ["official_bcm", "official_source"]].isna().all().all()
    fact = pd.read_csv(PROCESSED / "fact_site_year.csv")
    assert fact["year"].max() == 2025


# ---------- recompute ----------
def test_recompute_all_pass():
    c = pd.read_csv(INTERIM / "phase2b_recompute_comparison.csv", keep_default_na=False)
    assert len(c) == 68
    assert c["pass"].astype(str).eq("True").all(), c[c["pass"].astype(str) != "True"]


def test_recompute_covers_required_metrics():
    c = pd.read_csv(INTERIM / "phase2b_recompute_comparison.csv", keep_default_na=False)
    need = {"national_bcm", "persistent_count", "active_2025_count", "top10_site_share_2025", "pop_union"}
    assert need <= set(c["metric"])
    assert (c["metric"] == "national_bcm").sum() == 14
    assert (c["metric"] == "pop_union").sum() == len(pd.read_csv(PROCESSED / "population_groups.csv"))


def test_recompute_does_not_import_project():
    src = (ROOT / "validation" / "recompute.py").read_text(encoding="utf-8")
    code = src.split('"""', 2)[2]  # everything after the module docstring
    assert "flare_watch" not in code
    assert '"processed"' not in code and "data/processed" not in code


# ---------- cache ----------
def test_cache_matches_raw_hash():
    meta = json.loads(cache.CACHE_META.read_text(encoding="utf-8"))
    assert meta["source_sha256"] == cache.sha256(cache.SITE_FILE)
    assert meta["rows"] == 6664
    assert len(pd.read_parquet(cache.CACHE)) == 6664


# ---------- sanity ----------
def test_sanity_formulas():
    s = pd.read_csv(INTERIM / "phase2b_sanity_2025.csv").set_index("check")["value"]
    bcm = s["national_bcm_2025"]
    assert s["co2e_mt_2025"] == pytest.approx(bcm * 2.569)
    assert s["implied_flare_fee_high_usd_2025"] == pytest.approx(4 * s["implied_flare_fee_low_usd_2025"])
    assert s["energy_mmbtu_2025"] == pytest.approx(s["energy_mmbtu_2025_alt_route"], rel=1e-7)
    assert s["gas_value_central_usd_2025"] == pytest.approx(s["energy_mmbtu_2025"] * 3.52)
