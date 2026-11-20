"""Phase 3 step 8: write docs/phase3_model.md from the live FlareWatch model and
data/interim/phase3_validation.csv. Read-only against the model."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import model_spec as spec  # noqa: E402
from mcp_client import PBI  # noqa: E402

DOC = ROOT / "docs" / "phase3_model.md"
VAL = ROOT / "data" / "interim" / "phase3_validation.csv"
BACKUPS = ["FlareWatch_backup_20261120.pbix", "FlareWatch_backup_before_measures.pbix"]


def fmt(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "BLANK"
    v = float(v)
    if v.is_integer() and abs(v) >= 1:
        return f"{v:,.0f}"
    if abs(v) >= 1000:
        return f"{v:,.2f}"
    return f"{v:.6g}"


def main() -> None:
    pbi = PBI(readonly=True)
    try:
        rels = pbi.call("relationship_operations", operation="List")["data"]
        cols = {(t["tableName"], c["name"]): c
                for t in pbi.call("column_operations", operation="List")["data"] for c in t["columns"]}
        detail = pbi.call("column_operations", operation="Get",
                          references=[{"tableName": t, "name": c} for (t, c) in spec.FORMATS])
        for x in detail["results"]:  # List omits dataCategory; Get has it
            cols[(x["data"]["tableName"], x["data"]["name"])].update(
                {k: x["data"].get(k) for k in ("dataCategory", "formatString") if x["data"].get(k)})
        listed = pbi.call("measure_operations", operation="List")["data"]
        names = [m["name"] for t in listed for m in t["measures"]]
        got = pbi.call("measure_operations", operation="Get",
                       references=[{"tableName": spec.MEASURE_TABLE, "name": n} for n in names])
        measures = {r["data"]["name"]: r["data"] for r in got["results"]}
        tables = pbi.call("table_operations", operation="List")["data"]
        rule = pbi.dax(f"EVALUATE '{spec.RULE_TABLE}'")
    finally:
        pbi.close()

    val = pd.read_csv(VAL)
    n_pass, n_all = int(val["pass"].sum()), len(val)
    L: list[str] = []
    a = L.append
    a("# Phase 3: Power BI semantic model")
    a("")
    a("Date: 2026-11-20. Plan: [analysis_plan.md](analysis_plan.md), frozen v1.0. The plan's SHA-256 was checked "
      "against [plan_freeze.md](plan_freeze.md) before starting and matched. Amendments in force: A1, A2, A3 "
      "(see [amendments.md](amendments.md)).")
    a("")
    a("This document describes the model only. No report visuals were made. All flaring volumes are satellite "
      "**estimates** (NOAA, Payne Institute / Colorado School of Mines, World Bank GFMR).")
    a("")
    a("## 1. What was done")
    a("")
    a("1. **Backups** of the original `FlareWatch.pbix` (each byte-identical to the file at the "
      "time of copying):")
    a("")
    a("   | Backup in `powerbi/backup/` | SHA-256 |")
    a("   |---|---|")
    for b in BACKUPS:
        p = ROOT / "powerbi" / "backup" / b
        h = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "(backup not included in the public repo)"
        a(f"   | {b} | `{h}` |")
    a("")
    a("2. **Amendment A3** logged before applying: `dim_year` now runs 2012–2030 and has a new column "
      "`is_actual` (True 2012–2025, False 2026–2030). No values changed. Only `dim_year.csv` changed among the "
      "processed files; the other six are byte-identical. Tests: 29 of 29 pass (one new test for A3).")
    a("3. **MCP server** (Microsoft Power BI Modeling MCP, npm `@microsoft/powerbi-modeling-mcp@1.0.1`, pinned) "
      "switched to write mode in [.mcp.json](../.mcp.json). Claude Code had not loaded the server, so it was "
      "driven through [powerbi/mcp_client.py](../powerbi/mcp_client.py), which connects to the open Power BI "
      "Desktop window titled \"FlareWatch\". The Microsoft EULA was accepted on the user's instruction.")
    a("4. **Power Query sources** of all 7 tables repointed from a local `FlareWatch_data\\` folder "
      "to the project's `data/processed/` folder (same file names; in the public repo this folder is the "
      "Power Query parameter `DataFolder`). For "
      "`dim_year`, the column count was raised from 4 to 5 and `is_actual` typed as logical; the column was "
      "added to the model. Nothing else in the queries changed (they still use `Encoding=1252`; all processed "
      "CSVs are plain ASCII, so this has no effect). The user then refreshed in Power BI Desktop. Row counts "
      "after refresh: fact_site_year 6,664; dim_site 476; dim_year 19 (14 actual); dim_operator 40; dim_state "
      "38; param_assumptions 15; population_groups 38.")
    a("5. **Column settings, helper tables and measures** applied by "
      "[powerbi/phase3_build.py](../powerbi/phase3_build.py) from "
      "[powerbi/model_spec.py](../powerbi/model_spec.py).")
    a(f"6. **Validation** by [powerbi/phase3_validate.py](../powerbi/phase3_validate.py): DAX results compared "
      f"with pandas values from `data/processed/` and Phase 2b outputs. **{n_pass} of {n_all} checks pass.** "
      "Output: `data/interim/phase3_validation.csv`.")
    a("")
    a("## 2. Tables")
    a("")
    a("| Table | Type | Columns | Measures |")
    a("|---|---|---:|---:|")
    for t in tables:
        kind = "calculated (DAX)" if t["name"] in [c["name"] for c in spec.CALC_TABLES] else "import (CSV)"
        a(f"| {t['name']} | {kind} | {t['columnCount']} | {t.get('measureCount', 0)} |")
    a("")
    for t in spec.CALC_TABLES:
        a(f"- **{t['name']}**: `{t['daxExpression']}`. {t['description']}")
    a(f"- Rows of '{spec.RULE_TABLE}': " + "; ".join(f"{r['Rule']} → {r['Min Years']}" for r in rule) + ".")
    a("")
    a("## 3. Relationships")
    a("")
    a("All were auto-detected by Power BI and are unchanged. Plan s9.1 lists the first four; the fifth links "
      "the precomputed population table to states.")
    a("")
    a("| From (many) | To (one) | Cardinality | Filter direction | Active |")
    a("|---|---|---|---|---|")
    for r in rels:
        a(f"| {r['fromTable']}[{r['fromColumn']}] | {r['toTable']}[{r['toColumn']}] | "
          f"{r['fromCardinality']}-to-{r['toCardinality']} | "
          f"{'single' if r['crossFilteringBehavior'] == 'OneDirection' else r['crossFilteringBehavior']} | "
          f"{'yes' if r['isActive'] else 'no'} |")
    a("")
    a("`population_groups` has rows with state \"All\", which match no `dim_state` row. The Residents measures "
      "handle this (section 5).")
    a("")
    a("## 4. Column settings")
    a("")
    a("### Hidden from report view")
    a("")
    a("| Table | Column | Hidden in model |")
    a("|---|---|---|")
    for t, cs in spec.HIDDEN.items():
        for c in cs:
            a(f"| {t} | {c} | {'yes' if cols[(t, c)].get('isHidden') else 'NO'} |")
    a(f"| {spec.MEASURE_TABLE} | _ (placeholder) | {'yes' if cols.get((spec.MEASURE_TABLE, '_'), {}).get('isHidden') else 'NO'} |")
    a("")
    a("`state_iso` and `state_id` are hidden in both `dim_site` and `dim_state`.")
    a("")
    a("### Summarize by = None")
    a("")
    a("| Table | Column | Summarize by (model) |")
    a("|---|---|---|")
    for t, cs in spec.NO_SUM.items():
        for c in cs:
            a(f"| {t} | {c} | {cols[(t, c)].get('summarizeBy')} |")
    a("")
    a("`fact_site_year[bcm]` and `[mmscfd]` keep Sum.")
    a("")
    a("### Formats and data categories")
    a("")
    a("| Table | Column | Format | Data category |")
    a("|---|---|---|---|")
    for (t, c), f in spec.FORMATS.items():
        a(f"| {t} | {c} | `{cols[(t, c)].get('formatString')}` | {cols[(t, c)].get('dataCategory', '')} |")
    a("")
    a("**Sort:** `flare_level` keeps alphabetical order (Large, Medium, Small). A calculated sort column "
      "derived from `flare_level` in the same table was rejected by Power BI (circular dependency) and was "
      "removed. A Small/Medium/Large order would need an order column in the CSV, which would need an "
      "amendment. Other text columns sort alphabetically and years numerically, which is the intended order.")
    a("")
    a("## 5. Measures")
    a("")
    a(f"All {len(measures)} measures are in table `{spec.MEASURE_TABLE}`. Parameter values (conversions, CO2e "
      "factor, prices, flare fee rates, persistence threshold) are read from `param_assumptions` with "
      "`LOOKUPVALUE`, not hard-coded. The only literal years are those named in the spec: 2012, 2023 "
      "(change baselines) and 2025–2030 (illustrative path). Check values are 2025 unless stated.")
    a("")
    a("Notes:")
    a("")
    a("- **Flare Volume (bcm)** returns BLANK for 2026–2030 (`is_actual` = False), so every measure built on it "
      "is BLANK there too.")
    a("- **National Volume (bcm)** uses `ALLEXCEPT(fact_site_year, dim_year)`: only year filters are kept. A "
      "first version used `REMOVEFILTERS(fact_site_year)`, which also removed the year filter (expanded table); "
      "validation caught it and it was fixed before the checks below.")
    a("- **Residents within 2 km / 5 km** cannot be summed from sites (buffers overlap). They read the "
      "precomputed unions in `population_groups` for one group (`active_2025` by default, or the selected "
      "`population_groups[group]`) and either all states or exactly one selected state. They return BLANK if "
      "several states are selected or a site or operator filter is applied, because no union is precomputed "
      "for those selections.")
    a("- **Top 10 Fields Share** includes the \"Unattributed field\" group in the ranking, because plan s9.3 "
      "sets an exclusion only for operators.")
    a("- **Persistent Sites** follows the 'Persistence Rule' slicer; with no selection it uses "
      "`persistent_min_years` (12) from `param_assumptions`.")
    a("")
    for folder in ["Volume", "Sites", "Concentration", "Cost", "People", "Validation"]:
        a(f"### {folder}")
        a("")
        for name, f, fs, desc, _ in [m for m in spec.MEASURES if m[1] == folder]:
            m = measures[name]
            v = val[val["measure"] == name]
            status = "PASS" if len(v) and v["pass"].all() else ("FAIL" if len(v) else "no check")
            a(f"#### {name}")
            a("")
            a(f"- Display folder: {m.get('displayFolder')}. Format: `{m.get('formatString')}`.")
            a(f"- Description: {m.get('description')}")
            a("- DAX:")
            a("")
            a("  ```dax")
            for line in m["expression"].split("\n"):
                a(f"  {line}")
            a("  ```")
            a("")
            a(f"- Checks: **{status}** ({int(v['pass'].sum())} of {len(v)})")
            a("")
            if len(v) <= 6:
                a("  | Check | DAX | Python | Pass |")
                a("  |---|---:|---:|---|")
                for _, r in v.iterrows():
                    a(f"  | {r['check']} | {fmt(r['dax'])} | {fmt(r['python'])} | {'yes' if r['pass'] else 'NO'} |")
            else:
                shown = v[v["python"].notna()]
                blanks = v[v["python"].isna()]
                a("  | Check | DAX | Python | Pass |")
                a("  |---|---:|---:|---|")
                for _, r in shown.iterrows():
                    a(f"  | {r['check']} | {fmt(r['dax'])} | {fmt(r['python'])} | {'yes' if r['pass'] else 'NO'} |")
                if len(blanks):
                    a(f"  | {', '.join(blanks['check'].astype(str))} | BLANK | BLANK | "
                      f"{'yes' if blanks['pass'].all() else 'NO'} |")
            a("")
    a("## 6. Validation summary (task step 7)")
    a("")
    a("Tolerances: 0.001 bcm (and 0.001 Mt CO2e), exact for counts and years, 1 USD, 1 person, 1e-9 for shares "
      "and ratios.")
    a("")
    key = [("Flare Volume (bcm)", None, "National bcm by year 2012–2025 (and BLANK 2026–2030)"),
           ("Active Sites", "2025", "Active sites 2025"),
           ("Persistent Sites (12 of 14)", "all", "Persistent sites (12 of 14)"),
           ("Top 10 Sites Share", "2025", "Top-10 site share 2025"),
           ("CO2e (Mt)", "2025", "CO2e 2025 (Mt)"),
           ("Gas Value Low (USD)", "2025", "Gas value low 2025"),
           ("Gas Value Central (USD)", "2025", "Gas value central 2025"),
           ("Gas Value High (USD)", "2025", "Gas value high 2025"),
           ("Implied Flare Fee Low (USD)", "2025", "Implied flare fee low 2025"),
           ("Implied Flare Fee High (USD)", "2025", "Implied flare fee high 2025")]
    a("| Item | DAX | Python | Pass |")
    a("|---|---:|---:|---|")
    for mname, check, label in key:
        v = val[val["measure"] == mname]
        if check is None:
            a(f"| {label} | {int(v['pass'].sum())} of {len(v)} years match | — | "
              f"{'yes' if v['pass'].all() else 'NO'} |")
        else:
            r = v[v["check"] == check].iloc[0]
            a(f"| {label} | {fmt(r['dax'])} | {fmt(r['python'])} | {'yes' if r['pass'] else 'NO'} |")
    a("")
    a(f"All checks: **{n_pass} of {n_all} pass.**")
    a("")
    a("## 7. Model additions after Phase 3 (page 1 night redesign, 2026-11-20)")
    a("")
    a("Added only where missing; no existing measure changed. Written into the PBIP TMDL "
      "(`_Measures.tmdl`) by [powerbi/tmdl_add_measures.py](../powerbi/tmdl_add_measures.py) while Power BI "
      "Desktop was closed, then checked in the open model by phase3_validate.py (section 5).")
    a("")
    a("| Requested | Result |")
    a("|---|---|")
    a("| YoY Change Selected Year (%) | Added (folder Volume, format `▲ 0.0%;▼ 0.0%;0.0%`). |")
    a("| CO2e Selected Year (Mt) | Added (folder Cost, format `#,##0.0`). |")
    a("| Flare Volume Selected Year by state | Not added: the existing `Flare Volume Selected Year (bcm)` "
      "already returns per-state values when sliced by `dim_state[state]` (filter flows dim_state → dim_site → "
      "fact_site_year). Checked per state against pandas (section 5). |")
    a("| Volume Column Colour (polish round 2) | Added (folder Volume, text, no format string). Formatting "
      "helper for the conditional column colour of \"Gas flared each year\": \"#FF7A1A\" for 2025, \"#9C4519\" "
      "otherwise. Not a data value. |")
    a("| Flare Volume excl 2025 (bcm) and Flare Volume 2025 only (bcm) (final fix) | Added (folder Volume). "
      "Chart helpers: two stacked column series so 2025 has its own colour; checked to sum to Flare Volume "
      "(bcm) for every year 2012–2030 (section 5). |")
    a("| Site Passes Persistence Rule (pages 2–6) | Added (folder Sites). Filter helper for the Sites page: 1 if "
      "the site meets the rule chosen in the 'Persistence Rule' slicer (all sites when none chosen). Checked: "
      "476 / 218 / 171 / 133 sites for none / 10 / 12 / 14 of 14 (section 5). |")
    a("| Residents within 5 km of persistent sites (pages 2–6) | Added (folder People). Group fixed to "
      "'persistent'. Added because of a defect found in the existing `Residents within 5 km`: when the selected "
      "group has no row for a state, `SELECTEDVALUE(population_groups[group], \"active_2025\")` falls back to "
      "the active-2025 row (e.g. Kaduna showed 1,739 under 'persistent'). The existing measure was not changed "
      "(additions only); the People page uses the new measure for its by-state chart. Checked per state "
      "against population_groups.csv (section 5). |")
    a("| **Model fix (Phase 4): Residents within 2 km / Residents within 5 km** | Fixed (a model fix, not a plan "
      "amendment). The group is now read with the state filter removed: `VAR _g = CALCULATE ( SELECTEDVALUE ( "
      "population_groups[group], \"active_2025\" ), REMOVEFILTERS ( dim_state ) )`. Before, a state with no row "
      "for the selected group fell back to the active-2025 row (Kaduna showed 1,739 under 'persistent'); now it "
      "returns BLANK. Checked for every state, both groups and both buffers against population_groups.csv "
      "(section 5). The People cards use these measures; no other change. |")
    a("| Assumption Source (short) (Phase 4) | Added (folder Cost, text). Display helper: a source label of 8 words "
      "or fewer for each parameter, used by the Cost page assumptions table; full sources stay in "
      "param_assumptions and on the Methods page. Checked: all 15 parameters labelled, all ≤ 8 words. |")
    a("| Active Sites Label Points (polish round 2) | Added (folder Sites). Chart helper: Active Sites for 2021 "
      "and 2025 only, BLANK otherwise; an invisible series so only those points are labelled. |")
    a("")
    a("## 8. Open items")
    a("")
    a("- Save the file in Power BI Desktop (**File > Save**). Model changes made through the MCP server live in "
      "the open session until saved.")
    a("- No report visuals yet. The `trace` table in plan s9.1 is not built yet.")
    a("- `flare_level` sort order (section 4).")
    DOC.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", DOC.relative_to(ROOT))


if __name__ == "__main__":
    main()
