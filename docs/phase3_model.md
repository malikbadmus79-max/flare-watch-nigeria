# Phase 3: Power BI semantic model

Date: 2026-11-20. Plan: [analysis_plan.md](analysis_plan.md), frozen v1.0. The plan's SHA-256 was checked against [plan_freeze.md](plan_freeze.md) before starting and matched. Amendments in force: A1, A2, A3 (see [amendments.md](amendments.md)).

This document describes the model only. No report visuals were made. All flaring volumes are satellite **estimates** (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).

## 1. What was done

1. **Backups** of the original `FlareWatch.pbix` (each byte-identical to the file at the time of copying):

   | Backup in `powerbi/backup/` | SHA-256 |
   |---|---|
   | FlareWatch_backup_20261120.pbix | `b524e9185fe5d75f7fc22dc0f861ad0fb10adc79995edb7acf2e8710bc0cd8ed` |
   | FlareWatch_backup_before_measures.pbix | `b524e9185fe5d75f7fc22dc0f861ad0fb10adc79995edb7acf2e8710bc0cd8ed` |

2. **Amendment A3** logged before applying: `dim_year` now runs 2012–2030 and has a new column `is_actual` (True 2012–2025, False 2026–2030). No values changed. Only `dim_year.csv` changed among the processed files; the other six are byte-identical. Tests: 29 of 29 pass (one new test for A3).
3. **MCP server** (Microsoft Power BI Modeling MCP, npm `@microsoft/powerbi-modeling-mcp@1.0.1`, pinned) switched to write mode in [.mcp.json](../.mcp.json). Claude Code had not loaded the server, so it was driven through [powerbi/mcp_client.py](../powerbi/mcp_client.py), which connects to the open Power BI Desktop window titled "FlareWatch". The Microsoft EULA was accepted on the user's instruction.
4. **Power Query sources** of all 7 tables repointed from a local `FlareWatch_data\` folder to the project's `data/processed/` folder (same file names; in the public repo this folder is the Power Query parameter `DataFolder`). For `dim_year`, the column count was raised from 4 to 5 and `is_actual` typed as logical; the column was added to the model. Nothing else in the queries changed (they still use `Encoding=1252`; all processed CSVs are plain ASCII, so this has no effect). The user then refreshed in Power BI Desktop. Row counts after refresh: fact_site_year 6,664; dim_site 476; dim_year 19 (14 actual); dim_operator 40; dim_state 38; param_assumptions 15; population_groups 38.
5. **Column settings, helper tables and measures** applied by [powerbi/phase3_build.py](../powerbi/phase3_build.py) from [powerbi/model_spec.py](../powerbi/model_spec.py).
6. **Validation** by [powerbi/phase3_validate.py](../powerbi/phase3_validate.py): DAX results compared with pandas values from `data/processed/` and Phase 2b outputs. **340 of 340 checks pass.** Output: `data/interim/phase3_validation.csv`.

## 2. Tables

| Table | Type | Columns | Measures |
|---|---|---:|---:|
| fact_site_year | import (CSV) | 6 | 0 |
| dim_site | import (CSV) | 24 | 0 |
| dim_year | import (CSV) | 5 | 0 |
| dim_operator | import (CSV) | 4 | 0 |
| dim_state | import (CSV) | 5 | 0 |
| param_assumptions | import (CSV) | 6 | 0 |
| population_groups | import (CSV) | 6 | 0 |
| _Measures | calculated (DAX) | 1 | 45 |
| Persistence Rule | calculated (DAX) | 2 | 0 |

- **_Measures**: `ROW("_", BLANK())`. Holds the model's measures. No data.
- **Persistence Rule**: `DATATABLE("Rule", STRING, "Min Years", INTEGER, {{"12 of 14 years (main)", 12}, {"10 of 14 years", 10}, {"14 of 14 years", 14}})`. Slicer for the persistence rule used by [Persistent Sites] (plan s3, s9.3). Not related to other tables.
- Rows of 'Persistence Rule': 10 of 14 years → 10; 12 of 14 years (main) → 12; 14 of 14 years → 14.

## 3. Relationships

All were auto-detected by Power BI and are unchanged. Plan s9.1 lists the first four; the fifth links the precomputed population table to states.

| From (many) | To (one) | Cardinality | Filter direction | Active |
|---|---|---|---|---|
| fact_site_year[site_id] | dim_site[site_id] | Many-to-One | single | yes |
| fact_site_year[year] | dim_year[year] | Many-to-One | single | yes |
| dim_site[operator_clean] | dim_operator[operator_clean] | Many-to-One | single | yes |
| dim_site[state] | dim_state[state] | Many-to-One | single | yes |
| population_groups[state] | dim_state[state] | Many-to-One | single | yes |

`population_groups` has rows with state "All", which match no `dim_state` row. The Residents measures handle this (section 5).

## 4. Column settings

### Hidden from report view

| Table | Column | Hidden in model |
|---|---|---|
| dim_site | operator_raw | yes |
| dim_site | field_raw | yes |
| dim_site | state_iso | yes |
| dim_site | state_id | yes |
| dim_site | state_method | yes |
| dim_site | lga_id | yes |
| dim_site | lga_method | yes |
| dim_state | state_iso | yes |
| dim_state | state_id | yes |
| dim_operator | operator_raw_variants | yes |
| param_assumptions | plan_ref | yes |
| _Measures | _ (placeholder) | yes |

`state_iso` and `state_id` are hidden in both `dim_site` and `dim_state`.

### Summarize by = None

| Table | Column | Summarize by (model) |
|---|---|---|
| dim_site | lat | None |
| dim_site | lon | None |
| dim_site | pop_2km | None |
| dim_site | pop_5km | None |
| dim_site | active_years | None |
| dim_site | recent_volume_bcm | None |
| fact_site_year | year | None |
| dim_year | year | None |
| dim_operator | n_sites | None |
| dim_state | n_sites | None |
| population_groups | buffer_km | None |
| population_groups | n_sites | None |
| population_groups | pop_union | None |
| population_groups | pop_sum_of_sites | None |
| param_assumptions | value | None |

`fact_site_year[bcm]` and `[mmscfd]` keep Sum.

### Formats and data categories

| Table | Column | Format | Data category |
|---|---|---|---|
| fact_site_year | bcm | `#,##0.00` |  |
| fact_site_year | mmscfd | `#,##0.00` |  |
| dim_site | recent_volume_bcm | `#,##0.00` |  |
| dim_year | official_bcm | `#,##0.00` |  |
| dim_site | pop_2km | `#,##0` |  |
| dim_site | pop_5km | `#,##0` |  |
| population_groups | pop_union | `#,##0` |  |
| population_groups | pop_sum_of_sites | `#,##0` |  |
| dim_site | lat | `0.0000` | Latitude |
| dim_site | lon | `0.0000` | Longitude |

