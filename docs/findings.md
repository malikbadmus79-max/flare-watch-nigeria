# Flare Watch Nigeria: findings

**What this is:** a plain-English summary of what the data shows for the six research questions in the [analysis plan](analysis_plan.md).
- Every number here has been checked twice: by the independent recompute (68/68) and by the Power BI measure checks (340/340). See [phase2b_validation.md](phase2b_validation.md), [phase3_model.md](phase3_model.md) and [phase4_audit.md](phase4_audit.md).
- This document contains no new analysis.
- Volumes are **satellite estimates** (World Bank GFMR; NOAA, Payne Institute / Colorado School of Mines; 2026 release) in billion cubic metres (bcm).

## RQ1: National trend, 2012–2025

- Estimated flaring was **9.28 bcm in 2012** and **6.60 bcm in 2025**, a change of **−28.8%**.
- The lowest year was **2023, at 5.10 bcm**. Estimated flaring then rose in 2024 (6.11 bcm) and 2025.
  - 2025 was **+29.4%** above 2023 and **+8.0%** above 2024.
- An **illustrative** straight line from the 2025 level to zero in 2030 falls by 1.32 bcm a year.
  - It is not a forecast.
  - It says nothing about whether any target will be met.
  - Satellites measure all flaring, not only routine flaring.
  - NUPRC has stated a target to end routine flaring by 2030 ([context](sources_context.md)).

## RQ2: Persistence

- **476** flare sites are recorded for Nigeria between 2012 and 2025.
- In 2025, flaring was detected at **259** of them. The number of active sites peaked at **381 in 2021**.
- **171** sites show estimated flaring in at least 12 of the 14 years (the main rule).
  - Under the sensitivity rules the count is **218** (at least 10 of 14) and **133** (all 14 years).

## RQ3: Concentration (2025)

- **Top 10 sites:** 31.5% of estimated national volume.
- **Top 10 fields:** 36.5%. The fields are as recorded.
- **Top 10 operators:** 83.3%.
  - Operators are as recorded in the World Bank 2026 release and applied to all years. This is not a statement about any company's conduct.
  - Sites with no recorded operator ("Unattributed", 0.05 bcm in 2025) are excluded from the operator ranking.
- **By state:** the largest 2025 volumes were Offshore (2.57 bcm), Delta (1.29), Rivers (1.27), Imo (0.67), Bayelsa (0.44) and Edo (0.33).

## RQ4: What the flared gas represents (2025)

- **Implied emissions:** about **17.0 Mt CO2e**. This uses the implied average CO2e per bcm from the World Bank's 2025 global totals (98% combustion efficiency). It is a global average, not a Nigeria-specific factor.
- **Gross value of the gas flared at market prices (at 2025 prices):** **$506 million** (low), **$837 million** (central) and **$3,186 million** (high). This is not net revenue.
- **Implied flare fee at regulatory rates:**
  - Range: **$117 million** (US$0.50 per Mscf) to **$466 million** (US$2.00 per Mscf).
  - It is applied to all satellite volume, including non-routine flaring.
  - These are not amounts owed or paid, and they are not compared with any fees collected.

## RQ5: People living near flare sites (WorldPop 2025)

| Sites | Within 2 km | Within 5 km |
|---|---:|---:|
| Sites with flaring detected in 2025 | 1,166,928 | 5,061,850 |
| Persistent sites | 988,745 | 4,116,774 |

- Each person is counted once (a union of buffers).
- These are counts of residents living near flare sites. They are not a measure of exposure or health effects.
- **By state:** within 5 km of persistent sites, the largest counts are in Rivers (2,216,735) and Delta (1,327,931).

## RQ6: Satellite estimates vs official figures

| Year | Satellite (bcm) | Official (bcm) | Difference | Ratio |
|---|---:|---:|---:|---:|
| 2021 | 6.54 | 7.15 | −0.61 | 0.914 |
| 2022 | 5.16 | 5.34 | −0.17 | 0.968 |
| 2023 | 5.10 | 5.20 | −0.10 | 0.981 |
| 2024 | 6.11 | 5.46 | +0.65 | 1.119 |
| 2025 | 6.60 | 5.77 | +0.83 | 1.143 |

- **Sources for the official figures:** 2021–2024 are NUPRC via BudgIT; 2025 is the NUPRC figure as reported in the press (Amendment A1).
- **The pattern:** satellite estimates were below the official figures in 2021–2023 and above them in 2024–2025. The differences are reported, not explained.

## What this study cannot claim

- **Measured volumes:** all volumes are satellite estimates.
- **Company conduct:** operators are as recorded (World Bank 2026 release) and applied to all years. Nothing here is a statement about any company's conduct, or about which company operated a site in a given year.
- **Compliance or money owed:** nothing here says flare fees are owed, unpaid or evaded. The implied flare fees are not compared with amounts collected.
- **Health:** nothing here describes exposure, dose, risk or health effects. Resident counts show proximity only.
- **The 2030 path:** nothing here says Nigeria is on or off track. The path is not a forecast.
- **Satellite vs official gaps:** nothing here explains why the two series differ, or says that either is wrong.
- **Sites showing zero:** a site at zero means "no flaring detected", not "stopped flaring" or "no emissions".

## Known data issues (kept as recorded)

- **K1:** site s_38320 lies in Kaduna (Chikun), far from the Niger Delta. It is recorded as field "Obi Ayima" and was active only in 2025. The only other site with that field name is in Delta, 467 km away.
- **K2:** 33 sites labelled OFFSHORE fall inside a state's land boundary. They stay "Offshore", as the plan requires.
- **Model fix (Phase 4):** a dashboard measure for residents near sites returned the wrong group for states with no persistent site (Kaduna). It was fixed and checked against Python. The numbers above were not affected.
