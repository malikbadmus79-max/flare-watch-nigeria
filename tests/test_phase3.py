"""Phase 3 tests. They do not need Power BI open: they check the model spec and the saved
output of powerbi/phase3_validate.py (run with FlareWatch open)."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "powerbi"))
import model_spec as spec  # noqa: E402

FORBIDDEN = ["penalt", "owed", "unpaid", "evaded", "liable", "on track", "off track", "forecast", "health",
             "exposure"]


def test_validation_all_pass():
    v = pd.read_csv(ROOT / "data" / "interim" / "phase3_validation.csv")
    assert len(v) >= 90
    assert v["pass"].all(), v[~v["pass"]]
    names = {m[0] for m in spec.MEASURES}
    assert set(v["measure"]) <= names


def test_required_checks_present():
    v = pd.read_csv(ROOT / "data" / "interim" / "phase3_validation.csv")
    need = {"Flare Volume (bcm)", "Active Sites", "Persistent Sites (12 of 14)", "Top 10 Sites Share",
            "CO2e (Mt)", "Gas Value Low (USD)", "Gas Value Central (USD)", "Gas Value High (USD)",
            "Implied Flare Fee Low (USD)", "Implied Flare Fee High (USD)"}
    assert need <= set(v["measure"])
    fee = v[v["measure"].str.startswith("Implied Flare Fee")].set_index("measure")["python"]
    assert round(fee["Implied Flare Fee Low (USD)"]) == 116_552_636
    assert round(fee["Implied Flare Fee High (USD)"]) == 466_210_544


def test_measure_spec():
    names = [m[0] for m in spec.MEASURES]
    assert len(names) == len(set(names))
    folders = {m[1] for m in spec.MEASURES}
    assert folders == {"Volume", "Sites", "Concentration", "Cost", "People", "Validation"}
    for name, folder, fmt, desc, dax in spec.MEASURES:
        assert desc and dax, name
        assert fmt or name.endswith(("Colour", "(short)")), name  # only text helpers have no format string
        assert not any(w in name.lower() for w in FORBIDDEN), name
    assert "Implied Flare Fee Low (USD)" in names and "Implied Flare Fee High (USD)" in names


def test_no_hardcoded_parameters():
    """CO2e factor, prices and fee rates come from param_assumptions."""
    dax = {m[0]: m[4] for m in spec.MEASURES}
    for v in ["2.569", "2.13", "3.52", "13.4", "0.5", "2.00", "35314667", "1020"]:
        assert not any(v in d for d in dax.values()), v
    for name, p in [("CO2e (Mt)", "co2e_mt_per_bcm"), ("Gas Value Low (USD)", "price_low_usd_per_mmbtu"),
                    ("Gas Value Central (USD)", "price_central_usd_per_mmbtu"),
                    ("Gas Value High (USD)", "price_high_usd_per_mmbtu"),
                    ("Implied Flare Fee Low (USD)", "flare_fee_low_usd_per_mscf"),
                    ("Implied Flare Fee High (USD)", "flare_fee_high_usd_per_mscf")]:
        assert f'"{p}"' in dax[name], name