**Sort:** `flare_level` keeps alphabetical order (Large, Medium, Small). A calculated sort column derived from `flare_level` in the same table was rejected by Power BI (circular dependency) and was removed. A Small/Medium/Large order would need an order column in the CSV, which would need an amendment. Other text columns sort alphabetically and years numerically, which is the intended order.

## 5. Measures

All 45 measures are in table `_Measures`. Parameter values (conversions, CO2e factor, prices, flare fee rates, persistence threshold) are read from `param_assumptions` with `LOOKUPVALUE`, not hard-coded. The only literal years are those named in the spec: 2012, 2023 (change baselines) and 2025–2030 (illustrative path). Check values are 2025 unless stated.

Notes:

- **Flare Volume (bcm)** returns BLANK for 2026–2030 (`is_actual` = False), so every measure built on it is BLANK there too.
- **National Volume (bcm)** uses `ALLEXCEPT(fact_site_year, dim_year)`: only year filters are kept. A first version used `REMOVEFILTERS(fact_site_year)`, which also removed the year filter (expanded table); validation caught it and it was fixed before the checks below.
- **Residents within 2 km / 5 km** cannot be summed from sites (buffers overlap). They read the precomputed unions in `population_groups` for one group (`active_2025` by default, or the selected `population_groups[group]`) and either all states or exactly one selected state. They return BLANK if several states are selected or a site or operator filter is applied, because no union is precomputed for those selections.
- **Top 10 Fields Share** includes the "Unattributed field" group in the ranking, because plan s9.3 sets an exclusion only for operators.
- **Persistent Sites** follows the 'Persistence Rule' slicer; with no selection it uses `persistent_min_years` (12) from `param_assumptions`.

### Volume

#### Flare Volume (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Sum of estimated flared volume in the current filter context. BLANK for years without satellite data (2026-2030, Amendment A3). Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  VAR _hasActual = CALCULATE ( COUNTROWS ( dim_year ), dim_year[is_actual] = TRUE () )
  RETURN IF ( _hasActual > 0, SUM ( fact_site_year[bcm] ) )
  ```

- Checks: **PASS** (19 of 19)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | national 2012 | 9.2755 | 9.2755 | yes |
  | national 2013 | 9.26844 | 9.26844 | yes |
  | national 2014 | 7.90118 | 7.90118 | yes |
  | national 2015 | 7.18414 | 7.18414 | yes |
  | national 2016 | 6.94003 | 6.94003 | yes |
  | national 2017 | 7.83959 | 7.83959 | yes |
  | national 2018 | 8.17197 | 8.17197 | yes |
  | national 2019 | 8.24213 | 8.24213 | yes |
  | national 2020 | 6.96725 | 6.96725 | yes |
  | national 2021 | 6.54048 | 6.54048 | yes |
  | national 2022 | 5.16381 | 5.16381 | yes |
  | national 2023 | 5.09986 | 5.09986 | yes |
  | national 2024 | 6.11024 | 6.11024 | yes |
  | national 2025 | 6.60081 | 6.60081 | yes |
  | national 2026, national 2027, national 2028, national 2029, national 2030 | BLANK | BLANK | yes |

#### Flare Volume (million m3)

- Display folder: Volume. Format: `#,##0.0`.
- Description: Flare Volume (bcm) x 1,000 (param bcm_to_million_m3). Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  [Flare Volume (bcm)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "bcm_to_million_m3" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 6,600.81 | 6,600.81 | yes |

#### Flare Volume (Mscf)

- Display folder: Volume. Format: `#,##0`.
- Description: Flare Volume (bcm) x 35,314,667 Mscf per bcm (param bcm_to_mscf). Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  [Flare Volume (bcm)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "bcm_to_mscf" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 233,105,272.08 | 233,105,272.08 | yes |

#### Flare Volume (bcf)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Flare Volume (bcm) x 35.3147 (param bcm_to_bcf). Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  [Flare Volume (bcm)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "bcm_to_bcf" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 233.105 | 233.105 | yes |

#### National Volume (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Flare volume ignoring site, operator, field and state filters; year filter kept. Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  CALCULATE (
      [Flare Volume (bcm)],
      ALLEXCEPT ( fact_site_year, dim_year )
  )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 with state filter Rivers (filter ignored) | 6.60081 | 6.60081 | yes |

#### Share of National

- Display folder: Volume. Format: `0.0%`.
- Description: Flare Volume (bcm) / National Volume (bcm) for the same years.
- DAX:

  ```dax
  DIVIDE ( [Flare Volume (bcm)], [National Volume (bcm)] )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025, state Rivers | 0.192641 | 0.192641 | yes |

#### Recent Volume (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Mean annual flared volume over 2023-2025 (is_recent) for the selection; zero years count as 0. Ignores the year filter. Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  VAR _years = CALCULATE ( COUNTROWS ( dim_year ), REMOVEFILTERS ( dim_year ), dim_year[is_recent] = TRUE () )
  RETURN
      DIVIDE (
          CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[is_recent] = TRUE () ),
          _years
      )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | national (mean 2023-2025) | 5.93697 | 5.93697 | yes |
  | = sum of dim_site[recent_volume_bcm] | 5.93697 | 5.93697 | yes |

#### YoY Change (bcm)

- Display folder: Volume. Format: `+#,##0.00;-#,##0.00;0.00`.
- Description: Flare volume in the year in context minus the previous year. BLANK unless exactly one year is in context and both years have satellite data.
- DAX:

  ```dax
  VAR _y = SELECTEDVALUE ( dim_year[year] )
  VAR _cur = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
  VAR _prev = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y - 1 )
  RETURN IF ( NOT ISBLANK ( _y ) && NOT ISBLANK ( _cur ) && NOT ISBLANK ( _prev ), _cur - _prev )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 vs 2024 | 0.490567 | 0.490567 | yes |
  | 2012 (no previous year) is BLANK | BLANK | BLANK | yes |

#### YoY Change (%)

- Display folder: Volume. Format: `+0.0%;-0.0%;0.0%`.
- Description: YoY Change (bcm) / previous year's flare volume.
- DAX:

  ```dax
  VAR _y = SELECTEDVALUE ( dim_year[year] )
  VAR _prev = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y - 1 )
  RETURN DIVIDE ( [YoY Change (bcm)], _prev )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 vs 2024 | 0.080286 | 0.080286 | yes |

