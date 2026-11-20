# Phase 1: Analysis plan

Status: **FROZEN v1.0 — 2026-11-20**

The SHA-256 is recorded in [plan_freeze.md](plan_freeze.md). Any change must be logged in [amendments.md](amendments.md) before it is applied (section 10).

Date drafted: 2026-11-20.
Inputs read: [phase0_results.md](phase0_results.md), `data/interim/phase0_report.json`, and the two PDFs in `data/raw/docs/` (listed in `data/interim/phase0_sources.csv` with size and SHA-256).

This plan sets out questions, definitions, rules and outputs. It contains **no results**. The only numbers it quotes from the data were already reported in Phase 0.

### Citation convention for the PDFs

- **Method** = `World-Bank-s-Global-Gas-Flaring-Reduction-Partnership-Gas-Flaring-Estimates-Methodology-for-Determining-the-Gas-Flare-Volumes-from-Satellite-Data.pdf` (6 pages). Cited as "Method p.N".
- **Tracker** = `Global-Gas-FlaringTracker-June-23-2026.pdf` (34 PDF pages). Each PDF page is a two-page spread. Cited as "Tracker PDF p.N (printed pp. a–b)".

### Important note on the methodology PDF

The Method note describes the **earlier** calibration: country totals from Cedigaz for 2013–2017, with "Satellite flare volume estimate = 0.0281 x VIIRS radiant heat" (Method p.5). The Tracker says the data now uses a methodology developed in 2025, with "new, rigorously measured calibration data" (Tracker PDF p.17, printed pp. 32–33). It also says "This report includes revised data for years going back to 2012" (Tracker PDF p.26, printed pp. 50–51).

So the Method note does **not** describe how the 2026 release was produced. The Tracker points to "A more comprehensive description of the current methodology … on the GFMR website" (Tracker PDF p.26, fn xxvi) and cites Zhizhin et al. 2026 (*Remote Sensing* 18, 314) and Zhizhin et al. 2025 (*Energies* 18) (Tracker PDF p.34, ref 40). Neither paper is in `data/raw`. Obtaining them is an open item for Phase 2 (manual download).

---

## 1. Aim and context

- **Aim:** describe gas flaring in Nigeria from 2012 to 2025, using the World Bank GFMR satellite estimates (NOAA, Payne Institute / Colorado School of Mines). The analysis is organised by site, field, operator (as recorded), year and nearby population, and is delivered as a reproducible Power BI monitor.
- **Context 1:** NOSDRA's public gas-flare tracker has not been updated since May 2025. *[to be cited in Phase 4]*
- **Context 2:** NUPRC has a target of zero routine flaring by 2030. *[to be cited in Phase 4]*
- **Context 3:** the Tracker names Nigeria as one of nine countries that together produced 83% of global flaring in 2025 (Tracker PDF p.18, printed pp. 34–35). *[source in hand]*
- **What the project is:** descriptive. All volumes are satellite **estimates**, not site measurements: "Data presented here are estimates and do not reflect site measurements" (Tracker PDF p.17, printed pp. 32–33).

## 2. Research questions

| RQ | Question | Main outputs |
|---|---|---|
| RQ1 | **National trend, 2012–2025.** How has estimated national flaring changed? What would an **illustrative** straight line from the 2025 level to zero in 2030 look like? | Annual national bcm, with the illustrative 2025→2030 path. The path is a linear interpolation from the 2025 value to 0 in 2030. It is always labelled "illustrative", because satellites measure all flaring, not only routine flaring. The Tracker itself uses total volume as a proxy for routine flaring ("as a proxy, estimated total flare volumes … have been used", Tracker PDF p.9, printed pp. 16–17). |
| RQ2 | **Persistence.** Which sites flare year after year? | Count and list of persistent sites (section 3), with the 10/14 and 14/14 sensitivities. Number of active years per site. |
| RQ3 | **Concentration.** What share of national volume comes from the largest sites, fields and operators? | Share of national volume from the top 10 sites, top 10 fields and top 10 operators: each year, and for recent volume (2023–2025). Operators are shown "as recorded in the World Bank 2026 release". "Unattributed" is shown as its own row but is not ranked as an operator. |
| RQ4 | **Implied costs.** What are the CO2e emissions, the value of the gas burned, and the penalties implied at statutory NUPRC rates? | National and site-level CO2e (only if a sourced factor exists; see section 5), gas value as a low/central/high range, and implied penalty as a low–high range. |
| RQ5 | **People nearby.** How many residents live within 2 km and 5 km of active and persistent flare sites? | Residents within 2 km and 5 km of (a) sites active in 2025 and (b) persistent sites. National totals count each person once (a union of buffers). Site-level counts may overlap and are labelled as such. Totals are also given by state. |
| RQ6 | **Satellite vs official.** How do national satellite totals compare with official NUPRC/NNPC figures (via BudgIT where needed)? | Year-by-year table and chart of satellite vs official volumes, the absolute gap and the ratio. The gap is **described, not explained**. |

