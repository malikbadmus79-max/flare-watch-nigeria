# Phase 2a results: data preparation

Date: 2026-11-20. Plan: [analysis_plan.md](analysis_plan.md), frozen v1.0. Before starting, the plan's SHA-256 was checked against [plan_freeze.md](plan_freeze.md) and matched. Amendments in force: A1 (see [amendments.md](amendments.md)). A1 is not used in Phase 2a.

Scripts:
- `src/flare_watch/clean.py`
- `src/flare_watch/geo.py`
- `src/flare_watch/phase2a.py` (runner)

Tests: `tests/test_phase2a.py`. Machine-readable output: `data/interim/phase2a_report.json`.

This document records facts only. It contains no interpretation or rankings. All flaring volumes are satellite **estimates** (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).

## 1. What was done

1. **Plan hash** checked against `plan_freeze.md`: it matches (`f3818350…e46a`).
2. **Amendment A1** logged in `amendments.md` before any use. It covers the official 2025 figure labelled "NUPRC figure as reported in the press". The figure is not used until Phase 2b.
3. **Five raw files copied** from `Downloads`. They were not renamed, and the copies without "(1)" in the name were used. Each copy is byte-identical to its original.

   | File | Size (bytes) | SHA-256 |
   |---|---:|---|
   | worldpop/nga_pop_2025_CN_100m_R2025A_v1.tif | 157,014,323 | see `sources_phase2.csv` |
   | boundaries/geoBoundaries-NGA-ADM1.geojson | 2,289,696 | 〃 |
   | boundaries/geoBoundaries-NGA-ADM2.geojson | 9,422,551 | 〃 |
   | docs/SoGF.pdf (BudgIT, *The State of Gas Flaring in Nigeria*) | 2,718,768 | 〃 |
   | docs/FLARE-GAS-PREVENTION-OF-WASTE-AND-POLLUTION-REGULATIONS-2018.pdf | 1,006,643 | 〃 |

   - These files are registered in `data/interim/sources_phase2.csv` with URL and licence:
     - WorldPop: CC BY 4.0, DOI 10.5258/SOTON/WP00839.
     - geoBoundaries: gbOpen from GRID3 2022, CC BY 4.0.
     - BudgIT report and the Regulations: documents, cited only.
   - `phase0_sources.csv` is unchanged (5 rows).
   - `data/raw/worldpop/` and `data/raw/boundaries/` were added to `.gitignore`.
4. **Packages installed** in `.venv` and added to `requirements.txt`: geopandas 1.2.0, rasterio 1.5.2, shapely 2.2.0 and pyproj 3.8.0.
5. **Pipeline run:** `phase2a.py` reads the raw World Bank site file directly and writes the tables in section 6.
6. **Tests:** 11 of 11 passed (8 new, 3 from Phase 0).

## 2. Cleaning (plan Q1, Q2, Q10)

### `data/interim/operator_cleaning.csv`

| Raw value | Clean value | Rule | Sites | Rows |
|---|---|---|---:|---:|
| (missing) | Unattributed | plan Q1 | 57 | 798 |
| "Renaissance Africa Energy " (trailing space) | Renaissance Africa Energy | trim (plan Q2) | 75 | 1,050 |

- There are no case-only variants among operator names, so the case-fix rule changed nothing.
- No near-variants were merged. "Newcross EP" and "Newcross Petroleum" remain separate.
- After cleaning there are 40 operator values: 39 named operators plus "Unattributed".

### `data/interim/field_cleaning.csv`

| Column | Raw value | Clean value | Rule | Sites | Rows |
|---|---|---|---|---:|---:|
| Field name | (missing) | Unattributed field | plan Q1 | 57 | 798 |
| Field name | `*` | Unattributed field | plan Q10 | 1 | 14 |
| Field type | (missing) | Unattributed | plan Q1 | 57 | 798 |

- The `*` site is `s_4012`. Its operator (NEPL), field type (OIL) and location (OFFSHORE) are kept as recorded.
- After cleaning there are 171 field values: 170 named fields plus "Unattributed field".

## 3. Site flags (plan section 3)

| Flag | Sites |
|---|---:|
| Persistent, ≥10 of 14 years (`persistent_10`) | 218 |
| **Persistent, ≥12 of 14 years (`persistent`, main rule)** | **171** |
| Persistent, 14 of 14 years (`persistent_14`) | 133 |
| Active in 2025 (`active_2025`) | 259 |

- The 14/14 count (133) and the 2025 active count (259) equal the Phase 0 figures.
- `recent_volume_bcm` is the mean BCM over 2023–2025, with zero years counted as 0. Every site has a row for each of those years.

## 4. State and LGA assignment (plan Q8)

Boundaries: geoBoundaries gbOpen NGA ADM1 (37 polygons) and ADM2 (774 polygons), both EPSG:4326 and all valid.

