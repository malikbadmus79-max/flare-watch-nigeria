"""Phase 0 tests. Run phase0_check.py first; these read its interim outputs."""
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
SITE_FILE = ROOT / "data" / "raw" / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"

EXPECTED_COLUMNS = [
    "id", "lat", "lon", "Country", "BCM", "MMSCFD", "Year", "Field type",
    "Operator", "Field name", "Location", "Flare Level", "Flaring Vol (million m3)",
]


def test_site_file_has_expected_13_columns():
    wb = openpyxl.load_workbook(SITE_FILE, read_only=True)
    header = [c for c in next(wb["Dashboard_file"].iter_rows(max_row=1, values_only=True))]
    wb.close()
    while header and header[-1] is None:  # trailing empty cells, if any
        header.pop()
    assert len(header) == 13
    assert header == EXPECTED_COLUMNS


def test_nigeria_years_are_2012_to_2025():
    ng = pd.read_csv(INTERIM / "ng_flare_sites_long.csv")
    assert (ng["Country"] == "Nigeria").all()
    assert sorted(ng["Year"].unique()) == list(range(2012, 2026))


def test_site_totals_match_country_file():
    cmp = pd.read_csv(INTERIM / "check_site_vs_country.csv")
    assert len(cmp) == 14
    assert cmp["site_total_bcm"].notna().all() and cmp["country_bcm"].notna().all()
    assert (cmp["diff_bcm"].abs() <= 0.001).all()