#### Unattributed Volume (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Flare volume from sites with no recorded operator ("Unattributed"). Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  CALCULATE ( [Flare Volume (bcm)], KEEPFILTERS ( dim_operator[is_unattributed] = TRUE () ) )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 0.0526593 | 0.0526593 | yes |

#### Selected Year

- Display folder: Volume. Format: `0`.
- Description: Latest actual satellite year (is_actual) in the current selection; if none is selected, the latest actual year in the data (2025).
- DAX:

  ```dax
  COALESCE (
      CALCULATE ( MAX ( dim_year[year] ), KEEPFILTERS ( dim_year[is_actual] = TRUE () ) ),
      CALCULATE ( MAX ( dim_year[year] ), REMOVEFILTERS ( dim_year ), dim_year[is_actual] = TRUE () )
  )
  ```

- Checks: **PASS** (3 of 3)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection | 2,025 | 2,025 | yes |
  | selection 2012-2020 | 2,020 | 2,020 | yes |
  | selection 2026-2030 only (falls back to latest actual) | 2,025 | 2,025 | yes |

#### Flare Volume Selected Year (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Flare volume in [Selected Year]; other filters kept. Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  VAR _y = [Selected Year]
  RETURN CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
  ```

- Checks: **PASS** (12 of 12)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection (2025) | 6.60081 | 6.60081 | yes |
  | by state 2025: Offshore | 2.56588 | 2.56588 | yes |
  | by state 2025: Delta | 1.29413 | 1.29413 | yes |
  | by state 2025: Rivers | 1.27159 | 1.27159 | yes |
  | by state 2025: Imo | 0.671384 | 0.671384 | yes |
  | by state 2025: Bayelsa | 0.43972 | 0.43972 | yes |
  | by state 2025: Edo | 0.329245 | 0.329245 | yes |
  | by state 2025: Akwa Ibom | 0.0265105 | 0.0265105 | yes |
  | by state 2025: Abia | 0.00226601 | 0.00226601 | yes |
  | by state 2025: Kaduna | 8.41239e-05 | 8.41239e-05 | yes |
  | by state 2025: Ondo | 0 | 0 | yes |
  | states with no sites are BLANK | 0 | 0 | yes |

#### YoY Change Selected Year (%)

- Display folder: Volume. Format: `▲ 0.0%;▼ 0.0%;0.0%`.
- Description: (Flare volume in [Selected Year] - flare volume in the year before) / flare volume in the year before. Describes estimated change only. Added for the page 1 redesign.
- DAX:

  ```dax
  VAR _y = [Selected Year]
  VAR _cur = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
  VAR _prev = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y - 1 )
  RETURN DIVIDE ( _cur - _prev, _prev )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection (2025 vs 2024) | 0.080286 | 0.080286 | yes |
  | 2012 selected (no 2011) is BLANK | BLANK | BLANK | yes |

#### Volume Column Colour

- Display folder: Volume. Format: ``.
- Description: Formatting helper for the 'Gas flared each year' columns (conditional colour): "#FF7A1A" for 2025, "#9C4519" for other years. Returns text; not a data value.
- DAX:

  ```dax
  IF ( SELECTEDVALUE ( dim_year[year] ) = 2025, "#FF7A1A", "#9C4519" )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 returns #FF7A1A | BLANK | BLANK | yes |
  | 2024 returns #9C4519 | BLANK | BLANK | yes |

#### Flare Volume excl 2025 (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Chart helper: Flare Volume (bcm) for every year except 2025 (BLANK for 2025). Stacked with 'Flare Volume 2025 only (bcm)' so the 2025 column can have its own colour; the two always sum to Flare Volume (bcm). Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  CALCULATE ( [Flare Volume (bcm)], KEEPFILTERS ( dim_year[year] <> 2025 ) )
  ```

- Checks: **PASS** (20 of 20)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | excl + 2025-only = national 2012 | 9.2755 | 9.2755 | yes |
  | excl + 2025-only = national 2013 | 9.26844 | 9.26844 | yes |
  | excl + 2025-only = national 2014 | 7.90118 | 7.90118 | yes |
  | excl + 2025-only = national 2015 | 7.18414 | 7.18414 | yes |
  | excl + 2025-only = national 2016 | 6.94003 | 6.94003 | yes |
  | excl + 2025-only = national 2017 | 7.83959 | 7.83959 | yes |
  | excl + 2025-only = national 2018 | 8.17197 | 8.17197 | yes |
  | excl + 2025-only = national 2019 | 8.24213 | 8.24213 | yes |
  | excl + 2025-only = national 2020 | 6.96725 | 6.96725 | yes |
  | excl + 2025-only = national 2021 | 6.54048 | 6.54048 | yes |
  | excl + 2025-only = national 2022 | 5.16381 | 5.16381 | yes |
  | excl + 2025-only = national 2023 | 5.09986 | 5.09986 | yes |
  | excl + 2025-only = national 2024 | 6.11024 | 6.11024 | yes |
  | excl + 2025-only = national 2025 | 6.60081 | 6.60081 | yes |
  | excl + 2025-only = national 2026, excl + 2025-only = national 2027, excl + 2025-only = national 2028, excl + 2025-only = national 2029, excl + 2025-only = national 2030, 2025 is BLANK | BLANK | BLANK | yes |

#### Flare Volume 2025 only (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Chart helper: Flare Volume (bcm) for 2025 only (BLANK for other years). See 'Flare Volume excl 2025 (bcm)'. Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).
- DAX:

  ```dax
  CALCULATE ( [Flare Volume (bcm)], KEEPFILTERS ( dim_year[year] = 2025 ) )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2024 is BLANK | BLANK | BLANK | yes |

#### Change since 2012 (%)

- Display folder: Volume. Format: `+0.0%;-0.0%;0.0%`.
- Description: (Flare volume in [Selected Year] - flare volume in 2012) / flare volume in 2012. Describes estimated change only; no statement about targets.
- DAX:

  ```dax
  VAR _base = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = 2012 )
  RETURN DIVIDE ( [Flare Volume Selected Year (bcm)] - _base, _base )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection (2025) | -0.288361 | -0.288361 | yes |