## 3. Definitions (fixed)

| Term | Definition |
|---|---|
| Active site-year | A site-year with `BCM > 0`. |
| Zero rows | A site-year with `BCM = 0` means **"no flaring detected"** that year. Neither PDF says otherwise (see section 4, Q4). It does **not** mean "no emissions": the Tracker says periods with no detections can indicate "potential unlit flare situations" (Tracker PDF p.27, printed pp. 52–53). |
| Persistent site | Active in **at least 12 of the 14 years** (2012–2025). Sensitivity runs use 10 of 14 and 14 of 14. |
| Recent volume | Mean BCM per site over **2023, 2024 and 2025**. Zero years count as 0 in the mean. |
| Active in 2025 | `BCM > 0` in 2025. Used for RQ5 group (a). |
| Units | Volumes are shown in **bcm** and **million m3** (1 bcm = 1,000 million m3). For gas value and penalties: 1 bcm = 35.3147 billion cubic feet = **35,314,667 Mscf**, from 1 m3 = 35.3146667 ft3. The Tracker rounds this to 35.315 (Tracker PDF p.19, fn xx); the difference is below 0.001% and is noted, not adjusted. `MMSCFD` is carried as given in the source file. |

## 4. Data decisions (answers to the Phase 0 open questions)

**Q1. The 57 sites with no operator, field or field type.**
- Keep them in every total, labelled **"Unattributed"**.
- Do not guess operators from location in the main results.
- A location-based match may appear only as a separately labelled exploratory cross-check, if it is added by amendment.

**Q2. Operator names.**
- Trim spaces and fix case only. For example, "Renaissance Africa Energy " (with a trailing space) becomes "Renaissance Africa Energy".
- Do **not** merge near-variants such as "Newcross EP" and "Newcross Petroleum" unless the World Bank or GEM shows they are the same entity.
- Log every change (raw value, clean value, rule, evidence) in `data/interim/operator_cleaning.csv`.
- The GEM spelling "MoniPulo" vs the World Bank "Moni Pulo" is a GEM-matching issue (Q7). It does not change the World Bank operator name.

**Q3. Operator over time.**
- Use the operator recorded in the 2026 release for **all** years, labelled **"operator as recorded (2026 release)"**. Every operator trend carries this caveat.
- **What the PDFs say:** neither PDF says how operators are assigned to flare sites, or whether the operator is the one at the release date or in each year. **Not answered.**
- Related facts:
  - The Tracker says the new method "aggregates positional data for each flare detection nightly from 2012 to 2025" into "a multi-year catalog that assigns a single, consistent location to each flare" (Tracker PDF p.27, printed pp. 52–53). This fits the Phase 0 finding that each site has one fixed set of attributes in every year. It says nothing about operators.
  - The only mention of "operator data" concerns calibration: "The OGCI contributed this operator data" (Tracker PDF p.28, printed pp. 54–55). It is not about attribution.

**Q4. Zero rows.**
- Treated as "no flaring detected", as defined in section 3.
- **What the PDFs say:** neither PDF defines zero values in the site file. **Not answered explicitly.**
- Related facts:
  - The multi-year catalog (Tracker PDF p.27, quoted under Q3) explains why every site appears in every year: one catalogue of sites is used for 2012–2025. A zero is therefore most plausibly a catalogued site with no detections that year. This is an inference, not a documented statement.
  - The Tracker describes "Routine flaring with periods of no flare detections, i.e., potential unlit flare situations" (Tracker PDF p.27, Figure 27). So a zero must never be described as "no emissions" or "stopped".

