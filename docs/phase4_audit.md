# Phase 4 audit: numbers and wording

Date: 2026-11-20. Run by [powerbi/phase4_audit.py](../powerbi/phase4_audit.py) against the open FlareWatch model (DAX, Year = 2025, the slicer default) and the report files. Python values are computed independently in pandas from `data/processed/` and `data/interim/`. Machine-readable: `data/interim/phase4_audit.csv`.

Tolerances: 0.001 bcm (and Mt CO2e); exact for counts; 1 person; 1 USD; 1e-6 for shares and ratios; exact text for sets of names (top-N membership).

## B. Numbers shown on the report: **138 of 138 pass**

### National (22 of 22 pass)

| Visual | Item | Measure / column | Shown | DAX | Python | Pass |
|---|---|---|---|---:|---:|---|
| card Gas flared | 6.60 bcm | Flare Volume Selected Year (bcm) | 6.60 | 6.6008 | 6.6008 | yes |
| card Gas flared | +8.0% vs previous year | YoY Change Selected Year (%) | ▲ 8.0% | 0.0803 | 0.0803 | yes |
| card Implied emissions | 17.0 Mt CO2e | CO2e Selected Year (Mt) | 17.0 | 16.9575 | 16.9575 | yes |
| card Active flare sites | 259 | Active Sites Selected Year | 259 | 259 | 259 | yes |
| card Active flare sites | of 476 (text) | COUNTROWS(dim_site) | 476 | 476 | 476 | yes |
| card Active flare sites | 381 at the 2021 peak (text) | Active Sites, 2021 | 381 | 381 | 381 | yes |
| card Active flare sites | peak year 2021 (text) | year of max Active Sites | 2021 | 2,021 | 2,021 | yes |
| card Persistent sites | 171 | Persistent Sites (12 of 14) | 171 | 171 | 171 | yes |
| card Persistent sites | ≥12 of 14 years (text) | param persistent_min_years | 12 | 12 | 12 | yes |
| map subtitle | 476 recorded flare sites (text) | COUNTROWS(dim_site) | 476 | 476 | 476 | yes |
| map legend | Outside view: 5 sites (text) | dim_site outside lon 4.2-8.7, lat 3.35-6.8 | 5 | 5 | 5 | yes |
| map legend | 1 inland (text) | outside-view sites with location ONSHORE | 1 | 1 | 1 | yes |
| map legend | 4 offshore (text) | outside-view sites with location OFFSHORE | 4 | 4 | 4 | yes |
| Top 6 states | same 6 states (set) | TOPN 6 dim_state by Flare Volume Selected Year |  | Bayelsa,Delta,Edo,Imo,Offshore,Rivers | Bayelsa,Delta,Edo,Imo,Offshore,Rivers | yes |
| Top 6 states | label Offshore | Flare Volume Selected Year (bcm) | 2.57 | 2.5659 | 2.5659 | yes |
| Top 6 states | label Delta | Flare Volume Selected Year (bcm) | 1.29 | 1.2941 | 1.2941 | yes |
| Top 6 states | label Rivers | Flare Volume Selected Year (bcm) | 1.27 | 1.2716 | 1.2716 | yes |
| Top 6 states | label Imo | Flare Volume Selected Year (bcm) | 0.67 | 0.6714 | 0.6714 | yes |
| Top 6 states | label Bayelsa | Flare Volume Selected Year (bcm) | 0.44 | 0.4397 | 0.4397 | yes |
| Top 6 states | label Edo | Flare Volume Selected Year (bcm) | 0.33 | 0.3292 | 0.3292 | yes |
| Active flare sites chart | label 2021 | Active Sites Label Points | 381 | 381 | 381 | yes |
| Active flare sites chart | label 2025 | Active Sites Label Points | 259 | 259 | 259 | yes |

### Sites (17 of 17 pass)

