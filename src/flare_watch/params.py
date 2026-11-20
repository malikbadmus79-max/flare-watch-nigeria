"""Fixed assumptions (plan sections 3 and 5) -> data/processed/param_assumptions.csv."""
from __future__ import annotations

import pandas as pd

M3_TO_FT3 = 35.3146667
BCM_TO_MSCF = 35_314_667
BCM_TO_BCF = 35.3147
MMSCF_TO_M3 = 28_316.8466
HHV_BTU_PER_SCF = 1020
CO2E_MT_PER_BCM = 2.569
FEE_LOW, FEE_HIGH = 0.50, 2.00
PRICE_LOW, PRICE_CENTRAL, PRICE_HIGH = 2.13, 3.52, 13.4

VALUE_LABEL = "gross value of gas flared at market prices; not net revenue"
PRICE_LABEL = "at 2025 prices"
FEE_LABEL = "implied flare fee at regulatory rates"  # Amendment A2
CO2E_LABEL = "implied average CO2e per bcm from World Bank 2025 global totals (98% combustion efficiency)"

TRACKER = "World Bank Global Gas Flaring Tracker (June 2026)"
REGS = ("Flare Gas (Prevention of Waste and Pollution) Regulations 2018, as summarised in Templars law-firm "
        "copy (not the official gazette), PDF p.7")


def mmbtu_per_bcm() -> float:
    return BCM_TO_MSCF * 1000 * HHV_BTU_PER_SCF / 1e6


def param_table() -> pd.DataFrame:
    rows = [
        ("bcm_to_million_m3", 1000, "million m3 per bcm", "Definition", "plan s3", "fixed"),
        ("m3_to_ft3", M3_TO_FT3, "ft3 per m3", "Standard conversion", "plan s3", "fixed"),
        ("bcm_to_bcf", BCM_TO_BCF, "billion ft3 per bcm", "Standard conversion (rounded)", "plan s3", "fixed"),
        ("bcm_to_mscf", BCM_TO_MSCF, "Mscf per bcm", "Standard conversion", "plan s3", "fixed"),
        ("mmscf_to_m3", MMSCF_TO_M3, "m3 per MMscf", "Standard conversion (1 MMscf = 10^6 ft3)", "plan s3", "fixed"),
        ("hhv_btu_per_scf", HHV_BTU_PER_SCF, "Btu per scf", f"{TRACKER}, PDF p.19 fn xx", "plan s5.2", "fixed"),
        ("co2e_mt_per_bcm", CO2E_MT_PER_BCM, "MtCO2e per bcm",
         f"{CO2E_LABEL}: 429 MMtCO2e ({TRACKER}, PDF p.19) / 167 bcm (PDF p.17)", "plan s5.1", "fixed"),
        ("flare_fee_low_usd_per_mscf", FEE_LOW, "USD per Mscf",
         f"{REGS}: USD0.50/Mscf where the field produces less than 10,000 barrels of oil a day; {FEE_LABEL}",
         "plan s5.3", "verified (law-firm copy)"),
        ("flare_fee_high_usd_per_mscf", FEE_HIGH, "USD per Mscf",
         f"{REGS}: USD2.00 per 28.317 standard cubic metres (= per Mscf) for producers of 10,000 or more barrels "
         f"of oil a day; {FEE_LABEL}", "plan s5.3", "verified (law-firm copy)"),
        ("price_low_usd_per_mmbtu", PRICE_LOW, "USD per MMBtu",
         "NMDPRA domestic base price effective 1 Apr 2025 (TheCable, https://www.thecable.ng/experts-project-"
         "reduced-gas-cost-for-gencos-as-fg-cuts-domestic-base-price-to-2-1, accessed 2026-11-20); "
         f"{PRICE_LABEL}; {VALUE_LABEL}", "plan s5.2", "fixed"),
        ("price_central_usd_per_mmbtu", PRICE_CENTRAL, "USD per MMBtu",
         f"US Henry Hub 2025 average as used in {TRACKER}, PDF p.19 fn xx; {PRICE_LABEL}; {VALUE_LABEL}",
         "plan s5.2", "fixed"),
        ("price_high_usd_per_mmbtu", PRICE_HIGH, "USD per MMBtu",
         f"Lower of the two conflicting TTF/Asia LNG 2025 figures in {TRACKER} (PDF p.8 fn iv; PDF p.19 fn xx), "
         f"chosen to avoid resolving the inconsistency; {PRICE_LABEL}; {VALUE_LABEL}", "plan s5.2", "fixed"),
        ("persistent_min_years", 12, "years of 14", "Definition", "plan s3", "fixed"),
        ("persistent_sensitivity_low", 10, "years of 14", "Definition", "plan s3", "fixed"),
        ("persistent_sensitivity_high", 14, "years of 14", "Definition", "plan s3", "fixed"),
    ]
    return pd.DataFrame(rows, columns=["parameter", "value", "unit", "source", "plan_ref", "status"])