#### Change since 2023 (%)

- Display folder: Volume. Format: `+0.0%;-0.0%;0.0%`.
- Description: (Flare volume in [Selected Year] - flare volume in 2023) / flare volume in 2023. Describes estimated change only; no statement about targets.
- DAX:

  ```dax
  VAR _base = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = 2023 )
  RETURN DIVIDE ( [Flare Volume Selected Year (bcm)] - _base, _base )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection (2025) | 0.29431 | 0.29431 | yes |

#### Illustrative Path 2030 (bcm)

- Display folder: Volume. Format: `#,##0.00`.
- Description: Illustrative straight-line path to zero by 2030: 2025 national volume x (2030 - year) / 5, for years 2025-2030 only; BLANK otherwise. Not a forecast; no statement that Nigeria is on or off track (plan s7, Amendment A3).
- DAX:

  ```dax
  VAR _y = SELECTEDVALUE ( dim_year[year] )
  VAR _start = 2025
  VAR _end = 2030
  VAR _base = CALCULATE ( [National Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _start )
  RETURN IF ( _y >= _start && _y <= _end, _base * ( _end - _y ) / ( _end - _start ) )
  ```

- Checks: **PASS** (19 of 19)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 6.60081 | 6.60081 | yes |
  | 2026 | 5.28064 | 5.28064 | yes |
  | 2027 | 3.96048 | 3.96048 | yes |
  | 2028 | 2.64032 | 2.64032 | yes |
  | 2029 | 1.32016 | 1.32016 | yes |
  | 2030 | 0 | 0 | yes |
  | 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024 | BLANK | BLANK | yes |

### Sites

#### Active Sites

- Display folder: Sites. Format: `#,##0`.
- Description: Distinct sites with estimated flaring (bcm > 0) in the selected years. bcm = 0 means "no flaring detected".
- DAX:

  ```dax
  CALCULATE ( DISTINCTCOUNT ( fact_site_year[site_id] ), KEEPFILTERS ( fact_site_year[bcm] > 0 ) )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 259 | 259 | yes |
  | 2026 is BLANK | BLANK | BLANK | yes |

#### Active Sites Selected Year

- Display folder: Sites. Format: `#,##0`.
- Description: Active Sites in [Selected Year]; other filters kept.
- DAX:

  ```dax
  VAR _y = [Selected Year]
  RETURN CALCULATE ( [Active Sites], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection (2025) | 259 | 259 | yes |

#### Active Sites Label Points

- Display folder: Sites. Format: `#,##0`.
- Description: Chart helper: Active Sites for 2021 (the peak year) and 2025 only, BLANK for other years. Used as an invisible second series so only those two points carry data labels.
- DAX:

  ```dax
  VAR _y = SELECTEDVALUE ( dim_year[year] )
  RETURN IF ( _y = 2021 || _y = 2025, [Active Sites] )
  ```

- Checks: **PASS** (3 of 3)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2021 | 381 | 381 | yes |
  | 2025 | 259 | 259 | yes |
  | 2024 | BLANK | BLANK | yes |

#### Persistent Sites

- Display folder: Sites. Format: `#,##0`.
- Description: Sites flagged persistent under the rule chosen in the 'Persistence Rule' slicer (10, 12 or 14 of 14 years with bcm > 0); default is param persistent_min_years (12). Not affected by the year filter.
- DAX:

  ```dax
  VAR _rule = SELECTEDVALUE ( 'Persistence Rule'[Min Years], LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "persistent_min_years" ) )
  RETURN
      SWITCH (
          _rule,
          10, CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent_10] = TRUE () ) ),
          14, CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent_14] = TRUE () ) ),
          12, CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent] = TRUE () ) )
      )
  ```

- Checks: **PASS** (3 of 3)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | default rule (12 of 14) | 171 | 171 | yes |
  | rule 10 of 14 | 218 | 218 | yes |
  | rule 14 of 14 | 133 | 133 | yes |

#### Site Passes Persistence Rule

- Display folder: Sites. Format: `0`.
- Description: Filter helper for the Sites page: 1 if the site in context has at least the number of active years chosen in the 'Persistence Rule' slicer (10, 12 or 14 of 14), else 0; 1 for every site when no rule is selected.
- DAX:

  ```dax
  VAR _rule = SELECTEDVALUE ( 'Persistence Rule'[Min Years] )
  VAR _years = MAX ( dim_site[active_years] )
  RETURN IF ( ISBLANK ( _rule ) || _years >= _rule, 1, 0 )
  ```

- Checks: **PASS** (4 of 4)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no rule selected: all sites | 476 | 476 | yes |
  | rule 10 of 14 | 218 | 218 | yes |
  | rule 12 of 14 | 171 | 171 | yes |
  | rule 14 of 14 | 133 | 133 | yes |

#### Persistent Sites (12 of 14)

- Display folder: Sites. Format: `#,##0`.
- Description: Sites with bcm > 0 in at least 12 of the 14 years 2012-2025 (main rule, plan s3). Not affected by the year filter or the Persistence Rule slicer.
- DAX:

  ```dax
  CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent] = TRUE () ) )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | all | 171 | 171 | yes |

#### Active Years

- Display folder: Sites. Format: `0`.
- Description: Number of years 2012-2025 with bcm > 0 for the one site in context; BLANK unless exactly one site is in context. Ignores the year filter.
- DAX:

  ```dax
  IF (
      HASONEVALUE ( dim_site[site_id] ),
      CALCULATE (
          DISTINCTCOUNT ( fact_site_year[year] ),
          REMOVEFILTERS ( dim_year ),
          KEEPFILTERS ( fact_site_year[bcm] > 0 )
      )
  )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | site s_38320 | 1 | 1 | yes |
  | site m_61 (year filter 2025 ignored) | 14 | 14 | yes |

### Concentration

#### Top 10 Sites Share