| Visual | Item | Measure / column | Shown | DAX | Python | Pass |
|---|---|---|---|---:|---:|---|
| page subtitle | all 476 recorded flare sites (text) | COUNTROWS(dim_site) | 476 | 476 | 476 | yes |
| All sites table | rows | dim_site | 476 rows | 476 | 476 | yes |
| All sites table | column ay (Active years): rows not matching | dim_site[active_years] | 476 rows | 0 | 0 | yes |
| All sites table | column rv (Recent bcm): rows not matching | dim_site[recent_volume_bcm] | 476 rows | 0 | 0 | yes |
| All sites table | column sy (Selected-year bcm): rows not matching | Flare Volume Selected Year (bcm) | 476 rows | 0 | 0 | yes |
| All sites table | column Persistent: rows not matching | dim_site[persistent] | 476 rows | 0 | 0 | yes |
| Top 10 persistent by recent volume | same 10 sites (set) | TOPN 10 by Recent Volume (bcm) |  | s_3913,s_3926,s_3930,s_3938,s_3939,s_3941,s_3971,s_3978,s... | s_3913,s_3926,s_3930,s_3938,s_3939,s_3941,s_3971,s_3978,s... | yes |
| Top 10 persistent by recent volume | s_3930 | Recent Volume (bcm) | 0.28 | 0.2755 | 0.2755 | yes |
| Top 10 persistent by recent volume | s_3987 | Recent Volume (bcm) | 0.27 | 0.2679 | 0.2679 | yes |
| Top 10 persistent by recent volume | s_3913 | Recent Volume (bcm) | 0.18 | 0.1777 | 0.1777 | yes |
| Top 10 persistent by recent volume | s_3938 | Recent Volume (bcm) | 0.17 | 0.1736 | 0.1736 | yes |
| Top 10 persistent by recent volume | s_3980a | Recent Volume (bcm) | 0.17 | 0.1707 | 0.1707 | yes |
| Top 10 persistent by recent volume | s_3926 | Recent Volume (bcm) | 0.16 | 0.1646 | 0.1646 | yes |
| Top 10 persistent by recent volume | s_3971 | Recent Volume (bcm) | 0.15 | 0.1483 | 0.1483 | yes |
| Top 10 persistent by recent volume | s_3939 | Recent Volume (bcm) | 0.12 | 0.1244 | 0.1244 | yes |
| Top 10 persistent by recent volume | s_3978 | Recent Volume (bcm) | 0.12 | 0.1236 | 0.1236 | yes |
| Top 10 persistent by recent volume | s_3941 | Recent Volume (bcm) | 0.11 | 0.1131 | 0.1131 | yes |

### Operators (28 of 28 pass)

