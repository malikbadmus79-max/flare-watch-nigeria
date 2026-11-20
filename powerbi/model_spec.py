"""Phase 3 Power BI model spec: column settings and measures (plan s9.3, Amendments A2, A3).

Single source of truth for what phase3_build.py writes to the model and what
docs/phase3_model.md lists. Parameter values are read from param_assumptions in DAX,
never hard-coded. Wording follows plan section 7 (safe-claim rules).
"""

MEASURE_TABLE = "_Measures"
RULE_TABLE = "Persistence Rule"

# ---------- step 5: column settings ----------
NO_SUM = {
    "dim_site": ["lat", "lon", "pop_2km", "pop_5km", "active_years", "recent_volume_bcm"],
    "fact_site_year": ["year"],
    "dim_year": ["year"],
    "dim_operator": ["n_sites"],
    "dim_state": ["n_sites"],
    "population_groups": ["buffer_km", "n_sites", "pop_union", "pop_sum_of_sites"],
    "param_assumptions": ["value"],
}
HIDDEN = {
    "dim_site": ["operator_raw", "field_raw", "state_iso", "state_id", "state_method", "lga_id", "lga_method"],
    "dim_state": ["state_iso", "state_id"],
    "dim_operator": ["operator_raw_variants"],
    "param_assumptions": ["plan_ref"],
}
FORMATS = {
    ("fact_site_year", "bcm"): "#,##0.00",
    ("fact_site_year", "mmscfd"): "#,##0.00",
    ("dim_site", "recent_volume_bcm"): "#,##0.00",
    ("dim_year", "official_bcm"): "#,##0.00",
    ("dim_site", "pop_2km"): "#,##0",
    ("dim_site", "pop_5km"): "#,##0",
    ("population_groups", "pop_union"): "#,##0",
    ("population_groups", "pop_sum_of_sites"): "#,##0",
    ("dim_site", "lat"): "0.0000",
    ("dim_site", "lon"): "0.0000",
}
DATA_CATEGORY = {("dim_site", "lat"): "Latitude", ("dim_site", "lon"): "Longitude"}

# flare_level keeps alphabetical sort: a calculated sort column on fact_site_year derived from
# flare_level is rejected by Power BI (circular dependency). A Small/Medium/Large order would need
# an order column in the CSV (would need an amendment). Not done.
CALC_COLUMNS: list[dict] = []
SORT_BY: dict = {}

# ---------- step 6: tables ----------
CALC_TABLES = [
    {"name": MEASURE_TABLE, "daxExpression": 'ROW("_", BLANK())',
     "description": "Holds the model's measures. No data."},
    {"name": RULE_TABLE,
     "daxExpression": 'DATATABLE("Rule", STRING, "Min Years", INTEGER, '
                      '{{"12 of 14 years (main)", 12}, {"10 of 14 years", 10}, {"14 of 14 years", 14}})',
     "description": "Slicer for the persistence rule used by [Persistent Sites] (plan s3, s9.3). "
                    "Not related to other tables."},
]


def P(name: str) -> str:
    """DAX lookup of one parameter value from param_assumptions."""
    return f'LOOKUPVALUE ( param_assumptions[value], param_assumptions[parameter], "{name}" )'


EST = "Satellite estimate (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR)."
FEE_NOTE = ("Implied flare fee at regulatory rates (Amendment A2), applied to all satellite volume including "
            "non-routine flaring. Not an amount owed, due or unpaid; not comparable with amounts collected.")
VALUE_NOTE = "Gross value of gas flared at market prices, at 2025 prices; not net revenue."