- Display folder: Concentration. Format: `0.0%`.
- Description: Share of national volume from the 10 largest sites in context, by flare volume; ties broken by ascending site_id.
- DAX:

  ```dax
  VAR _t =
      ADDCOLUMNS ( VALUES ( dim_site[site_id] ), "@v", [Flare Volume (bcm)] )
  VAR _top = TOPN ( 10, _t, [@v], DESC, dim_site[site_id], ASC )
  RETURN DIVIDE ( SUMX ( _top, [@v] ), [National Volume (bcm)] )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 0.314624 | 0.314624 | yes |

#### Top 10 Fields Share

- Display folder: Concentration. Format: `0.0%`.
- Description: Share of national volume from the 10 largest fields in context (field as recorded; includes the "Unattributed field" group, as plan s9.3 sets no exclusion for fields); ties broken by ascending field name.
- DAX:

  ```dax
  VAR _t =
      ADDCOLUMNS ( VALUES ( dim_site[field] ), "@v", [Flare Volume (bcm)] )
  VAR _top = TOPN ( 10, _t, [@v], DESC, dim_site[field], ASC )
  RETURN DIVIDE ( SUMX ( _top, [@v] ), [National Volume (bcm)] )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 0.364888 | 0.364888 | yes |

#### Top 10 Operators Share

- Display folder: Concentration. Format: `0.0%`.
- Description: Share of national volume from the 10 largest operators in context (operator as recorded, 2026 release), excluding "Unattributed" from the ranking; ties broken by ascending operator name.
- DAX:

  ```dax
  VAR _t =
      ADDCOLUMNS (
          CALCULATETABLE (
              VALUES ( dim_operator[operator_clean] ),
              KEEPFILTERS ( dim_operator[is_unattributed] = FALSE () )
          ),
          "@v", [Flare Volume (bcm)]
      )
  VAR _top = TOPN ( 10, _t, [@v], DESC, dim_operator[operator_clean], ASC )
  RETURN DIVIDE ( SUMX ( _top, [@v] ), [National Volume (bcm)] )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 (Unattributed excluded) | 0.832642 | 0.832642 | yes |

### Cost

#### CO2e (Mt)

- Display folder: Cost. Format: `#,##0.00`.
- Description: Flare Volume (bcm) x param co2e_mt_per_bcm (2.569): implied average CO2e per bcm from World Bank 2025 global totals (98% combustion efficiency). Global average, not Nigeria-specific.
- DAX:

  ```dax
  [Flare Volume (bcm)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "co2e_mt_per_bcm" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 16.9575 | 16.9575 | yes |

#### CO2e Selected Year (Mt)

- Display folder: Cost. Format: `#,##0.0`.
- Description: CO2e (Mt) in [Selected Year]; other filters kept. Implied average CO2e per bcm from World Bank 2025 global totals (98% combustion efficiency). Added for the page 1 redesign.
- DAX:

  ```dax
  VAR _y = [Selected Year]
  RETURN CALCULATE ( [CO2e (Mt)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
  ```

- Checks: **PASS** (2 of 2)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | no selection (2025) | 16.9575 | 16.9575 | yes |
  | 2020 selected | 17.8989 | 17.8989 | yes |

#### Assumption Source (short)

- Display folder: Cost. Format: ``.
- Description: Display helper for the Cost page assumptions table: a short source label (8 words or fewer) for the parameter in context. Full sources are in param_assumptions[source] and on the Methods page.
- DAX:

  ```dax
  SWITCH (
      SELECTEDVALUE ( param_assumptions[parameter] ),
      "bcm_to_million_m3", "Definition",
      "m3_to_ft3", "Standard conversion",
      "bcm_to_bcf", "Standard conversion (rounded)",
      "bcm_to_mscf", "Standard conversion",
      "mmscf_to_m3", "Standard conversion",
      "hhv_btu_per_scf", "World Bank Tracker 2026, p.19",
      "co2e_mt_per_bcm", "World Bank Tracker 2026, pp.17, 19",
      "flare_fee_low_usd_per_mscf", "2018 Regulations, law-firm copy, p.7",
      "flare_fee_high_usd_per_mscf", "2018 Regulations, law-firm copy, p.7",
      "price_low_usd_per_mmbtu", "NMDPRA base price, Apr 2025 (TheCable)",
      "price_central_usd_per_mmbtu", "Henry Hub 2025, World Bank Tracker",
      "price_high_usd_per_mmbtu", "TTF/Asia LNG 2025, World Bank Tracker",
      "persistent_min_years", "Definition (plan s3)",
      "persistent_sensitivity_low", "Definition (plan s3)",
      "persistent_sensitivity_high", "Definition (plan s3)",
      SELECTEDVALUE ( param_assumptions[source] )
  )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | every parameter has a label of <= 8 words | BLANK | BLANK | yes |

#### Gas Energy (MMBtu)

- Display folder: Cost. Format: `#,##0`.
- Description: Flare Volume (Mscf) x 1,000 scf/Mscf x param hhv_btu_per_scf (1,020 Btu/scf) / 10^6.
- DAX:

  ```dax
  [Flare Volume (Mscf)] * 1000 * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "hhv_btu_per_scf" ) / 1000000
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 237,767,377.53 | 237,767,377.53 | yes |

#### Gas Value Low (USD)

- Display folder: Cost. Format: `\$#,##0`.
- Description: Gas Energy (MMBtu) x param price_low_usd_per_mmbtu (2.13). Gross value of gas flared at market prices, at 2025 prices; not net revenue.
- DAX:

  ```dax
  [Gas Energy (MMBtu)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "price_low_usd_per_mmbtu" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 506,444,514.13 | 506,444,514.13 | yes |

#### Gas Value Central (USD)

- Display folder: Cost. Format: `\$#,##0`.
- Description: Gas Energy (MMBtu) x param price_central_usd_per_mmbtu (3.52). Gross value of gas flared at market prices, at 2025 prices; not net revenue.
- DAX:

  ```dax
  [Gas Energy (MMBtu)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "price_central_usd_per_mmbtu" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 836,941,168.89 | 836,941,168.89 | yes |

#### Gas Value High (USD)

- Display folder: Cost. Format: `\$#,##0`.
- Description: Gas Energy (MMBtu) x param price_high_usd_per_mmbtu (13.4). Gross value of gas flared at market prices, at 2025 prices; not net revenue.
- DAX:

  ```dax
  [Gas Energy (MMBtu)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "price_high_usd_per_mmbtu" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 3,186,082,858.84 | 3,186,082,858.84 | yes |

#### Implied Flare Fee Low (USD)

- Display folder: Cost. Format: `\$#,##0`.
- Description: Flare Volume (Mscf) x param flare_fee_low_usd_per_mscf (USD 0.50). Implied flare fee at regulatory rates (Amendment A2), applied to all satellite volume including non-routine flaring. Not an amount owed, due or unpaid; not comparable with amounts collected.
- DAX:

  ```dax
  [Flare Volume (Mscf)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "flare_fee_low_usd_per_mscf" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 116,552,636.04 | 116,552,636.04 | yes |

#### Implied Flare Fee High (USD)

- Display folder: Cost. Format: `\$#,##0`.
- Description: Flare Volume (Mscf) x param flare_fee_high_usd_per_mscf (USD 2.00). Implied flare fee at regulatory rates (Amendment A2), applied to all satellite volume including non-routine flaring. Not an amount owed, due or unpaid; not comparable with amounts collected.
- DAX:

  ```dax
  [Flare Volume (Mscf)] * LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "flare_fee_high_usd_per_mscf" )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2025 | 466,210,544.17 | 466,210,544.17 | yes |

### People

#### Residents within 2 km

- Display folder: People. Format: `#,##0`.
- Description: Residents living within 2 km of a flare site (WorldPop 2025), union of buffers so each person is counted once, from population_groups. Group from population_groups[group] (default active_2025); state from dim_state if exactly one state is selected, else all states. BLANK if several states are selected or a site or operator filter is applied (unions are precomputed per group and state only). No exposure or health claim.
- DAX:

  ```dax
  VAR _g = CALCULATE ( SELECTEDVALUE ( population_groups[group], "active_2025" ), REMOVEFILTERS ( dim_state ) )
  VAR _st = IF ( ISFILTERED ( dim_state ), SELECTEDVALUE ( dim_state[state] ), "All" )
  RETURN
      IF (
          NOT ISBLANK ( _st ) && NOT ISFILTERED ( dim_site ) && NOT ISFILTERED ( dim_operator ),
          CALCULATE (
              SUM ( population_groups[pop_union] ),
              REMOVEFILTERS ( population_groups ),
              REMOVEFILTERS ( dim_state ),
              population_groups[group] = _g,
              population_groups[state] = _st,
              population_groups[buffer_km] = 2
          )
      )
  ```