| Item | Count |
|---|---:|
| Sites with Location = OFFSHORE → state/LGA "Offshore" | 103 |
| Onshore sites | 373 |
| Onshore sites inside an ADM1 polygon | 373 |
| Onshore sites inside an ADM2 polygon | 373 |
| Assigned by nearest polygon within 2 km | 0 |
| Unassigned | 0 |
| Points on a shared boundary (multiple matches) | 0 |
| Sites whose LGA is not in their assigned state (QA) | 0 |
| OFFSHORE-labelled sites that fall inside an ADM1 land polygon (informational; still "Offshore" per plan) | 33 |

No site is "Unassigned", so `dim_state` has no "Unassigned" row. It has 37 states plus "Offshore", 38 rows in total.

### Sites by state

| State | Sites | LGAs with ≥1 site |
|---|---:|---:|
| Abia | 8 | 1 |
| Akwa Ibom | 3 | 2 |
| Bayelsa | 38 | 5 |
| Delta | 116 | 14 |
| Edo | 10 | 3 |
| Imo | 26 | 2 |
| Kaduna | 1 | 1 |
| Ondo | 1 | 1 |
| Rivers | 170 | 18 |
| Offshore | 103 | — |
| **Total** | **476** | **47** |

The Kaduna site is `s_38320` (field type OIL, ONSHORE, active in 1 of 14 years). It is listed as recorded.

## 5. Population method (plan Q8)

- **Raster:** WorldPop `nga_pop_2025_CN_100m_R2025A_v1.tif` (2025, constrained, 100 m). It is in EPSG:4326 with a pixel size of 0.000833°. Nodata is −99999, and nodata, NaN and negative values are treated as 0.
- **Buffers:** 2 km and 5 km circles around each site's lat/lon, built in EPSG:32632 (UTM 32N, 32 segments per quarter circle) and then reprojected to EPSG:4326.
- **Pixel rule:** a pixel counts if its centre lies inside the buffer (`all_touched=False`). Each pixel's full value is counted.
- **Per-site values** (`pop_2km`, `pop_5km` in `dim_site`): the sum for each site's own buffer. Neighbouring buffers overlap, so these values must not be added up across sites.
- **Union totals** (`data/processed/population_groups.csv`):
  - Each total is the sum over the union of buffers, so each person is counted once.
  - Groups: `active_2025` and `persistent` (≥12/14), at 2 km and 5 km. For each group there is one row for all sites and one row per state, including "Offshore". That gives 38 rows.
  - A state row counts residents within the buffers of the sites located in that state, wherever those residents live. Rows for different states can overlap where buffers cross state lines.
  - `pop_sum_of_sites` is given alongside each row as a check.
- **Offshore:** WorldPop has no population at sea, so only the land part of an offshore buffer adds residents. Of the 103 offshore sites, 67 have 0 residents within 2 km and 63 have 0 within 5 km. Every onshore site has more than 0 residents within both 2 km and 5 km.
- **Checks (all pass):**
  - union ≤ sum of per-site values for every group;
  - `pop_5km` ≥ `pop_2km` for every site;
  - all values ≥ 0.

Population values are counts of residents living near a flare site only. They make no statement about exposure or health (plan section 7).

## 6. Power BI tables (`data/processed/`, CSV, UTF-8)

| File | Rows | Notes |
|---|---:|---|
| `fact_site_year.csv` | 6,664 | `site_id, year, bcm, mmscfd, flare_level, active` |
| `dim_site.csv` | 476 | The plan's columns plus `active_2025`, `operator_raw`, `field_raw`, `state_iso`, `state_id`, `state_method`, `lga_id` and `lga_method`, for traceability. |
| `dim_year.csv` | 14 | `year, is_recent, official_bcm, official_source`. `official_bcm` is blank until Phase 2b. |
| `dim_operator.csv` | 40 | `operator_clean, operator_raw_variants, is_unattributed, n_sites` |
| `dim_state.csv` | 38 | 37 ADM1 states plus "Offshore". `pop_total` (optional in the plan) is not computed. |
| `param_assumptions.csv` | 14 | See the bullets below. |
| `population_groups.csv` | 38 | Union totals; see section 5. |

`param_assumptions.csv` contains:
- conversion constants;
- the higher heating value (1,020 Btu/scf);
- the CO2e factor of 2.569 Mt/bcm (implied average from World Bank 2025 global totals, 98% combustion efficiency);
- flare fee rates of $0.50 and $2.00 per Mscf, with status "to be verified in 2b" (called "penalty rates" at the time; renamed under Amendment A2);
- the three prices, left blank ("to be sourced in 2b");
- the persistence thresholds.

National totals by year from `fact_site_year.csv` equal the raw site file to within 1e-9 bcm (test).

## 7. Notes for Phase 2b

- Verify the flare fee rates (Amendment A2) and the basis for each rate against `docs/FLARE-GAS-PREVENTION-OF-WASTE-AND-POLLUTION-REGULATIONS-2018.pdf`.
- Fill in the gas price range.
- Fill `dim_year.official_bcm` for 2021–2025, using the 2025 figure under amendment A1.
- The source URLs of the BudgIT report and the Regulations PDF are not recorded yet. They are marked "URL to be recorded in Phase 4".