# name, folder, format, description, DAX
MEASURES = [
    # ----- Volume -----
    ("Flare Volume (bcm)", "Volume", "#,##0.00",
     f"Sum of estimated flared volume in the current filter context. BLANK for years without satellite data "
     f"(2026-2030, Amendment A3). {EST}",
     """VAR _hasActual = CALCULATE ( COUNTROWS ( dim_year ), dim_year[is_actual] = TRUE () )
RETURN IF ( _hasActual > 0, SUM ( fact_site_year[bcm] ) )"""),
    ("Flare Volume (million m3)", "Volume", "#,##0.0",
     f"Flare Volume (bcm) x 1,000 (param bcm_to_million_m3). {EST}",
     f"[Flare Volume (bcm)] * {P('bcm_to_million_m3')}"),
    ("Flare Volume (Mscf)", "Volume", "#,##0",
     f"Flare Volume (bcm) x 35,314,667 Mscf per bcm (param bcm_to_mscf). {EST}",
     f"[Flare Volume (bcm)] * {P('bcm_to_mscf')}"),
    ("Flare Volume (bcf)", "Volume", "#,##0.00",
     f"Flare Volume (bcm) x 35.3147 (param bcm_to_bcf). {EST}",
     f"[Flare Volume (bcm)] * {P('bcm_to_bcf')}"),
    ("National Volume (bcm)", "Volume", "#,##0.00",
     f"Flare volume ignoring site, operator, field and state filters; year filter kept. {EST}",
     """CALCULATE (
    [Flare Volume (bcm)],
    ALLEXCEPT ( fact_site_year, dim_year )
)"""),
    ("Share of National", "Volume", "0.0%",
     "Flare Volume (bcm) / National Volume (bcm) for the same years.",
     "DIVIDE ( [Flare Volume (bcm)], [National Volume (bcm)] )"),
    ("Recent Volume (bcm)", "Volume", "#,##0.00",
     f"Mean annual flared volume over 2023-2025 (is_recent) for the selection; zero years count as 0. "
     f"Ignores the year filter. {EST}",
     """VAR _years = CALCULATE ( COUNTROWS ( dim_year ), REMOVEFILTERS ( dim_year ), dim_year[is_recent] = TRUE () )
RETURN
    DIVIDE (
        CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[is_recent] = TRUE () ),
        _years
    )"""),
    ("YoY Change (bcm)", "Volume", "+#,##0.00;-#,##0.00;0.00",
     "Flare volume in the year in context minus the previous year. BLANK unless exactly one year is in "
     "context and both years have satellite data.",
     """VAR _y = SELECTEDVALUE ( dim_year[year] )
VAR _cur = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
VAR _prev = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y - 1 )
RETURN IF ( NOT ISBLANK ( _y ) && NOT ISBLANK ( _cur ) && NOT ISBLANK ( _prev ), _cur - _prev )"""),
    ("YoY Change (%)", "Volume", "+0.0%;-0.0%;0.0%",
     "YoY Change (bcm) / previous year's flare volume.",
     """VAR _y = SELECTEDVALUE ( dim_year[year] )
VAR _prev = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y - 1 )
RETURN DIVIDE ( [YoY Change (bcm)], _prev )"""),
    ("Unattributed Volume (bcm)", "Volume", "#,##0.00",
     f"Flare volume from sites with no recorded operator (\"Unattributed\"). {EST}",
     "CALCULATE ( [Flare Volume (bcm)], KEEPFILTERS ( dim_operator[is_unattributed] = TRUE () ) )"),
    ("Selected Year", "Volume", "0",
     "Latest actual satellite year (is_actual) in the current selection; if none is selected, the latest "
     "actual year in the data (2025).",
     """COALESCE (
    CALCULATE ( MAX ( dim_year[year] ), KEEPFILTERS ( dim_year[is_actual] = TRUE () ) ),
    CALCULATE ( MAX ( dim_year[year] ), REMOVEFILTERS ( dim_year ), dim_year[is_actual] = TRUE () )
)"""),
    ("Flare Volume Selected Year (bcm)", "Volume", "#,##0.00",
     f"Flare volume in [Selected Year]; other filters kept. {EST}",
     """VAR _y = [Selected Year]
RETURN CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )"""),
    ("YoY Change Selected Year (%)", "Volume", "▲ 0.0%;▼ 0.0%;0.0%",
     "(Flare volume in [Selected Year] - flare volume in the year before) / flare volume in the year before. "
     "Describes estimated change only. Added for the page 1 redesign.",
     """VAR _y = [Selected Year]
VAR _cur = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )
VAR _prev = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y - 1 )
RETURN DIVIDE ( _cur - _prev, _prev )"""),
    ("Volume Column Colour", "Volume", "",
     "Formatting helper for the 'Gas flared each year' columns (conditional colour): \"#FF7A1A\" for 2025, "
     "\"#9C4519\" for other years. Returns text; not a data value.",
     'IF ( SELECTEDVALUE ( dim_year[year] ) = 2025, "#FF7A1A", "#9C4519" )'),
    ("Flare Volume excl 2025 (bcm)", "Volume", "#,##0.00",
     f"Chart helper: Flare Volume (bcm) for every year except 2025 (BLANK for 2025). Stacked with "
     f"'Flare Volume 2025 only (bcm)' so the 2025 column can have its own colour; the two always sum to "
     f"Flare Volume (bcm). {EST}",
     "CALCULATE ( [Flare Volume (bcm)], KEEPFILTERS ( dim_year[year] <> 2025 ) )"),
    ("Flare Volume 2025 only (bcm)", "Volume", "#,##0.00",
     f"Chart helper: Flare Volume (bcm) for 2025 only (BLANK for other years). See 'Flare Volume excl 2025 "
     f"(bcm)'. {EST}",
     "CALCULATE ( [Flare Volume (bcm)], KEEPFILTERS ( dim_year[year] = 2025 ) )"),
    ("Change since 2012 (%)", "Volume", "+0.0%;-0.0%;0.0%",
     "(Flare volume in [Selected Year] - flare volume in 2012) / flare volume in 2012. Describes estimated "
     "change only; no statement about targets.",
     """VAR _base = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = 2012 )
RETURN DIVIDE ( [Flare Volume Selected Year (bcm)] - _base, _base )"""),
    ("Change since 2023 (%)", "Volume", "+0.0%;-0.0%;0.0%",
     "(Flare volume in [Selected Year] - flare volume in 2023) / flare volume in 2023. Describes estimated "
     "change only; no statement about targets.",
     """VAR _base = CALCULATE ( [Flare Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = 2023 )
RETURN DIVIDE ( [Flare Volume Selected Year (bcm)] - _base, _base )"""),
    ("Illustrative Path 2030 (bcm)", "Volume", "#,##0.00",
     "Illustrative straight-line path to zero by 2030: 2025 national volume x (2030 - year) / 5, for years "
     "2025-2030 only; BLANK otherwise. Not a forecast; no statement that Nigeria is on or off track "
     "(plan s7, Amendment A3).",
     """VAR _y = SELECTEDVALUE ( dim_year[year] )
VAR _start = 2025
VAR _end = 2030
VAR _base = CALCULATE ( [National Volume (bcm)], REMOVEFILTERS ( dim_year ), dim_year[year] = _start )
RETURN IF ( _y >= _start && _y <= _end, _base * ( _end - _y ) / ( _end - _start ) )"""),
    # ----- Sites -----
    ("Active Sites", "Sites", "#,##0",
     "Distinct sites with estimated flaring (bcm > 0) in the selected years. bcm = 0 means \"no flaring "
     "detected\".",
     "CALCULATE ( DISTINCTCOUNT ( fact_site_year[site_id] ), KEEPFILTERS ( fact_site_year[bcm] > 0 ) )"),
    ("Active Sites Selected Year", "Sites", "#,##0",
     "Active Sites in [Selected Year]; other filters kept.",
     """VAR _y = [Selected Year]
RETURN CALCULATE ( [Active Sites], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )"""),
    ("Active Sites Label Points", "Sites", "#,##0",
     "Chart helper: Active Sites for 2021 (the peak year) and 2025 only, BLANK for other years. Used as an "
     "invisible second series so only those two points carry data labels.",
     """VAR _y = SELECTEDVALUE ( dim_year[year] )
RETURN IF ( _y = 2021 || _y = 2025, [Active Sites] )"""),
    ("Persistent Sites", "Sites", "#,##0",
     "Sites flagged persistent under the rule chosen in the 'Persistence Rule' slicer (10, 12 or 14 of 14 "
     "years with bcm > 0); default is param persistent_min_years (12). Not affected by the year filter.",
     f"""VAR _rule = SELECTEDVALUE ( '{RULE_TABLE}'[Min Years], {P('persistent_min_years')} )
RETURN
    SWITCH (
        _rule,
        10, CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent_10] = TRUE () ) ),
        14, CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent_14] = TRUE () ) ),
        12, CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent] = TRUE () ) )
    )"""),
    ("Site Passes Persistence Rule", "Sites", "0",
     "Filter helper for the Sites page: 1 if the site in context has at least the number of active years chosen "
     "in the 'Persistence Rule' slicer (10, 12 or 14 of 14), else 0; 1 for every site when no rule is selected.",
     """VAR _rule = SELECTEDVALUE ( 'Persistence Rule'[Min Years] )
VAR _years = MAX ( dim_site[active_years] )
RETURN IF ( ISBLANK ( _rule ) || _years >= _rule, 1, 0 )"""),
    ("Persistent Sites (12 of 14)", "Sites", "#,##0",
     "Sites with bcm > 0 in at least 12 of the 14 years 2012-2025 (main rule, plan s3). Not affected by the "
     "year filter or the Persistence Rule slicer.",
     "CALCULATE ( COUNTROWS ( dim_site ), KEEPFILTERS ( dim_site[persistent] = TRUE () ) )"),
    ("Active Years", "Sites", "0",
     "Number of years 2012-2025 with bcm > 0 for the one site in context; BLANK unless exactly one site is "
     "in context. Ignores the year filter.",
     """IF (
    HASONEVALUE ( dim_site[site_id] ),
    CALCULATE (
        DISTINCTCOUNT ( fact_site_year[year] ),
        REMOVEFILTERS ( dim_year ),
        KEEPFILTERS ( fact_site_year[bcm] > 0 )
    )
)"""),
    # ----- Concentration -----
    ("Top 10 Sites Share", "Concentration", "0.0%",
     "Share of national volume from the 10 largest sites in context, by flare volume; ties broken by "
     "ascending site_id.",
     """VAR _t =
    ADDCOLUMNS ( VALUES ( dim_site[site_id] ), "@v", [Flare Volume (bcm)] )
VAR _top = TOPN ( 10, _t, [@v], DESC, dim_site[site_id], ASC )
RETURN DIVIDE ( SUMX ( _top, [@v] ), [National Volume (bcm)] )"""),
    ("Top 10 Fields Share", "Concentration", "0.0%",
     "Share of national volume from the 10 largest fields in context (field as recorded; includes the "
     "\"Unattributed field\" group, as plan s9.3 sets no exclusion for fields); ties broken by ascending field name.",
     """VAR _t =
    ADDCOLUMNS ( VALUES ( dim_site[field] ), "@v", [Flare Volume (bcm)] )
VAR _top = TOPN ( 10, _t, [@v], DESC, dim_site[field], ASC )
RETURN DIVIDE ( SUMX ( _top, [@v] ), [National Volume (bcm)] )"""),
    ("Top 10 Operators Share", "Concentration", "0.0%",
     "Share of national volume from the 10 largest operators in context (operator as recorded, 2026 release), "
     "excluding \"Unattributed\" from the ranking; ties broken by ascending operator name.",
     """VAR _t =
    ADDCOLUMNS (
        CALCULATETABLE (
            VALUES ( dim_operator[operator_clean] ),
            KEEPFILTERS ( dim_operator[is_unattributed] = FALSE () )
        ),
        "@v", [Flare Volume (bcm)]
    )
VAR _top = TOPN ( 10, _t, [@v], DESC, dim_operator[operator_clean], ASC )
RETURN DIVIDE ( SUMX ( _top, [@v] ), [National Volume (bcm)] )"""),
    # ----- Cost -----
    ("CO2e (Mt)", "Cost", "#,##0.00",
     "Flare Volume (bcm) x param co2e_mt_per_bcm (2.569): implied average CO2e per bcm from World Bank 2025 "
     "global totals (98% combustion efficiency). Global average, not Nigeria-specific.",
     f"[Flare Volume (bcm)] * {P('co2e_mt_per_bcm')}"),
    ("CO2e Selected Year (Mt)", "Cost", "#,##0.0",
     "CO2e (Mt) in [Selected Year]; other filters kept. Implied average CO2e per bcm from World Bank 2025 "
     "global totals (98% combustion efficiency). Added for the page 1 redesign.",
     """VAR _y = [Selected Year]
RETURN CALCULATE ( [CO2e (Mt)], REMOVEFILTERS ( dim_year ), dim_year[year] = _y )"""),
    ("Assumption Source (short)", "Cost", "",
     "Display helper for the Cost page assumptions table: a short source label (8 words or fewer) for the "
     "parameter in context. Full sources are in param_assumptions[source] and on the Methods page.",
     """SWITCH (
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
)"""),
    ("Gas Energy (MMBtu)", "Cost", "#,##0",
     "Flare Volume (Mscf) x 1,000 scf/Mscf x param hhv_btu_per_scf (1,020 Btu/scf) / 10^6.",
     f"[Flare Volume (Mscf)] * 1000 * {P('hhv_btu_per_scf')} / 1000000"),
    ("Gas Value Low (USD)", "Cost", "\\$#,##0",
     f"Gas Energy (MMBtu) x param price_low_usd_per_mmbtu (2.13). {VALUE_NOTE}",
     f"[Gas Energy (MMBtu)] * {P('price_low_usd_per_mmbtu')}"),
    ("Gas Value Central (USD)", "Cost", "\\$#,##0",
     f"Gas Energy (MMBtu) x param price_central_usd_per_mmbtu (3.52). {VALUE_NOTE}",
     f"[Gas Energy (MMBtu)] * {P('price_central_usd_per_mmbtu')}"),
    ("Gas Value High (USD)", "Cost", "\\$#,##0",
     f"Gas Energy (MMBtu) x param price_high_usd_per_mmbtu (13.4). {VALUE_NOTE}",
     f"[Gas Energy (MMBtu)] * {P('price_high_usd_per_mmbtu')}"),
    ("Implied Flare Fee Low (USD)", "Cost", "\\$#,##0",
     f"Flare Volume (Mscf) x param flare_fee_low_usd_per_mscf (USD 0.50). {FEE_NOTE}",
     f"[Flare Volume (Mscf)] * {P('flare_fee_low_usd_per_mscf')}"),
    ("Implied Flare Fee High (USD)", "Cost", "\\$#,##0",
     f"Flare Volume (Mscf) x param flare_fee_high_usd_per_mscf (USD 2.00). {FEE_NOTE}",
     f"[Flare Volume (Mscf)] * {P('flare_fee_high_usd_per_mscf')}"),
    # ----- People -----
    ("Residents within 2 km", "People", "#,##0",
     "Residents living within 2 km of a flare site (WorldPop 2025), union of buffers so each person is counted "
     "once, from population_groups. Group from population_groups[group] (default active_2025); state from "
     "dim_state if exactly one state is selected, else all states. BLANK if several states are selected or a "
     "site or operator filter is applied (unions are precomputed per group and state only). No exposure or "
     "health claim.",
     """VAR _g = CALCULATE ( SELECTEDVALUE ( population_groups[group], "active_2025" ), REMOVEFILTERS ( dim_state ) )
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
    )"""),
    ("Residents within 5 km", "People", "#,##0",
     "As Residents within 2 km, for 5 km buffers. No exposure or health claim.",
     """VAR _g = CALCULATE ( SELECTEDVALUE ( population_groups[group], "active_2025" ), REMOVEFILTERS ( dim_state ) )
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
    )"""),
    ("Residents within 5 km of persistent sites", "People", "#,##0",
     "Residents living within 5 km of persistent sites (WorldPop 2025), union of buffers, from population_groups "
     "with the group fixed to 'persistent' (no fallback to another group); all states, or exactly one selected "
     "state; BLANK where a state has no persistent site. No exposure or health claim.",
     """VAR _st = IF ( ISFILTERED ( dim_state ), SELECTEDVALUE ( dim_state[state] ), "All" )
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
    )"""),
    ("Residents within 5 km (per site)", "People", "#,##0",
     "Residents living within 5 km of the one site in context (its own buffer; may overlap with neighbouring "
     "sites, so do not add across sites). BLANK unless exactly one site is in context. No exposure or health "
     "claim.",
     "IF ( HASONEVALUE ( dim_site[site_id] ), SUM ( dim_site[pop_5km] ) )"),
    # ----- Validation -----
    ("Official Volume (bcm)", "Validation", "#,##0.00",
     "Official national flared volume converted to bcm (2021-2024 NUPRC via BudgIT; 2025 NUPRC figure as "
     "reported in the press, Amendment A1). BLANK where none, or if any selected year has none.",
     """VAR _n = COUNTROWS ( dim_year )
VAR _k = COUNT ( dim_year[official_bcm] )
RETURN IF ( _n > 0 && _k = _n, SUM ( dim_year[official_bcm] ) )"""),
    ("Satellite − Official (bcm)", "Validation", "+#,##0.00;-#,##0.00;0.00",
     "National Volume (bcm) minus Official Volume (bcm). Reports the difference only, not its cause.",
     """VAR _off = [Official Volume (bcm)]
RETURN IF ( NOT ISBLANK ( _off ), [National Volume (bcm)] - _off )"""),
    ("Satellite ÷ Official", "Validation", "0.000",
     "National Volume (bcm) / Official Volume (bcm). Reports the ratio only, not its cause.",
     "DIVIDE ( [National Volume (bcm)], [Official Volume (bcm)] )"),
]