- Checks: **PASS** (82 of 82)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | active_2025, state Abia | 2,510.14 | 2,510.14 | yes |
  | active_2025, state Akwa Ibom | 13,708.78 | 13,708.78 | yes |
  | active_2025, state Bayelsa | 90,351.61 | 90,351.61 | yes |
  | active_2025, state Delta | 330,810.26 | 330,810.26 | yes |
  | active_2025, state Edo | 8,726.23 | 8,726.23 | yes |
  | active_2025, state Imo | 48,862.69 | 48,862.69 | yes |
  | active_2025, state Kaduna | 186.383 | 186.383 | yes |
  | active_2025, state Offshore | 74,679.58 | 74,679.58 | yes |
  | active_2025, state Rivers | 635,850.23 | 635,850.23 | yes |
  | persistent, state Abia | 2,388.39 | 2,388.39 | yes |
  | persistent, state Akwa Ibom | 1,147.03 | 1,147.03 | yes |
  | persistent, state Bayelsa | 87,676.93 | 87,676.93 | yes |
  | persistent, state Delta | 282,755.77 | 282,755.77 | yes |
  | persistent, state Edo | 5,870.47 | 5,870.47 | yes |
  | persistent, state Imo | 7,928.09 | 7,928.09 | yes |
  | persistent, state Offshore | 67,332.34 | 67,332.34 | yes |
  | persistent, state Rivers | 571,629.08 | 571,629.08 | yes |
  | active_2025, all states (default) | 1,166,927.90 | 1,166,927.90 | yes |
  | active_2025, Rivers | 635,850.23 | 635,850.23 | yes |
  | active_2025, state , active_2025, state Abuja Federal Capital Territory, active_2025, state Adamawa, active_2025, state Anambra, active_2025, state Bauchi, active_2025, state Benue, active_2025, state Borno, active_2025, state Cross River, active_2025, state Ebonyi, active_2025, state Ekiti, active_2025, state Enugu, active_2025, state Gombe, active_2025, state Jigawa, active_2025, state Kano, active_2025, state Katsina, active_2025, state Kebbi, active_2025, state Kogi, active_2025, state Kwara, active_2025, state Lagos, active_2025, state Nasarawa, active_2025, state Niger, active_2025, state Ogun, active_2025, state Ondo, active_2025, state Osun, active_2025, state Oyo, active_2025, state Plateau, active_2025, state Sokoto, active_2025, state Taraba, active_2025, state Yobe, active_2025, state Zamfara, persistent, state , persistent, state Abuja Federal Capital Territory, persistent, state Adamawa, persistent, state Anambra, persistent, state Bauchi, persistent, state Benue, persistent, state Borno, persistent, state Cross River, persistent, state Ebonyi, persistent, state Ekiti, persistent, state Enugu, persistent, state Gombe, persistent, state Jigawa, persistent, state Kaduna, persistent, state Kano, persistent, state Katsina, persistent, state Kebbi, persistent, state Kogi, persistent, state Kwara, persistent, state Lagos, persistent, state Nasarawa, persistent, state Niger, persistent, state Ogun, persistent, state Ondo, persistent, state Osun, persistent, state Oyo, persistent, state Plateau, persistent, state Sokoto, persistent, state Taraba, persistent, state Yobe, persistent, state Zamfara, two states selected is BLANK, site filter applied is BLANK | BLANK | BLANK | yes |

#### Residents within 5 km

- Display folder: People. Format: `#,##0`.
- Description: As Residents within 2 km, for 5 km buffers. No exposure or health claim.
- DAX:

  ```dax
  VAR _g = CALCULATE ( SELECTEDVALUE ( population_groups[group], "active_2025" ), REMOVEFILTERS ( dim_state ) )
  VAR _st = IF ( ISFILTERED ( dim_state ), SELECTEDVALUE ( dim_state[state] ), "All" )
  RETURN
      IF (
          NOT ISBLANK ( _st ) && NOT ISFILTERED ( dim_site ) && NOT ISFILTERED ( dim_operator ),
          CALCULATE (
              SUM ( population_groups[pop_union] ),
              REMOVEFILTERS ( population_groups ),
              REMOVEFILTERS ( dim_state ),
              population_groups[group] = _g,
              population_groups[state] = _st,
              population_groups[buffer_km] = 5
          )
      )
  ```