| Visual | Item | Measure / column | Shown | DAX | Python | Pass |
|---|---|---|---|---:|---:|---|
| card Top 10 operators' share | 83.3% | Top 10 Operators Share | 83.3% | 0.8326 | 0.8326 | yes |
| card Unattributed volume | 0.05 bcm | Unattributed Volume (bcm) | 0.05 | 0.0527 | 0.0527 | yes |
| Unattributed bar | label | Flare Volume Selected Year (bcm), Unattributed | 0.05 | 0.0527 | 0.0527 | yes |
| Top 12 operators | same 12 operators (set) | TOPN 12 |  | Chevron,Eni,ExxonMobil,Heirs Energies,NEPL,NNPC Limited,N... | Chevron,Eni,ExxonMobil,Heirs Energies,NEPL,NNPC Limited,N... | yes |
| Top 12 operators | label NEPL | Flare Volume Selected Year (bcm) | 1.51 | 1.5106 | 1.5106 | yes |
| Top 12 operators | label ExxonMobil | Flare Volume Selected Year (bcm) | 1.03 | 1.0282 | 1.0282 | yes |
| Top 12 operators | label Oando Oil | Flare Volume Selected Year (bcm) | 0.55 | 0.5463 | 0.5463 | yes |
| Top 12 operators | label NNPC Limited | Flare Volume Selected Year (bcm) | 0.50 | 0.5046 | 0.5046 | yes |
| Top 12 operators | label Sterling Global | Flare Volume Selected Year (bcm) | 0.49 | 0.4866 | 0.4866 | yes |
| Top 12 operators | label Renaissance Africa Energy | Flare Volume Selected Year (bcm) | 0.49 | 0.4859 | 0.4859 | yes |
| Top 12 operators | label Chevron | Flare Volume Selected Year (bcm) | 0.28 | 0.2762 | 0.2762 | yes |
| Top 12 operators | label Nigeria LNG | Flare Volume Selected Year (bcm) | 0.27 | 0.2673 | 0.2673 | yes |
| Top 12 operators | label Heirs Energies | Flare Volume Selected Year (bcm) | 0.21 | 0.2073 | 0.2073 | yes |
| Top 12 operators | label SEPLAT Energy | Flare Volume Selected Year (bcm) | 0.18 | 0.1832 | 0.1832 | yes |
| Top 12 operators | label TotalEnergies | Flare Volume Selected Year (bcm) | 0.17 | 0.1670 | 0.1670 | yes |
| Top 12 operators | label Eni | Flare Volume Selected Year (bcm) | 0.13 | 0.1347 | 0.1347 | yes |
| Top 10 fields | same 10 fields (set) | TOPN 10 |  | Agu,Cawthorne Channel,Edop,Egbema West,NLNG,Obiafu-Obriko... | Agu,Cawthorne Channel,Edop,Egbema West,NLNG,Obiafu-Obriko... | yes |
| Top 10 fields | label Egbema West | Flare Volume Selected Year (bcm) | 0.37 | 0.3699 | 0.3699 | yes |
| Top 10 fields | label Oso | Flare Volume Selected Year (bcm) | 0.31 | 0.3099 | 0.3099 | yes |
| Top 10 fields | label NLNG | Flare Volume Selected Year (bcm) | 0.27 | 0.2673 | 0.2673 | yes |
| Top 10 fields | label Utapate | Flare Volume Selected Year (bcm) | 0.26 | 0.2615 | 0.2615 | yes |
| Top 10 fields | label Cawthorne Channel | Flare Volume Selected Year (bcm) | 0.22 | 0.2215 | 0.2215 | yes |
| Top 10 fields | label Odidi | Flare Volume Selected Year (bcm) | 0.21 | 0.2124 | 0.2124 | yes |
| Top 10 fields | label Usan | Flare Volume Selected Year (bcm) | 0.21 | 0.2103 | 0.2103 | yes |
| Top 10 fields | label Edop | Flare Volume Selected Year (bcm) | 0.19 | 0.1901 | 0.1901 | yes |
| Top 10 fields | label Obiafu-Obrikom | Flare Volume Selected Year (bcm) | 0.19 | 0.1862 | 0.1862 | yes |
| Top 10 fields | label Agu | Flare Volume Selected Year (bcm) | 0.18 | 0.1795 | 0.1795 | yes |
| Top 5 operators trend | legend: same 5 operators (set) | TOPN 5 by Flare Volume 2012-2025 |  | Chevron,ExxonMobil,NEPL,NNPC Limited,Oando Oil | Chevron,ExxonMobil,NEPL,NNPC Limited,Oando Oil | yes |

### Cost (23 of 23 pass)

