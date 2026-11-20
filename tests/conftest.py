"""Skip the tests that need the raw source files when data/raw/ is not present.

The raw files are not redistributed in this repository (see README, "Data you must download yourself").
With them in data/raw/, every test runs; without them, the tests below are skipped and the rest run
against the committed data/processed/ and data/interim/ outputs.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE_FILE = ROOT / "data" / "raw" / "Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx"

NEEDS_RAW = {
    "test_site_file_has_expected_13_columns",
    "test_nigeria_years_are_2012_to_2025",
    "test_national_totals_match_raw",
    "test_sources_registers",
    "test_cache_matches_raw_hash",
}


def pytest_collection_modifyitems(config, items):
    if SITE_FILE.exists():
        return
    skip = pytest.mark.skip(reason="needs the raw source files in data/raw/ (not redistributed)")
    for item in items:
        if item.name in NEEDS_RAW:
            item.add_marker(skip)
