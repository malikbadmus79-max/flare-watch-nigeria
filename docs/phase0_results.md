# Phase 0 results: setup and data check

Date: 2026-11-20. Script: `src/flare_watch/phase0_check.py`. Tests: `tests/test_phase0.py`.
Full machine-readable output: `data/interim/phase0_report.json`.

This document records facts only. It contains no analysis and draws no conclusions.

## 1. What was done

1. Created the project structure:
   - folders: `data/raw`, `data/interim`, `data/processed`, `docs`, `src/flare_watch`, `tests`, `powerbi`, `figures`;
   - files: `README.md`, `.gitignore`, `requirements.txt` and `pytest.ini`.
2. Created `.venv` (Python 3.12.10) and installed the requirements: pandas 3.1.1, openpyxl 3.1.5 and pytest 9.2.0.
3. Copied three raw files from `Downloads` into `data/raw`. The site file was renamed to remove " (1)".
   - The originals were not changed.
   - Each copy's SHA-256 matches its original.
4. Ran `phase0_check.py`, then the tests: 3 of 3 passed.

## 2. Sources (`data/interim/phase0_sources.csv`)

| File | Size (bytes) | SHA-256 |
|---|---:|---|
| Flare-Volume-Estimates-by-individual-Flare-Location-2012-2025.xlsx | 47,115,914 | 8b6052d23c09584d5964d6549026961b5ee8529b9b882edb4073fd6e9bc40354 |
| Flare-volume-and-intensity-estimates-2012-2025.xlsx | 78,034 | dae0c289b3539d29c210676d5a0eea6904b10d3e9baac81c1100717c7b3aa405 |
| Global-Oil-and-Gas-Extraction-Tracker-March-2026.xlsx | 5,393,993 | 10ed7bc007e47895c2f387449365c20d0a87679cb8c69be678d0cc60df4d1aa5 |

- **World Bank site and country files**
  - Source: https://www.worldbank.org/en/programs/gasflaringreduction/global-flaring-data
  - Attribution: NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR.
  - Licence: none stated explicitly; the World Bank disclaimer applies.
- **GEM tracker**
  - Source: https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker
  - Licence: CC BY 4.0.

## 3. World Bank site file: Nigeria (sheet `Dashboard_file`)

### 3.1 Columns, size and coverage

The sheet has 383,544 rows across all countries and 13 columns, exactly as expected:

`id, lat, lon, Country, BCM, MMSCFD, Year, Field type, Operator, Field name, Location, Flare Level, Flaring Vol (million m3)`

The Nigeria rows are saved to `data/interim/ng_flare_sites_long.csv`.

| Item | Value |
|---|---:|
| Rows | 6,664 |
| Unique site ids | 476 |
| Years covered | 2012–2025 (14) |
| Rows per year | 476 in every year (balanced panel) |
| Rows with BCM = 0 | 2,475 |
| Rows with BCM missing | 0 |
| Sites with BCM = 0 in all 14 years | 13 |
| Sites with BCM > 0 in all 14 years | 133 |
| Maximum \|BCM − Flaring Vol (million m3)/1000\| | 5.6 × 10⁻¹⁷ |

### 3.2 Missing values

"Missing" means empty, NaN or the literal text "NA".

| Column | Rows missing | Sites missing | Literal "NA" |
|---|---:|---:|---:|
| Operator | 798 | 57 | 0 |
| Field name | 798 | 57 | 0 |
| Field type | 798 | 57 | 0 |

### 3.3 Counts by category

| Field type | Rows | Sites |
|---|---:|---:|
| OIL | 5,096 | 364 |
| GAS | 714 | 51 |
| LNG | 56 | 4 |
| missing | 798 | 57 |

| Location | Rows | Sites |
|---|---:|---:|
| ONSHORE | 5,222 | 373 |
| OFFSHORE | 1,442 | 103 |

| Flare Level | Rows | Sites with this level in at least one year |
|---|---:|---:|
| Small | 6,120 | 465 |
| Medium | 538 | 96 |
| Large | 6 | 2 |

The following attributes are the same for each site in every year: Field type, Operator, Field name, Location, lat and lon. Flare Level changes across years for 87 sites, so the "Sites" column for Flare Level adds up to more than 476.

### 3.4 Sites with any flaring (BCM > 0), by year

| 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 237 | 228 | 241 | 257 | 265 | 274 | 329 | 351 | 360 | 381 | 370 | 332 | 305 | 259 |