- Checks: **PASS** (80 of 80)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | active_2025, state Abia | 107,162.65 | 107,162.65 | yes |
  | active_2025, state Akwa Ibom | 85,976.68 | 85,976.68 | yes |
  | active_2025, state Bayelsa | 489,777.04 | 489,777.04 | yes |
  | active_2025, state Delta | 1,690,028.49 | 1,690,028.49 | yes |
  | active_2025, state Edo | 35,967.81 | 35,967.81 | yes |
  | active_2025, state Imo | 196,092.49 | 196,092.49 | yes |
  | active_2025, state Kaduna | 1,739.04 | 1,739.04 | yes |
  | active_2025, state Offshore | 256,836.68 | 256,836.68 | yes |
  | active_2025, state Rivers | 2,583,261.61 | 2,583,261.61 | yes |
  | persistent, state Abia | 69,417.39 | 69,417.39 | yes |
  | persistent, state Akwa Ibom | 33,896.03 | 33,896.03 | yes |
  | persistent, state Bayelsa | 448,001.82 | 448,001.82 | yes |
  | persistent, state Delta | 1,327,930.85 | 1,327,930.85 | yes |
  | persistent, state Edo | 21,156.02 | 21,156.02 | yes |
  | persistent, state Imo | 45,723.95 | 45,723.95 | yes |
  | persistent, state Offshore | 239,451.93 | 239,451.93 | yes |
  | persistent, state Rivers | 2,216,734.63 | 2,216,734.63 | yes |
  | active_2025, all states (default) | 5,061,850.03 | 5,061,850.03 | yes |
  | persistent, all states | 4,116,773.85 | 4,116,773.85 | yes |
  | active_2025, state , active_2025, state Abuja Federal Capital Territory, active_2025, state Adamawa, active_2025, state Anambra, active_2025, state Bauchi, active_2025, state Benue, active_2025, state Borno, active_2025, state Cross River, active_2025, state Ebonyi, active_2025, state Ekiti, active_2025, state Enugu, active_2025, state Gombe, active_2025, state Jigawa, active_2025, state Kano, active_2025, state Katsina, active_2025, state Kebbi, active_2025, state Kogi, active_2025, state Kwara, active_2025, state Lagos, active_2025, state Nasarawa, active_2025, state Niger, active_2025, state Ogun, active_2025, state Ondo, active_2025, state Osun, active_2025, state Oyo, active_2025, state Plateau, active_2025, state Sokoto, active_2025, state Taraba, active_2025, state Yobe, active_2025, state Zamfara, persistent, state , persistent, state Abuja Federal Capital Territory, persistent, state Adamawa, persistent, state Anambra, persistent, state Bauchi, persistent, state Benue, persistent, state Borno, persistent, state Cross River, persistent, state Ebonyi, persistent, state Ekiti, persistent, state Enugu, persistent, state Gombe, persistent, state Jigawa, persistent, state Kaduna, persistent, state Kano, persistent, state Katsina, persistent, state Kebbi, persistent, state Kogi, persistent, state Kwara, persistent, state Lagos, persistent, state Nasarawa, persistent, state Niger, persistent, state Ogun, persistent, state Ondo, persistent, state Osun, persistent, state Oyo, persistent, state Plateau, persistent, state Sokoto, persistent, state Taraba, persistent, state Yobe, persistent, state Zamfara | BLANK | BLANK | yes |

#### Residents within 5 km of persistent sites

- Display folder: People. Format: `#,##0`.
- Description: Residents living within 5 km of persistent sites (WorldPop 2025), union of buffers, from population_groups with the group fixed to 'persistent' (no fallback to another group); all states, or exactly one selected state; BLANK where a state has no persistent site. No exposure or health claim.
- DAX:

  ```dax
  VAR _st = IF ( ISFILTERED ( dim_state ), SELECTEDVALUE ( dim_state[state] ), "All" )
  RETURN
      IF (
          NOT ISBLANK ( _st ) && NOT ISFILTERED ( dim_site ) && NOT ISFILTERED ( dim_operator ),
          CALCULATE (
              SUM ( population_groups[pop_union] ),
              REMOVEFILTERS ( population_groups ),
              REMOVEFILTERS ( dim_state ),
              population_groups[group] = "persistent",
              population_groups[state] = _st,
              population_groups[buffer_km] = 5
          )
      )
  ```

- Checks: **PASS** (40 of 40)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | all states | 4,116,773.85 | 4,116,773.85 | yes |
  | state Abia | 69,417.39 | 69,417.39 | yes |
  | state Akwa Ibom | 33,896.03 | 33,896.03 | yes |
  | state Bayelsa | 448,001.82 | 448,001.82 | yes |
  | state Delta | 1,327,930.85 | 1,327,930.85 | yes |
  | state Edo | 21,156.02 | 21,156.02 | yes |
  | state Imo | 45,723.95 | 45,723.95 | yes |
  | state Offshore | 239,451.93 | 239,451.93 | yes |
  | state Rivers | 2,216,734.63 | 2,216,734.63 | yes |
  | state , state Abuja Federal Capital Territory, state Adamawa, state Anambra, state Bauchi, state Benue, state Borno, state Cross River, state Ebonyi, state Ekiti, state Enugu, state Gombe, state Jigawa, state Kaduna, state Kano, state Katsina, state Kebbi, state Kogi, state Kwara, state Lagos, state Nasarawa, state Niger, state Ogun, state Ondo, state Osun, state Oyo, state Plateau, state Sokoto, state Taraba, state Yobe, state Zamfara | BLANK | BLANK | yes |

#### Residents within 5 km (per site)

- Display folder: People. Format: `#,##0`.
- Description: Residents living within 5 km of the one site in context (its own buffer; may overlap with neighbouring sites, so do not add across sites). BLANK unless exactly one site is in context. No exposure or health claim.
- DAX:

  ```dax
  IF ( HASONEVALUE ( dim_site[site_id] ), SUM ( dim_site[pop_5km] ) )
  ```

- Checks: **PASS** (1 of 1)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | site s_38320 | 1,739.04 | 1,739.04 | yes |

### Validation

#### Official Volume (bcm)

- Display folder: Validation. Format: `#,##0.00`.
- Description: Official national flared volume converted to bcm (2021-2024 NUPRC via BudgIT; 2025 NUPRC figure as reported in the press, Amendment A1). BLANK where none, or if any selected year has none.
- DAX:

  ```dax
  VAR _n = COUNTROWS ( dim_year )
  VAR _k = COUNT ( dim_year[official_bcm] )
  RETURN IF ( _n > 0 && _k = _n, SUM ( dim_year[official_bcm] ) )
  ```