**Q5. Flare Level (Small / Medium / Large).**
- Report it as given by the World Bank. Do not build our own size bands.
- **What the PDFs say:** neither PDF defines the cut-offs. **Not answered.**
- The Tracker only speaks generally about "large flares" and "small flares" (e.g. Tracker PDF p.17 and p.28). It does not give thresholds.
- Flare Level is shown as a site-year attribute (it changes for 87 sites). Since the cut-offs are undocumented, it is never used to rank sites.

**Q6. How country totals are built.**
- Country totals are the sum of the site rows, so they are **not** an independent check. Independent validation uses official figures (RQ6).
- **What the PDFs say:** this is partly answered.
  - Method p.2: "As the geographical position of each flare is detected by the satellite, the flare volumes can be precisely allocated to the country in which the flaring takes place." Country estimates are therefore built from flare-level estimates, which matches the Phase 0 floating-point match. (This describes the earlier method; the Tracker does not say this changed.)
  - Tracker PDF p.9 (printed pp. 16–17), and repeated elsewhere: "upstream oil and gas facilities include oil and gas production and processing facilities, and facilities that liquefy natural gas". So the national total covers upstream flaring only, not refineries or other downstream sites.
  - Calibration (Method p.5) once used country-level Cedigaz data, so the old country totals were not fully independent of reported figures. The new calibration uses metered test-flare data instead (Tracker PDF p.28).

**Q7. GEM.**
- Use GEM only as a cross-check of field status and coordinates.
- Name matching is improved by explicit rules in Phase 2, for example stripping bracketed qualifiers ("Akpo (PSC)" → "Akpo"). Each rule is logged with the number of names it affects.
- No fuzzy merges without a logged rule. GEM does not change any World Bank volume or operator.

**Q8. Population.**
- Source: WorldPop gridded population for Nigeria (CC BY 4.0). Use one year; the most recent available year is chosen and recorded in Phase 2.
- Buffers of 2 km and 5 km around each site's lat/lon, computed in a metric projection (e.g. UTM 32N), not in degrees.
- State and LGA from an open boundary file (geoBoundaries or GRID3; the choice and licence are recorded in Phase 2).
- **Offshore sites:** sites with `Location = OFFSHORE` get `state = "Offshore"` and `lga = "Offshore"`. They are not assigned to a coastal state.
- **Land-based residents only:** population counts include only residents on land inside each buffer. WorldPop has no offshore population, so offshore buffers count only the part that reaches land, if any.
- The user downloads these files manually in Phase 2. Their hashes are added to `phase0_sources.csv`, or a Phase 2 equivalent.

**Q10. Field name "\*".**
- The one site whose Field name is recorded as `*` is treated as an **unattributed field**. Its field is shown as "Unattributed", and its operator and field type are kept as recorded.
- Log the change (raw value, clean value, rule) in `data/interim/field_cleaning.csv`. That file follows the same format as `operator_cleaning.csv` and records all field-name changes.

**Q9. Licence.**
- The World Bank data files state no explicit licence. Raw files are not redistributed (`data/raw/*.xlsx` is gitignored).
- Publish only derived tables and code, with the attribution "NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR" and the World Bank disclaimer.
- The Tracker report itself states that it "may be reproduced, in whole or in part, for noncommercial purposes as long as full attribution to this work is given" (Tracker PDF p.2). This covers the report, not the data files.
- `.gitignore` covers both `data/raw/*.xlsx` and `data/raw/docs/`, so the source PDFs are not redistributed either.

## 5. Calculations and assumptions

Every assumption below is recorded in `data/interim/assumptions.csv` in Phase 2. Each row holds the parameter, the value, the source, the source page or URL, the access date and the sensitivity range.

### 5.1 CO2e

- **The World Bank states no CO2e factor per bcm.** The Tracker gives only global totals and the assumption behind them:
  - Numerator: "Global flaring in 2025 resulted in total emissions of 429 MMtCO2e. Of this, about 50 MMtCO2e was in the form of methane" (Tracker PDF p.19, printed pp. 36–37).
  - Denominator: "gas flaring at upstream oil and gas facilities increased from 157 bcm in 2024 to 167 bcm in 2025" (Tracker PDF p.17, printed pp. 32–33). The same 167 bcm figure appears in the Executive Summary (PDF p.7, printed pp. 12–13) and Key Findings (PDF p.11, printed pp. 20–21).
  - Assumption: "the conventional assumption is used that flares are 98 percent efficient at burning methane" (Tracker PDF p.19, fn xix; also p.10, fn ix).