| Visual | Item | Measure / column | Shown | DAX | Python | Pass |
|---|---|---|---|---:|---:|---|
| card Implied emissions | 17.0 Mt CO2e | CO2e Selected Year (Mt) | 17.0 | 16.9575 | 16.9575 | yes |
| card Gross value | Gas Value Low (USD) | Gas Value Low (USD) | $506M | 506,444,514.13 | 506,444,514.13 | yes |
| card Gross value | Gas Value Central (USD) | Gas Value Central (USD) | $837M | 836,941,168.89 | 836,941,168.89 | yes |
| card Gross value | Gas Value High (USD) | Gas Value High (USD) | $3,186M | 3,186,082,858.84 | 3,186,082,858.84 | yes |
| card Implied flare fee | Implied Flare Fee Low (USD) | Implied Flare Fee Low (USD) | $117M | 116,552,636.04 | 116,552,636.04 | yes |
| card Implied flare fee | Implied Flare Fee High (USD) | Implied Flare Fee High (USD) | $466M | 466,210,544.17 | 466,210,544.17 | yes |
| card Implied flare fee | $0.50/Mscf (text) | param flare_fee_low_usd_per_mscf | $0.50 | 0.5000 | 0.5000 | yes |
| card Implied flare fee | $2.00/Mscf (text) | param flare_fee_high_usd_per_mscf | $2.00 | 2 | 2 | yes |
| Assumptions table | bcm_to_million_m3 | param_assumptions[value] |  | 1,000 | 1,000 | yes |
| Assumptions table | m3_to_ft3 | param_assumptions[value] |  | 35.3147 | 35.3147 | yes |
| Assumptions table | bcm_to_bcf | param_assumptions[value] |  | 35.3147 | 35.3147 | yes |
| Assumptions table | bcm_to_mscf | param_assumptions[value] |  | 35,314,667 | 35,314,667 | yes |
| Assumptions table | mmscf_to_m3 | param_assumptions[value] |  | 28,316.85 | 28,316.85 | yes |
| Assumptions table | hhv_btu_per_scf | param_assumptions[value] |  | 1,020 | 1,020 | yes |
| Assumptions table | co2e_mt_per_bcm | param_assumptions[value] |  | 2.5690 | 2.5690 | yes |
| Assumptions table | flare_fee_low_usd_per_mscf | param_assumptions[value] |  | 0.5000 | 0.5000 | yes |
| Assumptions table | flare_fee_high_usd_per_mscf | param_assumptions[value] |  | 2 | 2 | yes |
| Assumptions table | price_low_usd_per_mmbtu | param_assumptions[value] |  | 2.1300 | 2.1300 | yes |
| Assumptions table | price_central_usd_per_mmbtu | param_assumptions[value] |  | 3.5200 | 3.5200 | yes |
| Assumptions table | price_high_usd_per_mmbtu | param_assumptions[value] |  | 13.4000 | 13.4000 | yes |
| Assumptions table | persistent_min_years | param_assumptions[value] |  | 12 | 12 | yes |
| Assumptions table | persistent_sensitivity_low | param_assumptions[value] |  | 10 | 10 | yes |
| Assumptions table | persistent_sensitivity_high | param_assumptions[value] |  | 14 | 14 | yes |

### People (23 of 23 pass)