### 3.5 Names

- **Operator:** 40 distinct values, or 39 after trimming spaces. "Renaissance Africa Energy" appears both with and without a trailing space.
- **Field name:** 171 distinct values. One site has the field name `*`.

## 4. Check: site totals vs the country file (sheet `Flare volume`)

**Result: PASS.**
- In all 14 years (2012–2025), the sum of Nigeria site BCM equals the Nigeria row of the country file to within 0.001 bcm.
- The largest absolute difference is 7.1 × 10⁻¹⁵ bcm.
- The table is saved to `data/interim/check_site_vs_country.csv`.

| Year | Site total (bcm) | Country file (bcm) |
|---|---:|---:|
| 2012 | 9.275499 | 9.275499 |
| 2013 | 9.268442 | 9.268442 |
| 2014 | 7.901176 | 7.901176 |
| 2015 | 7.184144 | 7.184144 |
| 2016 | 6.940027 | 6.940027 |
| 2017 | 7.839595 | 7.839595 |
| 2018 | 8.171973 | 8.171973 |
| 2019 | 8.242127 | 8.242127 |
| 2020 | 6.967253 | 6.967253 |
| 2021 | 6.540477 | 6.540477 |
| 2022 | 5.163808 | 5.163808 |
| 2023 | 5.099863 | 5.099863 |
| 2024 | 6.110239 | 6.110239 |
| 2025 | 6.600806 | 6.600806 |

## 5. GEM tracker: Nigeria (sheet `Field-level main data`)

The Nigeria rows are saved to `data/interim/gem_ng_fields.csv`.

| Item | Value |
|---|---:|
| Fields (rows with Country/Area = Nigeria) | 265 |
| Unique Unit IDs | 265 |
| With latitude and longitude | 142 |
| With operator | 237 |
| With both | 139 |
| Location accuracy | exact 127; approximate 16; missing 122 |

| Status | Count |
|---|---:|
| operating | 204 |
| in-development | 33 |
| mothballed | 23 |
| discovered | 4 |
| missing | 1 |

## 6. First name match: World Bank field names vs GEM unit names

This match is a first indicator only.

- **Method:** each GEM unit name is cut before " Oil" or " Gas". For example, "Abana Oil and Gas Field (Nigeria)" becomes "Abana". The result is compared, ignoring case, with the distinct World Bank field names.
- **Result:** 96 of the 171 World Bank field names match a GEM name. 75 do not.
- **Output:** `data/interim/name_match_wb_gem.csv`.
- **Examples of non-matches:**
  - names with qualifiers, such as "Adanga (conc)", "Akpo (gas)", "Akpo (PSC)" and "Agbami-Ekoli (OML 127)";
  - "Abana East";
  - "Afam Umuosi";
  - `*`.

## 7. Open questions for Phase 1

1. **The 57 sites with no Operator, Field name or Field type** (798 rows): should they be kept as "unattributed", or matched to fields by location?
2. **Operator spelling:**
   - Should names be trimmed and harmonised, for example the trailing space in "Renaissance Africa Energy"?
   - Should near-variants such as "Newcross EP" and "Newcross Petroleum" be kept separate?
   - The site file has "Moni Pulo" while GEM has "MoniPulo".
3. **Operator over time:** the site file gives one operator per site for all years. It is not stated whether this is the operator at the release date or in each year. This needs to be checked in the World Bank documentation before operators are shown by year.
4. **Rows with BCM = 0** (2,475): do they mean "no flare detected" or something else? This should be confirmed in the source notes before deciding how Power BI shows them.
5. **Flare Level changes** across years for 87 sites. How are the Small, Medium and Large cut-offs defined?
6. **The site-vs-country check matches to floating-point precision.** This suggests the country figure is the sum of the site rows rather than an independent estimate. Confirm in the source notes.
7. **Field matching:**
   - Fuzzy or rule-based matching is needed for the 75 unmatched names (qualifiers in brackets, "East", "/" compounds, the `*` site).
   - A spatial match is also an option. Only 142 of the 265 GEM fields have coordinates, and 122 have no location accuracy recorded.
8. **Nearby population:** no population data is in `data/raw` yet. The source, licence and buffer distance are still to be decided.
9. **Licence:** the World Bank files state no explicit licence. Reuse terms should be confirmed before any Power BI file is published.