- **Central factor (adopted):** 429 MMtCO2e ÷ 167 bcm = **2.569 MtCO2e per bcm** (2.568862…; both inputs are rounded in the source, so the factor is good to about three significant figures).
  - Label it everywhere as **"implied average CO2e per bcm from World Bank 2025 global totals (98% combustion efficiency)"**.
  - It is a global average. It does not reflect Nigerian gas composition or flare efficiency, and it includes the methane slip implied by 98% combustion efficiency.
  - CO2e (Mt) = bcm × 2.569. The same factor is applied to every year.
- **Replacement:** if Phase 2 finds a factor that the World Bank or GFMR states directly (e.g. on the current methodology page or in Zhizhin et al. 2025/2026), it may replace this one **by amendment**.
- **Sensitivity:** the Tracker's lower "effective" destruction efficiency of 94%, under which methane emissions "would be triple the conventional estimates" (Tracker PDF p.10). This is shown only as a scenario: methane share × 3, using the global ≈50/429 split. It is labelled as a scenario.

### 5.2 Value of gas burned

- **Energy conversion** (from the Tracker, PDF p.19, fn xx; PDF p.8, fn iv): higher heating value **1,020 Btu/scf** and **1 m3 = 35.315 scf**.
  - MMBtu = bcm × 35,314,667 Mscf × 1,000 scf/Mscf × 1,020 Btu/scf ÷ 10⁶.
- **Price range:** USD per MMBtu, as low / central / high. Sources and dates are recorded in Phase 2.
  - Benchmark prices the Tracker uses for 2025: US Henry Hub **US$3.52/MMBtu**, EU TTF and Asia JKM.
  - The Tracker's footnotes disagree on the last two. PDF p.19, fn xx gives TTF **13.8** and Asia **13.4**. PDF p.8, fn iv gives TTF **13.4** and Asia **13.8**. This is recorded as a source inconsistency and is not resolved by us.
  - The Tracker maps each country to one benchmark but does not say which one Nigeria uses.
  - A Nigeria-relevant central price (e.g. a domestic or regulated gas price) is to be sourced in Phase 2.
- **Wording:** the result is "gross value of gas flared at market prices". The Tracker notes that such a figure "does not represent net revenue" (Tracker PDF p.16, fn xv). The same caveat applies here.

### 5.3 Implied penalty

- **Rates:** Flare Gas (Prevention of Waste and Pollution) Regulations 2018, now administered by NUPRC.
  - **Low: US$0.50 per Mscf.**
  - **High: US$2.00 per Mscf.**
  - In the Regulations the rate depends on the producer's output, and output is not in the satellite data, so both rates are shown as a range.
  - The rates, the tier basis and the citation are to be checked against the gazetted text in Phase 2 and cited in Phase 4.
- **Formula:** penalty = satellite volume (Mscf) × rate. It is applied to all satellite volume, which includes non-routine flaring, and this is stated next to every figure.
- **Wording:** always **"implied at statutory rates"**. Never "owed", "unpaid", "due" or "evaded".

## 6. Validation plan

1. **Official vs satellite (RQ6).**
   - Compare national satellite totals with official NUPRC/NNPC flared volumes (via BudgIT where needed) for **at least 2021–2025**, and for more years if available.
   - Record the source, table or page, original unit and conversion for every official figure.
   - The gap is reported, not explained.
2. **GEM cross-check.** For the top sites in each priority list and in RQ3, check GEM field status (operating / mothballed / etc.) and whether the coordinates are plausible. Mismatches are listed, not corrected.
3. **Independent recompute.**
   - The key totals are computed twice, by separate code paths: a pandas pipeline and a second implementation (e.g. DuckDB SQL or a separate script). The totals are national bcm by year, persistent-site count, top-10 shares, and the RQ5 population totals.
   - Tolerance: 0.001 bcm for volumes and an exact match for counts.
   - Power BI measures are checked against the same values.
