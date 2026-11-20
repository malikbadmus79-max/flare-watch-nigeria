"""Official national flared volumes (RQ6) -> data/interim/official_volumes.csv.

Every figure is transcribed by hand from the cited page and checked against a
rendered image of that page. Only rows with used == True enter
dim_year.official_bcm. Rows with used == False are recorded for transparency.
"""
from __future__ import annotations

import pandas as pd

from flare_watch.params import MMSCF_TO_M3

SOGF = "BudgIT, The State of Gas Flaring in Nigeria (Jan 2026), SoGF.pdf"
PRESS_LABEL = "NUPRC figure as reported in the press"
PRESS = ("Per Second News, 30 Jan 2026, reporting NUPRC '2025 Gas Production Status Report' "
         "(https://persecondnews.com/2026/01/30/nigerias-gas-flaring-hits-203-9bn-scf-in-2025-nuprc/, "
         "accessed 2026-11-20); Amendment A1")

UNIT_TO_MMSCF = {"MMscf": 1.0, "billion scf": 1000.0}

# (year, value, unit, source, page, original_source, label, used, note)
RECORDS = [
    (2021, 252_579, "MMscf", SOGF, "PDF p.18 (printed p.15), 'Total Gas Flared (MMSCF)'", "NUPRC",
     "NUPRC via BudgIT", True, ""),
    (2022, 188_442, "MMscf", SOGF, "PDF p.18 (printed p.15)", "NUPRC", "NUPRC via BudgIT", True, ""),
    (2023, 183_526, "MMscf", SOGF, "PDF p.18 (printed p.15)", "NUPRC", "NUPRC via BudgIT", True, ""),
    (2024, 192_887, "MMscf", SOGF, "PDF p.18 (printed p.15)", "NUPRC", "NUPRC via BudgIT", True, ""),
    (2025, 203.9, "billion scf", PRESS, "n/a (press article)", "NUPRC", PRESS_LABEL, True, "Amendment A1"),
]

# Stated in SoGF but NOT used (outside plan scope or unit inconsistent). See phase2b_validation.md.
NEITI_T2 = {2014: 282, 2015: 318, 2016: 288, 2017: 355, 2018: 267, 2019: 265, 2020: 230,
            2021: 250, 2022: 188, 2023: 183}
for y, v in NEITI_T2.items():
    RECORDS.append((y, v, "billion scf", SOGF, "PDF p.9 (printed p.6), Table 2 'Flare Gas (Billion SCF)'",
                    "NEITI", "NEITI via BudgIT", False,
                    "Not used: source is NEITI, not NUPRC/NNPC as plan RQ6 specifies; use would need an amendment"))
DPR_T1 = {2012: 465.25, 2013: 427.97, 2014: 393.83, 2015: 330.93, 2016: 288.91}
for y, v in DPR_T1.items():
    RECORDS.append((y, v, "stated 'Million SCF'", SOGF,
                    "PDF p.8 (printed p.5), Table 1 'Gas flared (Million SCF)'", "DPR via BudgIT 2018",
                    "DPR via BudgIT", False,
                    "Not used: unit label 'Million SCF' is implausible for national volumes and the values "
                    "disagree with Table 2 for 2014-2016; not converted"))


def official_volumes() -> pd.DataFrame:
    df = pd.DataFrame(RECORDS, columns=["year", "value", "unit", "source", "page", "original_source",
                                        "label", "used", "note"])
    mm = df["unit"].map(UNIT_TO_MMSCF)
    df["mmscf"] = df["value"] * mm
    df["bcm"] = df["mmscf"] * MMSCF_TO_M3 / 1e9
    df = df[["year", "value", "unit", "mmscf", "bcm", "source", "page", "original_source", "label", "used", "note"]]
    return df.sort_values(["used", "year"], ascending=[False, True]).reset_index(drop=True)


def used_by_year(df: pd.DataFrame) -> pd.DataFrame:
    u = df[df["used"]]
    if u["year"].duplicated().any():
        raise ValueError("More than one used official figure for a year")
    return u.set_index("year")[["bcm", "label"]]