| Visual | Item | Measure / column | Shown | DAX | Python | Pass |
|---|---|---|---|---:|---:|---|
| card 1 | active_2025 2 km | Residents within 2 km (group active_2025) | 1,166,928 | 1,166,927.90 | 1,166,927.90 | yes |
| card 2 | active_2025 5 km | Residents within 5 km (group active_2025) | 5,061,850 | 5,061,850.03 | 5,061,850.03 | yes |
| card 3 | persistent 2 km | Residents within 2 km (group persistent) | 988,745 | 988,745.45 | 988,745.45 | yes |
| card 4 | persistent 5 km | Residents within 5 km (group persistent) | 4,116,774 | 4,116,773.85 | 4,116,773.85 | yes |
| Residents by state (persistent, 5 km) | label Abia | Residents within 5 km of persistent sites | 69,417 | 69,417.39 | 69,417.39 | yes |
| Residents by state (persistent, 5 km) | label Akwa Ibom | Residents within 5 km of persistent sites | 33,896 | 33,896.03 | 33,896.03 | yes |
| Residents by state (persistent, 5 km) | label Bayelsa | Residents within 5 km of persistent sites | 448,002 | 448,001.82 | 448,001.82 | yes |
| Residents by state (persistent, 5 km) | label Delta | Residents within 5 km of persistent sites | 1,327,931 | 1,327,930.85 | 1,327,930.85 | yes |
| Residents by state (persistent, 5 km) | label Edo | Residents within 5 km of persistent sites | 21,156 | 21,156.02 | 21,156.02 | yes |
| Residents by state (persistent, 5 km) | label Imo | Residents within 5 km of persistent sites | 45,724 | 45,723.95 | 45,723.95 | yes |
| Residents by state (persistent, 5 km) | label Offshore | Residents within 5 km of persistent sites | 239,452 | 239,451.93 | 239,451.93 | yes |
| Residents by state (persistent, 5 km) | label Rivers | Residents within 5 km of persistent sites | 2,216,735 | 2,216,734.63 | 2,216,734.63 | yes |
| Top 10 persistent by residents | same 10 sites (set) | TOPN 10 |  | m_62,s_3621,s_3643,s_3664,s_3731,s_3747,s_3749,s_3788,s_3... | m_62,s_3621,s_3643,s_3664,s_3731,s_3747,s_3749,s_3788,s_3... | yes |
| Top 10 persistent by residents | s_3788 | Residents within 5 km (per site) | 572,038 | 572,037.92 | 572,037.92 | yes |
| Top 10 persistent by residents | s_3792 | Residents within 5 km (per site) | 508,195 | 508,195.42 | 508,195.42 | yes |
| Top 10 persistent by residents | s_3806 | Residents within 5 km (per site) | 383,160 | 383,160.48 | 383,160.48 | yes |
| Top 10 persistent by residents | s_3664 | Residents within 5 km (per site) | 272,727 | 272,726.85 | 272,726.85 | yes |
| Top 10 persistent by residents | s_3621 | Residents within 5 km (per site) | 254,795 | 254,795.23 | 254,795.23 | yes |
| Top 10 persistent by residents | s_3747 | Residents within 5 km (per site) | 243,066 | 243,066.16 | 243,066.16 | yes |
| Top 10 persistent by residents | s_3731 | Residents within 5 km (per site) | 200,281 | 200,280.55 | 200,280.55 | yes |
| Top 10 persistent by residents | m_62 | Residents within 5 km (per site) | 193,661 | 193,661.36 | 193,661.36 | yes |
| Top 10 persistent by residents | s_3643 | Residents within 5 km (per site) | 173,188 | 173,188.22 | 173,188.22 | yes |
| Top 10 persistent by residents | s_3749 | Residents within 5 km (per site) | 160,123 | 160,122.54 | 160,122.54 | yes |

### Methods (25 of 25 pass)

| Visual | Item | Measure / column | Shown | DAX | Python | Pass |
|---|---|---|---|---:|---:|---|
| Satellite vs official table | 2021 satellite | Flare Volume (bcm) | 6.54 | 6.5405 | 6.5405 | yes |
| Satellite vs official table | 2021 official | Official Volume (bcm) | 7.15 | 7.1522 | 7.1522 | yes |
| Satellite vs official table | 2021 difference | Satellite − Official (bcm) | -0.61 | -0.6118 | -0.6118 | yes |
| Satellite vs official table | 2021 ratio | Satellite ÷ Official | 0.914 | 0.9145 | 0.9145 | yes |
| Satellite vs official table | 2022 satellite | Flare Volume (bcm) | 5.16 | 5.1638 | 5.1638 | yes |
| Satellite vs official table | 2022 official | Official Volume (bcm) | 5.34 | 5.3361 | 5.3361 | yes |
| Satellite vs official table | 2022 difference | Satellite − Official (bcm) | -0.17 | -0.1723 | -0.1723 | yes |
| Satellite vs official table | 2022 ratio | Satellite ÷ Official | 0.968 | 0.9677 | 0.9677 | yes |
| Satellite vs official table | 2023 satellite | Flare Volume (bcm) | 5.10 | 5.0999 | 5.0999 | yes |
| Satellite vs official table | 2023 official | Official Volume (bcm) | 5.20 | 5.1969 | 5.1969 | yes |
| Satellite vs official table | 2023 difference | Satellite − Official (bcm) | -0.10 | -0.0970 | -0.0970 | yes |
| Satellite vs official table | 2023 ratio | Satellite ÷ Official | 0.981 | 0.9813 | 0.9813 | yes |
| Satellite vs official table | 2024 satellite | Flare Volume (bcm) | 6.11 | 6.1102 | 6.1102 | yes |
| Satellite vs official table | 2024 official | Official Volume (bcm) | 5.46 | 5.4620 | 5.4620 | yes |
| Satellite vs official table | 2024 difference | Satellite − Official (bcm) | +0.65 | 0.6483 | 0.6483 | yes |
| Satellite vs official table | 2024 ratio | Satellite ÷ Official | 1.119 | 1.1187 | 1.1187 | yes |
| Satellite vs official table | 2025 satellite | Flare Volume (bcm) | 6.60 | 6.6008 | 6.6008 | yes |
| Satellite vs official table | 2025 official | Official Volume (bcm) | 5.77 | 5.7738 | 5.7738 | yes |
| Satellite vs official table | 2025 difference | Satellite − Official (bcm) | +0.83 | 0.8270 | 0.8270 | yes |
| Satellite vs official table | 2025 ratio | Satellite ÷ Official | 1.143 | 1.1432 | 1.1432 | yes |
| Validation results | recompute n pass (text) | phase2b_recompute_comparison.csv | recompute (DuckDB, shapely): 68 / 68 | 68 | 68 | yes |
| Validation results | model checks n pass (text) | phase3_validation.csv (built from) | Python: 340 / 340 pass | 340 | 340 | yes |
| Amendments | A1: 203.9 billion scf (text) | official_volumes.csv 2025 value | 203.9 | 203.9000 | 203.9000 | yes |
| Known data issues | K1: 467 km (text) | phase2b_flag_kaduna.json | 467 km | 467 | 467 | yes |
| Known data issues | K2: 33 sites (text) | phase2b_flag_offshore_in_polygon.csv rows | 33 | 33 | 33 | yes |