4. **Traceability.** Every number on the dashboard maps to a file and column (or a measure defined over them) in `data/processed/`, listed in a trace table on the Methods/Validation page. A test fails if any dashboard headline figure has no trace entry.
5. **Carried over from Phase 0.** The site-sum vs country-file check is kept as a regression test. It confirms data integrity, not independence (Q6).

## 7. Safe-claim rules

| May say | May not say |
|---|---|
| "Satellite estimates show …"; "estimated flaring" | Any claim that a volume is measured or exact |
| "Operator as recorded (2026 release)" | That an operator flared in a year it may not have operated the site; any statement of company conduct or wrongdoing |
| "Illustrative straight-line path to zero by 2030" | That Nigeria is "on track" or "off track" for routine-flaring targets, or that the path is a forecast |
| "Penalties implied at statutory rates" (low–high) | "Owed", "unpaid", "due", "evaded", "liable", or any compliance finding |
| (nothing on penalties collected) | Any comparison of implied penalties with penalties collected, paid or remitted (e.g. NUPRC, NNPC or BudgIT penalty figures), or anything that implies a shortfall |
| "Residents living within 2 km / 5 km of a flare site" | Any health effect, exposure, dose or risk claim |
| "No flaring detected" (for BCM = 0) | "Stopped flaring", "no emissions" |
| "Satellite and official figures differ by X" | Why they differ, or that either is wrong or misreported |
| "Flare Level as classified by the World Bank" | Our own size categories |
| "Unattributed sites" | Guessed operators for unattributed sites |

Every page carries the attribution "NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR" and a note that the figures are estimates.

## 8. Priority lists (rules fixed; no composite score)

- **(a) Top 10 persistent sites by recent volume:** persistent sites (≥12/14) ranked by recent volume (mean BCM 2023–2025), largest first.
- **(b) Top 10 persistent sites by residents within 5 km:** persistent sites ranked by WorldPop residents within 5 km of the site, largest first. Counts are per site, so they may overlap between neighbouring sites, and this is stated.
- **Ties:** broken by ascending `site_id`.
- The two lists are shown **separately**. They are not combined, weighted or scored, and they are not called "worst" or "most harmful".
- Sensitivity: membership of each list under the 10/14 and 14/14 persistence rules is reported alongside.

## 9. Dashboard design spec (Power BI)

### 9.1 Data model (star schema)

| Table | Grain | Columns |
|---|---|---|
| `fact_site_year` | site × year | `site_id`, `year`, `bcm`, `mmscfd`, `flare_level`, `active` (BCM > 0) |
| `dim_site` | site | `site_id`, `lat`, `lon`, `field`, `operator_clean`, `field_type`, `location`, `state`, `lga`, `pop_2km`, `pop_5km`, `persistent` (12/14), `persistent_10`, `persistent_14`, `active_years`, `recent_volume_bcm` |
| `dim_year` | year | `year`, `is_recent` (2023–2025), `official_bcm` (RQ6; blank where none) |
| `dim_operator` | operator | `operator_clean`, `operator_raw_variants`, `is_unattributed` |
| `dim_state` | state | `state`, `pop_total` (optional, for context only). Includes an **"Offshore"** member for `Location = OFFSHORE` sites (no population). |
| `param_assumptions` | parameter | Price low/central/high, penalty rates, CO2e factor (blank until sourced), conversion constants |
| `trace` | dashboard figure | `figure_id`, `page`, `measure_or_column`, `source_file` |

Relationships: `fact_site_year` → `dim_site` (site_id), `dim_year` (year). `dim_site` → `dim_operator` (operator_clean), `dim_state` (state). All are single-direction, one-to-many.

### 9.2 Pages

**Build order:**
- **Core (build first):** pages 1, 2, 3 and 6.
- **Build after core pages work:** pages 4 and 5.

1. **National trend and 2030 path** — *Core (build first)*: annual bcm 2012–2025 with the illustrative path, the active-site count by year, and the RQ6 overlay as a toggle.
2. **Site explorer** — *Core (build first)*: map of sites (sized by volume, filtered by year, persistence and field type), with drill-through to a site page showing its year series, attributes and population.
3. **Operators and fields** — *Core (build first)*: concentration (top-10 shares) and operator/field tables, with the "as recorded (2026 release)" caveat banner.
4. **Cost of flaring** — *Build after core pages work*: CO2e (implied average factor), gas value range and implied penalty range, each with its assumption visible.
5. **People near flares** — *Build after core pages work*: residents within 2 km and 5 km of active-2025 and persistent sites, by state, and priority list (b).
6. **Methods and validation** — *Core (build first)*: sources and hashes, definitions, safe-claim notes, satellite vs official table, independent-recompute results, the trace table, and the amendments log summary.