- Checks: **PASS** (7 of 7)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2021 | 7.15224 | 7.15224 | yes |
  | 2022 | 5.33608 | 5.33608 | yes |
  | 2023 | 5.19688 | 5.19688 | yes |
  | 2024 | 5.46195 | 5.46195 | yes |
  | 2025 | 5.77381 | 5.77381 | yes |
  | 2020 is BLANK, 2020-2025 selected is BLANK (2020 has none) | BLANK | BLANK | yes |

#### Satellite − Official (bcm)

- Display folder: Validation. Format: `+#,##0.00;-#,##0.00;0.00`.
- Description: National Volume (bcm) minus Official Volume (bcm). Reports the difference only, not its cause.
- DAX:

  ```dax
  VAR _off = [Official Volume (bcm)]
  RETURN IF ( NOT ISBLANK ( _off ), [National Volume (bcm)] - _off )
  ```

- Checks: **PASS** (5 of 5)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2021 | -0.611763 | -0.611763 | yes |
  | 2022 | -0.172276 | -0.172276 | yes |
  | 2023 | -0.0970143 | -0.0970143 | yes |
  | 2024 | 0.648288 | 0.648288 | yes |
  | 2025 | 0.827001 | 0.827001 | yes |

#### Satellite ÷ Official

- Display folder: Validation. Format: `0.000`.
- Description: National Volume (bcm) / Official Volume (bcm). Reports the ratio only, not its cause.
- DAX:

  ```dax
  DIVIDE ( [National Volume (bcm)], [Official Volume (bcm)] )
  ```

- Checks: **PASS** (5 of 5)

  | Check | DAX | Python | Pass |
  |---|---:|---:|---|
  | 2021 | 0.914465 | 0.914465 | yes |
  | 2022 | 0.967715 | 0.967715 | yes |
  | 2023 | 0.981332 | 0.981332 | yes |
  | 2024 | 1.11869 | 1.11869 | yes |
  | 2025 | 1.14323 | 1.14323 | yes |

## 6. Validation summary (task step 7)

Tolerances: 0.001 bcm (and 0.001 Mt CO2e), exact for counts and years, 1 USD, 1 person, 1e-9 for shares and ratios.

| Item | DAX | Python | Pass |
|---|---:|---:|---|
| National bcm by year 2012–2025 (and BLANK 2026–2030) | 19 of 19 years match | — | yes |
| Active sites 2025 | 259 | 259 | yes |
| Persistent sites (12 of 14) | 171 | 171 | yes |
| Top-10 site share 2025 | 0.314624 | 0.314624 | yes |
| CO2e 2025 (Mt) | 16.9575 | 16.9575 | yes |
| Gas value low 2025 | 506,444,514.13 | 506,444,514.13 | yes |
| Gas value central 2025 | 836,941,168.89 | 836,941,168.89 | yes |
| Gas value high 2025 | 3,186,082,858.84 | 3,186,082,858.84 | yes |
| Implied flare fee low 2025 | 116,552,636.04 | 116,552,636.04 | yes |
| Implied flare fee high 2025 | 466,210,544.17 | 466,210,544.17 | yes |

All checks: **340 of 340 pass.**

## 7. Model additions after Phase 3 (page 1 night redesign, 2026-11-20)

Added only where missing; no existing measure changed. Written into the PBIP TMDL (`_Measures.tmdl`) by [powerbi/tmdl_add_measures.py](../powerbi/tmdl_add_measures.py) while Power BI Desktop was closed, then checked in the open model by phase3_validate.py (section 5).

| Requested | Result |
|---|---|
| YoY Change Selected Year (%) | Added (folder Volume, format `▲ 0.0%;▼ 0.0%;0.0%`). |
| CO2e Selected Year (Mt) | Added (folder Cost, format `#,##0.0`). |
| Flare Volume Selected Year by state | Not added: the existing `Flare Volume Selected Year (bcm)` already returns per-state values when sliced by `dim_state[state]` (filter flows dim_state → dim_site → fact_site_year). Checked per state against pandas (section 5). |
| Volume Column Colour (polish round 2) | Added (folder Volume, text, no format string). Formatting helper for the conditional column colour of "Gas flared each year": "#FF7A1A" for 2025, "#9C4519" otherwise. Not a data value. |
| Flare Volume excl 2025 (bcm) and Flare Volume 2025 only (bcm) (final fix) | Added (folder Volume). Chart helpers: two stacked column series so 2025 has its own colour; checked to sum to Flare Volume (bcm) for every year 2012–2030 (section 5). |
| Site Passes Persistence Rule (pages 2–6) | Added (folder Sites). Filter helper for the Sites page: 1 if the site meets the rule chosen in the 'Persistence Rule' slicer (all sites when none chosen). Checked: 476 / 218 / 171 / 133 sites for none / 10 / 12 / 14 of 14 (section 5). |
| Residents within 5 km of persistent sites (pages 2–6) | Added (folder People). Group fixed to 'persistent'. Added because of a defect found in the existing `Residents within 5 km`: when the selected group has no row for a state, `SELECTEDVALUE(population_groups[group], "active_2025")` falls back to the active-2025 row (e.g. Kaduna showed 1,739 under 'persistent'). The existing measure was not changed (additions only); the People page uses the new measure for its by-state chart. Checked per state against population_groups.csv (section 5). |
| **Model fix (Phase 4): Residents within 2 km / Residents within 5 km** | Fixed (a model fix, not a plan amendment). The group is now read with the state filter removed: `VAR _g = CALCULATE ( SELECTEDVALUE ( population_groups[group], "active_2025" ), REMOVEFILTERS ( dim_state ) )`. Before, a state with no row for the selected group fell back to the active-2025 row (Kaduna showed 1,739 under 'persistent'); now it returns BLANK. Checked for every state, both groups and both buffers against population_groups.csv (section 5). The People cards use these measures; no other change. |
| Assumption Source (short) (Phase 4) | Added (folder Cost, text). Display helper: a source label of 8 words or fewer for each parameter, used by the Cost page assumptions table; full sources stay in param_assumptions and on the Methods page. Checked: all 15 parameters labelled, all ≤ 8 words. |
| Active Sites Label Points (polish round 2) | Added (folder Sites). Chart helper: Active Sites for 2021 and 2025 only, BLANK otherwise; an invisible series so only those points are labelled. |

## 8. Open items

- Save the file in Power BI Desktop (**File > Save**). Model changes made through the MCP server live in the open session until saved.
- No report visuals yet. The `trace` table in plan s9.1 is not built yet.
- `flare_level` sort order (section 4).