Notes:

- Chart values that are drawn but not labelled (bars and lines without data labels, axis ticks) are not listed; the measures behind them are checked year by year in docs/phase3_model.md.
- The All sites table (476 rows) is checked column by column; the table shows the number of rows that do not match (expected 0).
- Card values are shown rounded (e.g. 6.60, $506M); the audit compares the unrounded value.

## C. Wording audit (safe-claim rules, plan s7, A2, A3)

Strings checked: 366 (report text boxes, titles, subtitles, buttons, field labels and tooltip names on all 6 pages, plus every measure description). Words searched: owed, unpaid, due, evaded, liable, penalty, health, exposure, on track, off track, forecast, risk, dose, compliance, violation, illegal. Also checked: operator titles carry "as recorded" (or the page does), any 2030 path is called illustrative, every page calls the figures estimates.

Hits needing a fix: **0**. Allowed occurrences (disclaimers in the negative, or the 'formerly penalty' note): 28.

| Page | Visual | Kind | Rule | Text | Verdict |
|---|---|---|---|---|---|
| Cost | cardFeeSub | text | owed | Not amounts owed or paid | allowed (negated disclaimer) |
| Cost | costNote | text | owed | Gross value at market prices, not net revenue. Fees implied at regulatory rates ($0.50/$2.00 per Mscf); not am... | allowed (negated disclaimer) |
| People | peopleNote | text | health | Counts of residents living near flare sites (WorldPop 2025). Proximity only — not a measure of exposure or hea... | allowed (negated disclaimer) |
| People | peopleNote | text | exposure | Counts of residents living near flare sites (WorldPop 2025). Proximity only — not a measure of exposure or hea... | allowed (negated disclaimer) |
| Methods | methods3 | text | penalty | A2: now “implied flare fee at regulatory rates” (formerly “penalty”); values unchanged. | allowed (formerly-penalty note) |
| Methods | methods4 | text | owed | Fees implied at regulatory rates; not amounts owed or paid. Residents near sites = proximity only; no exposure... | allowed (negated disclaimer) |
| Methods | methods4 | text | health | Fees implied at regulatory rates; not amounts owed or paid. Residents near sites = proximity only; no exposure... | allowed (negated disclaimer) |
| Methods | methods4 | text | exposure | Fees implied at regulatory rates; not amounts owed or paid. Residents near sites = proximity only; no exposure... | allowed (negated disclaimer) |
| Methods | methods4 | text | forecast | The 2030 path is illustrative, not a forecast. | allowed (negated disclaimer) |
| model | Illustrative Path 2030 (bcm) | measure description | off track | Illustrative straight-line path to zero by 2030: 2025 national volume x (2030 - year) / 5, for years 2025-2030... | allowed (negated disclaimer) |
| model | Illustrative Path 2030 (bcm) | measure description | forecast | Illustrative straight-line path to zero by 2030: 2025 national volume x (2030 - year) / 5, for years 2025-2030... | allowed (negated disclaimer) |
| model | Implied Flare Fee Low (USD) | measure description | owed | Flare Volume (Mscf) x param flare_fee_low_usd_per_mscf (USD 0.50). Implied flare fee at regulatory rates (Amen... | allowed (negated disclaimer) |
| model | Implied Flare Fee Low (USD) | measure description | unpaid | Flare Volume (Mscf) x param flare_fee_low_usd_per_mscf (USD 0.50). Implied flare fee at regulatory rates (Amen... | allowed (negated disclaimer) |
| model | Implied Flare Fee Low (USD) | measure description | due | Flare Volume (Mscf) x param flare_fee_low_usd_per_mscf (USD 0.50). Implied flare fee at regulatory rates (Amen... | allowed (negated disclaimer) |
| model | Implied Flare Fee High (USD) | measure description | owed | Flare Volume (Mscf) x param flare_fee_high_usd_per_mscf (USD 2.00). Implied flare fee at regulatory rates (Ame... | allowed (negated disclaimer) |
| model | Implied Flare Fee High (USD) | measure description | unpaid | Flare Volume (Mscf) x param flare_fee_high_usd_per_mscf (USD 2.00). Implied flare fee at regulatory rates (Ame... | allowed (negated disclaimer) |
| model | Implied Flare Fee High (USD) | measure description | due | Flare Volume (Mscf) x param flare_fee_high_usd_per_mscf (USD 2.00). Implied flare fee at regulatory rates (Ame... | allowed (negated disclaimer) |
| model | Residents within 2 km | measure description | health | Residents living within 2 km of a flare site (WorldPop 2025), union of buffers so each person is counted once,... | allowed (negated disclaimer) |
| model | Residents within 2 km | measure description | exposure | Residents living within 2 km of a flare site (WorldPop 2025), union of buffers so each person is counted once,... | allowed (negated disclaimer) |
| model | Residents within 5 km | measure description | health | As Residents within 2 km, for 5 km buffers. No exposure or health claim. | allowed (negated disclaimer) |
| model | Residents within 5 km | measure description | exposure | As Residents within 2 km, for 5 km buffers. No exposure or health claim. | allowed (negated disclaimer) |
| model | Residents within 5 km (per site) | measure description | health | Residents living within 5 km of the one site in context (its own buffer; may overlap with neighbouring sites, ... | allowed (negated disclaimer) |
| model | Residents within 5 km (per site) | measure description | exposure | Residents living within 5 km of the one site in context (its own buffer; may overlap with neighbouring sites, ... | allowed (negated disclaimer) |
| model | Residents within 5 km of persistent sites | measure description | health | Residents living within 5 km of persistent sites (WorldPop 2025), union of buffers, from population_groups wit... | allowed (negated disclaimer) |
| model | Residents within 5 km of persistent sites | measure description | exposure | Residents living within 5 km of persistent sites (WorldPop 2025), union of buffers, from population_groups wit... | allowed (negated disclaimer) |
| Operators | opsBars | title | operator without 'as recorded' | Top 12 operators by gas flared, selected year | allowed (page states 'as recorded') |
| Operators | top5Trend | title | operator without 'as recorded' | Top 5 operators, gas flared 2012–2025 | allowed (page states 'as recorded') |
| Operators | unattrBar | title | operator without 'as recorded' | Unattributed (no operator recorded), selected year | allowed (page states 'as recorded') |
