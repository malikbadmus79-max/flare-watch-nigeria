"""Phase 5b tests: the web map (map/index.html) against data/processed/.

The page embeds its data as JSON. These tests check that every number the page shows (national
estimated bcm by year, sites with flaring detected by year, site attributes) equals the processed
tables, that the committed page is what build_web_map.py generates, and the safe-claim wording.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from flare_watch import build_web_map  # noqa: E402

PAGE = ROOT / "map" / "index.html"
PROCESSED = ROOT / "data" / "processed"
YEARS = list(range(2012, 2026))
FORBIDDEN = ["penalt", "owed", "unpaid", "evaded", "liable", "on track", "off track", "forecast", "health",
             "exposure", "stopped flaring", "no emissions", "worst", "most harmful", "measured"]
APPROVED_DISCLAIMER = ("All volumes are satellite estimates; operators as recorded; not a statement about any "
                       "company's conduct; proximity only, not exposure or health.")


@pytest.fixture(scope="module")
def html():
    return PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def data(html):
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    assert m, "embedded data block not found"
    return json.loads(m.group(1))


@pytest.fixture(scope="module")
def fact():
    return pd.read_csv(PROCESSED / "fact_site_year.csv")


@pytest.fixture(scope="module")
def site():
    return pd.read_csv(PROCESSED / "dim_site.csv")


def test_page_size_and_up_to_date(html):
    assert PAGE.stat().st_size < 2 * 1024 * 1024
    assert html == build_web_map.build_html(), "map/index.html is stale: run src/flare_watch/build_web_map.py"


def test_national_totals_match_processed(data, fact):
    nat = fact.groupby("year").agg(bcm=("bcm", "sum"), active=("active", "sum")).reindex(YEARS)
    assert data["years"] == YEARS
    for k, y in enumerate(YEARS):
        assert abs(data["national_bcm"][k] - nat.loc[y, "bcm"]) < 1e-6, y
        assert f"{data['national_bcm'][k]:.2f}" == f"{nat.loc[y, 'bcm']:.2f}", y  # value shown on the page
        assert data["national_active"][k] == int(nat.loc[y, "active"]), y          # exact count
    assert data["national_active"][-1] == 259 and f"{data['national_bcm'][-1]:.2f}" == "6.60"


def test_site_values_match_processed(data, fact, site):
    assert data["n_sites"] == len(site) == 476
    assert data["n_persistent"] == int(site["persistent"].sum())
    cols = data["fields"]
    page = pd.DataFrame(data["sites"], columns=cols).set_index("site_id")
    assert list(page.index) == list(site["site_id"])
    s = site.set_index("site_id")
    assert (page["active_years"] == s["active_years"]).all()
    assert (page["persistent"].astype(bool) == s["persistent"]).all()
    assert (page["field"] == s["field"]).all() and (page["operator"] == s["operator_clean"]).all()
    assert (page["location"] == s["location"]).all() and (page["state"] == s["state"]).all()
    assert ((page["pop_2km"] - s["pop_2km"]).abs() <= 0.5).all()
    assert ((page["pop_5km"] - s["pop_5km"]).abs() <= 0.5).all()

    vols = pd.DataFrame(page["bcm_by_year"].tolist(), index=page.index, columns=YEARS)
    wide = fact.pivot(index="site_id", columns="year", values="bcm").reindex(index=page.index, columns=YEARS)
    act = fact.pivot(index="site_id", columns="year", values="active").reindex(index=page.index, columns=YEARS)
    assert ((vols > 0) == act).all().all(), "flaring detected / not detected must match fact_site_year.active"
    assert ((vols - wide).abs() <= wide.abs() * 1e-4 + 1e-12).all().all()
    for k, y in enumerate(YEARS):  # the per-site values the map draws add up to the national total
        assert abs(vols[y].sum() - data["national_bcm"][k]) < 0.001, y
        assert int((vols[y] > 0).sum()) == data["national_active"][k], y
    assert data["max_bcm"] == pytest.approx(wide.max().max(), rel=1e-4)


def test_safe_claim_wording(html):
    assert APPROVED_DISCLAIMER in html
    for phrase in ["satellite estimate", "as recorded, World Bank 2026 release", "proximity only",
                   "No flaring detected", "may overlap", "WorldPop", "CC BY 4.0", "geoBoundaries",
                   "NOAA", "Payne Institute", "World Bank GFMR", "Malik Kolawole Badmus", build_web_map.REPO_URL,
                   "OpenStreetMap"]:
        assert phrase.lower() in html.lower(), phrase
    text = html.replace(APPROVED_DISCLAIMER, "").lower()
    hits = [w for w in FORBIDDEN if w in text]
    assert not hits, hits