### 9.3 DAX measures to build (names and definitions only)

| Measure | Plain-English definition |
|---|---|
| `Flare Volume (bcm)` | Sum of bcm in the current filter context. |
| `Flare Volume (million m3)` | Flare Volume (bcm) × 1,000. |
| `Flare Volume (Mscf)` | Flare Volume (bcm) × 35,314,667. |
| `Flare Volume (bcf)` | Flare Volume (bcm) × 35.3147. |
| `National Volume (bcm)` | Flare Volume ignoring all site, operator, field and state filters (year filter kept). |
| `Share of National` | Flare Volume ÷ National Volume. |
| `Active Sites` | Count of distinct sites with bcm > 0. |
| `Persistent Sites` | Count of sites flagged persistent under the selected rule (12/14 by default; 10/14 or 14/14 by slicer). |
| `Active Years` | Number of years with bcm > 0 for the site in context. |
| `Recent Volume (bcm)` | Mean annual bcm over 2023–2025 for the selection. |
| `YoY Change (bcm)` | Volume in the selected year minus the previous year. |
| `YoY Change (%)` | YoY Change ÷ previous year's volume. |
| `Top 10 Sites Share` | Share of national volume from the 10 largest sites in context (ties broken by site_id). |
| `Top 10 Fields Share` | The same for fields. |
| `Top 10 Operators Share` | The same for operators, excluding "Unattributed" from the ranking. |
| `Unattributed Volume (bcm)` | Volume from sites with no recorded operator. |
| `Illustrative Path 2030 (bcm)` | For 2025–2030: a straight line from the 2025 national volume to 0 in 2030; blank for other years. |
| `CO2e (Mt)` | Flare Volume (bcm) × 2.569, the implied average CO2e per bcm from World Bank 2025 global totals (98% combustion efficiency); factor held in `param_assumptions`. |
| `Gas Energy (MMBtu)` | Volume in Mscf × 1,000 × 1,020 ÷ 10⁶. |
| `Gas Value Low / Central / High (USD)` | Gas Energy × the low, central and high price. |
| `Implied Penalty Low (USD)` | Volume in Mscf × US$0.50. |
| `Implied Penalty High (USD)` | Volume in Mscf × US$2.00. |
| `Residents within 2 km` / `Residents within 5 km` | Residents in the union of buffers of the selected sites (each person counted once), taken from precomputed tables. |
| `Residents within 5 km (per site)` | Residents in one site's own buffer (may overlap with neighbours). |
| `Official Volume (bcm)` | Official NUPRC/NNPC volume for the year, converted to bcm. |
| `Satellite − Official (bcm)` | National Volume minus Official Volume. |
| `Satellite ÷ Official` | National Volume divided by Official Volume. |

The union-of-buffers population totals cannot be added up from per-site values. They are precomputed in Python for each group the dashboard shows (active-2025, persistent, by state) and loaded as a small table.

## 10. Amendments

- After the plan is frozen (hash recorded), **any** change to a definition, rule, source or output is first logged in [amendments.md](amendments.md) with its date, reason and effect, and then applied.
- Amendments are numbered and never deleted. Results produced before an amendment are labelled with the plan version they used.

## Open items carried into Phase 2

1. Obtain the current GFMR methodology description and/or Zhizhin et al. 2025/2026 (Q3–Q6). Check whether either states a CO2e factor that should replace the implied average (5.1), by amendment.
2. Source the price range (5.2). Settle the TTF/JKM footnote inconsistency by using a primary price source.
3. Verify the penalty rates and tier basis against the gazetted 2018 Regulations (5.3).
4. Download WorldPop and the boundary file, and record hashes and licences (Q8).
5. Collect official NUPRC/NNPC/BudgIT volumes for 2021–2025 or more (RQ6).
6. Done in Phase 1: `data/raw/docs/` was added to `.gitignore`, and `phase0_check.py` now lists all five raw sources (three data files and two PDFs) in `phase0_sources.csv`.
