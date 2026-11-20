"""Phase 3 step 7: check DAX measures in the open FlareWatch model against values computed in
pandas from data/processed (and Phase 2b outputs). Writes data/interim/phase3_validation.csv.
Tolerances: 0.001 bcm, exact counts, 1 USD (plan s6 item 3)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from mcp_client import PBI  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
INTERIM = ROOT / "data" / "interim"
OUT = INTERIM / "phase3_validation.csv"

TOL = {"bcm": 0.001, "count": 0, "usd": 1.0, "share": 1e-9, "mt": 0.001, "mmbtu": 1.0, "pop": 1.0,
       "ratio": 1e-9, "year": 0, "mscf": 1.0, "m3": 0.001, "bcf": 0.001}


def expected() -> dict:
    fact = pd.read_csv(PROCESSED / "fact_site_year.csv")
    site = pd.read_csv(PROCESSED / "dim_site.csv", keep_default_na=False, na_values=[""])
    year = pd.read_csv(PROCESSED / "dim_year.csv")
    groups = pd.read_csv(PROCESSED / "population_groups.csv", keep_default_na=False)
    prm = pd.read_csv(PROCESSED / "param_assumptions.csv").set_index("parameter")["value"]
    sanity = pd.read_csv(INTERIM / "phase2b_sanity_2025.csv").set_index("check")["value"]
    recomp = pd.read_csv(INTERIM / "phase2b_recompute_comparison.csv", keep_default_na=False)

    nat = fact.groupby("year")["bcm"].sum()
    f25 = fact[fact["year"] == 2025].merge(site, on="site_id")
    e: dict = {}
    for y, v in nat.items():
        e[f"national_bcm_{y}"] = v
    b25 = nat[2025]
    e["active_sites_2025"] = int((fact[fact["year"] == 2025]["bcm"] > 0).sum())
    e["persistent_12"] = int(site["persistent"].sum())
    e["persistent_10"] = int(site["persistent_10"].sum())
    e["persistent_14"] = int(site["persistent_14"].sum())
    e["top10_site_share_2025"] = float(recomp.loc[recomp["metric"] == "top10_site_share_2025", "recompute"].iloc[0])

    def top10(col, exclude=None):
        g = f25.groupby(col)["bcm"].sum().reset_index()
        if exclude:
            g = g[g[col] != exclude]
        g = g.sort_values(["bcm", col], ascending=[False, True]).head(10)
        return g["bcm"].sum() / b25

    e["top10_field_share_2025"] = top10("field")
    e["top10_operator_share_2025"] = top10("operator_clean", "Unattributed")
    e["co2e_mt_2025"] = sanity["co2e_mt_2025"]
    e["energy_mmbtu_2025"] = sanity["energy_mmbtu_2025"]
    for k in ["gas_value_low_usd_2025", "gas_value_central_usd_2025", "gas_value_high_usd_2025",
              "implied_flare_fee_low_usd_2025", "implied_flare_fee_high_usd_2025"]:
        e[k] = sanity[k]
    e["million_m3_2025"] = b25 * prm["bcm_to_million_m3"]
    e["mscf_2025"] = sanity["mscf_2025"]
    e["bcf_2025"] = b25 * prm["bcm_to_bcf"]
    e["recent_volume_bcm"] = fact[fact["year"].isin([2023, 2024, 2025])]["bcm"].sum() / 3
    e["recent_volume_sum_of_sites"] = site["recent_volume_bcm"].sum()
    e["yoy_bcm_2025"] = nat[2025] - nat[2024]
    e["yoy_pct_2025"] = (nat[2025] - nat[2024]) / nat[2024]
    e["unattributed_bcm_2025"] = f25.loc[f25["operator_clean"] == "Unattributed", "bcm"].sum()
    e["share_rivers_2025"] = f25.loc[f25["state"] == "Rivers", "bcm"].sum() / b25
    e["selected_year_default"] = 2025
    e["selected_year_2012_2020"] = 2020
    e["change_since_2012"] = (b25 - nat[2012]) / nat[2012]
    e["change_since_2023"] = (b25 - nat[2023]) / nat[2023]
    for y in range(2025, 2031):
        e[f"path_{y}"] = b25 * (2030 - y) / 5
    sid = "s_38320"
    e["active_years_s_38320"] = int(site.set_index("site_id").loc[sid, "active_years"])
    top_site = site.sort_values(["active_years", "site_id"], ascending=[False, True]).iloc[0]["site_id"]
    e["_top_site"] = top_site
    e[f"active_years_top_site"] = int(site.set_index("site_id").loc[top_site, "active_years"])
    e["pop5_site_s_38320"] = float(site.set_index("site_id").loc[sid, "pop_5km"])
    g = groups.set_index(["group", "state", "buffer_km"])["pop_union"]
    e["res2_active_all"] = g[("active_2025", "All", 2)]
    e["res5_active_all"] = g[("active_2025", "All", 5)]
    e["res5_persistent_all"] = g[("persistent", "All", 5)]
    e["res2_active_rivers"] = g[("active_2025", "Rivers", 2)]
    e["co2e_mt_2020"] = nat[2020] * prm["co2e_mt_per_bcm"]
    e["state_bcm_2025"] = f25.groupby("state")["bcm"].sum().to_dict()
    y = year.set_index("year")
    for yr in range(2021, 2026):
        e[f"official_{yr}"] = y.loc[yr, "official_bcm"]
        e[f"sat_minus_off_{yr}"] = nat[yr] - y.loc[yr, "official_bcm"]
        e[f"sat_over_off_{yr}"] = nat[yr] / y.loc[yr, "official_bcm"]
    return e


def num(x):
    return None if x in ("", None) else float(x)


def main() -> None:
    e = expected()
    pbi = PBI()
    rows = []

    def add(measure, check, kind, got, exp):
        if exp is None:
            ok = got is None
            diff = None
        else:
            diff = None if got is None else abs(got - float(exp))
            ok = diff is not None and diff <= TOL[kind]
        rows.append({"measure": measure, "check": check, "dax": got, "python": exp,
                     "abs_diff": diff, "tolerance": TOL.get(kind), "pass": ok})

    def one(expr, filt=""):
        q = f'EVALUATE ROW("v", CALCULATE({expr}{", " + filt if filt else ""}))'
        res = pbi.dax(q)
        return num(res[0]["v"]) if res else None

    try:
        # national bcm by year 2012-2030 (2026-2030 must be BLANK)
        by_year = {int(r["year"]): num(r["v"]) for r in pbi.dax(
            'EVALUATE ADDCOLUMNS(VALUES(dim_year[year]), "v", [Flare Volume (bcm)])')}
        for yr in range(2012, 2031):
            add("Flare Volume (bcm)", f"national {yr}", "bcm", by_year[yr], e.get(f"national_bcm_{yr}"))
        nat_year = {int(r["year"]): num(r["v"]) for r in pbi.dax(
            'EVALUATE CALCULATETABLE(ADDCOLUMNS(VALUES(dim_year[year]), "v", [National Volume (bcm)]), '
            'dim_state[state] = "Rivers")')}
        add("National Volume (bcm)", "2025 with state filter Rivers (filter ignored)", "bcm", nat_year[2025],
            e["national_bcm_2025"])
        f25 = 'dim_year[year] = 2025'
        add("Flare Volume (million m3)", "2025", "m3", one("[Flare Volume (million m3)]", f25), e["million_m3_2025"])
        add("Flare Volume (Mscf)", "2025", "mscf", one("[Flare Volume (Mscf)]", f25), e["mscf_2025"])
        add("Flare Volume (bcf)", "2025", "bcf", one("[Flare Volume (bcf)]", f25), e["bcf_2025"])
        add("Share of National", "2025, state Rivers", "share",
            one("[Share of National]", f25 + ', dim_state[state] = "Rivers"'), e["share_rivers_2025"])
        add("Recent Volume (bcm)", "national (mean 2023-2025)", "bcm", one("[Recent Volume (bcm)]"),
            e["recent_volume_bcm"])
        add("Recent Volume (bcm)", "= sum of dim_site[recent_volume_bcm]", "bcm", one("[Recent Volume (bcm)]"),
            e["recent_volume_sum_of_sites"])
        add("YoY Change (bcm)", "2025 vs 2024", "bcm", one("[YoY Change (bcm)]", f25), e["yoy_bcm_2025"])
        add("YoY Change (%)", "2025 vs 2024", "share", one("[YoY Change (%)]", f25), e["yoy_pct_2025"])
        add("YoY Change (bcm)", "2012 (no previous year) is BLANK", "bcm",
            one("[YoY Change (bcm)]", "dim_year[year] = 2012"), None)
        add("Unattributed Volume (bcm)", "2025", "bcm", one("[Unattributed Volume (bcm)]", f25),
            e["unattributed_bcm_2025"])
        add("Selected Year", "no selection", "year", one("[Selected Year]"), 2025)
        add("Selected Year", "selection 2012-2020", "year",
            one("[Selected Year]", "dim_year[year] <= 2020"), 2020)
        add("Selected Year", "selection 2026-2030 only (falls back to latest actual)", "year",
            one("[Selected Year]", "dim_year[year] >= 2026"), 2025)
        add("Flare Volume Selected Year (bcm)", "no selection (2025)", "bcm",
            one("[Flare Volume Selected Year (bcm)]"), e["national_bcm_2025"])
        add("Change since 2012 (%)", "no selection (2025)", "share", one("[Change since 2012 (%)]"),
            e["change_since_2012"])
        add("Change since 2023 (%)", "no selection (2025)", "share", one("[Change since 2023 (%)]"),
            e["change_since_2023"])
        # page 1 redesign additions
        add("YoY Change Selected Year (%)", "no selection (2025 vs 2024)", "share",
            one("[YoY Change Selected Year (%)]"), e["yoy_pct_2025"])
        add("YoY Change Selected Year (%)", "2012 selected (no 2011) is BLANK", "share",
            one("[YoY Change Selected Year (%)]", "dim_year[year] = 2012"), None)
        add("CO2e Selected Year (Mt)", "no selection (2025)", "mt", one("[CO2e Selected Year (Mt)]"),
            e["co2e_mt_2025"])
        add("CO2e Selected Year (Mt)", "2020 selected", "mt",
            one("[CO2e Selected Year (Mt)]", "dim_year[year] = 2020"), e["co2e_mt_2020"])
        stacked = {int(r["year"]): (num(r["a"]), num(r["b"])) for r in pbi.dax(
            'EVALUATE ADDCOLUMNS(VALUES(dim_year[year]), "a", [Flare Volume excl 2025 (bcm)], '
            '"b", [Flare Volume 2025 only (bcm)])')}
        for yr in range(2012, 2031):
            a_, b_ = stacked[yr]
            tot = None if a_ is None and b_ is None else (a_ or 0) + (b_ or 0)
            add("Flare Volume excl 2025 (bcm)", f"excl + 2025-only = national {yr}", "bcm", tot,
                e.get(f"national_bcm_{yr}"))
        add("Flare Volume 2025 only (bcm)", "2024 is BLANK", "bcm", stacked[2024][1], None)
        add("Flare Volume excl 2025 (bcm)", "2025 is BLANK", "bcm", stacked[2025][0], None)
        pg = pd.read_csv(PROCESSED / "population_groups.csv", keep_default_na=False)
        p5 = pg[(pg["group"] == "persistent") & (pg["buffer_km"] == 5)].set_index("state")["pop_union"]
        pers = {r["state"]: num(r["v"]) for r in pbi.dax(
            'EVALUATE ADDCOLUMNS(VALUES(dim_state[state]), "v", [Residents within 5 km of persistent sites])')}
        add("Residents within 5 km of persistent sites", "all states", "pop",
            one("[Residents within 5 km of persistent sites]"), float(p5["All"]))
        for st in sorted(pers):
            add("Residents within 5 km of persistent sites", f"state {st}", "pop", pers[st],
                float(p5[st]) if st in p5.index else None)
        # Phase 4 fix: original Residents measures, per state and group (no fallback to another group)
        for km in (2, 5):
            for grp in ("active_2025", "persistent"):
                ref = pg[(pg["group"] == grp) & (pg["buffer_km"] == km)].set_index("state")["pop_union"]
                got = {r["state"]: num(r["v"]) for r in pbi.dax(
                    f'EVALUATE CALCULATETABLE(ADDCOLUMNS(VALUES(dim_state[state]), "v", '
                    f'[Residents within {km} km]), population_groups[group] = "{grp}")')}
                for st in sorted(got):
                    add(f"Residents within {km} km", f"{grp}, state {st}", "pop", got[st],
                        float(ref[st]) if st in ref.index else None)
        short = pbi.dax('EVALUATE ADDCOLUMNS(VALUES(param_assumptions[parameter]), "s", '
                        '[Assumption Source (short)])')
        rows.append({"measure": "Assumption Source (short)", "check": "every parameter has a label of <= 8 words",
                     "dax": None, "python": None, "abs_diff": None, "tolerance": None,
                     "pass": len(short) == 15 and all(r["s"] and len(r["s"].split()) <= 8 for r in short)})
        passes = 'COUNTROWS(FILTER(VALUES(dim_site[site_id]), [Site Passes Persistence Rule] = 1))'
        add("Site Passes Persistence Rule", "no rule selected: all sites", "count", one(passes), 476)
        for r, k in [(10, "persistent_10"), (12, "persistent_12"), (14, "persistent_14")]:
            add("Site Passes Persistence Rule", f"rule {r} of 14", "count",
                one(passes, f"'Persistence Rule'[Min Years] = {r}"), e[k])
        for yr, exp in [(2021, 381), (2025, 259), (2024, None)]:
            add("Active Sites Label Points", str(yr), "count",
                one("[Active Sites Label Points]", f"dim_year[year] = {yr}"), exp)
        for yr, exp in [(2025, "#FF7A1A"), (2024, "#9C4519")]:
            res = pbi.dax(f'EVALUATE ROW("v", CALCULATE([Volume Column Colour], dim_year[year] = {yr}))')
            got = res[0]["v"] if res else None
            rows.append({"measure": "Volume Column Colour", "check": f"{yr} returns {exp}", "dax": None,
                         "python": None, "abs_diff": None, "tolerance": None, "pass": got == exp})
        by_state = {r["state"]: num(r["v"]) for r in pbi.dax(
            'EVALUATE CALCULATETABLE(ADDCOLUMNS(VALUES(dim_state[state]), "v", '
            '[Flare Volume Selected Year (bcm)]), dim_year[year] = 2025)')}
        for st, v in sorted(e["state_bcm_2025"].items(), key=lambda kv: -kv[1]):
            add("Flare Volume Selected Year (bcm)", f"by state 2025: {st}", "bcm", by_state.get(st), v)
        no_sites = [s for s, v in by_state.items() if s not in e["state_bcm_2025"]]
        add("Flare Volume Selected Year (bcm)", "states with no sites are BLANK", "count",
            float(sum(by_state[s] is not None for s in no_sites)), 0)
        path = {int(r["year"]): num(r["v"]) for r in pbi.dax(
            'EVALUATE ADDCOLUMNS(VALUES(dim_year[year]), "v", [Illustrative Path 2030 (bcm)])')}
        for yr in range(2012, 2031):
            add("Illustrative Path 2030 (bcm)", str(yr), "bcm", path[yr], e.get(f"path_{yr}"))

        add("Active Sites", "2025", "count", one("[Active Sites]", f25), e["active_sites_2025"])
        add("Active Sites Selected Year", "no selection (2025)", "count", one("[Active Sites Selected Year]"),
            e["active_sites_2025"])
        add("Active Sites", "2026 is BLANK", "count", one("[Active Sites]", "dim_year[year] = 2026"), None)
        add("Persistent Sites", "default rule (12 of 14)", "count", one("[Persistent Sites]"), e["persistent_12"])
        add("Persistent Sites", "rule 10 of 14", "count",
            one("[Persistent Sites]", "'Persistence Rule'[Min Years] = 10"), e["persistent_10"])
        add("Persistent Sites", "rule 14 of 14", "count",
            one("[Persistent Sites]", "'Persistence Rule'[Min Years] = 14"), e["persistent_14"])
        add("Persistent Sites (12 of 14)", "all", "count", one("[Persistent Sites (12 of 14)]"), e["persistent_12"])
        add("Active Years", "site s_38320", "count",
            one("[Active Years]", 'dim_site[site_id] = "s_38320"'), e["active_years_s_38320"])
        add("Active Years", f"site {e['_top_site']} (year filter 2025 ignored)", "count",
            one("[Active Years]", f'dim_site[site_id] = "{e["_top_site"]}", ' + f25), e["active_years_top_site"])

        add("Top 10 Sites Share", "2025", "share", one("[Top 10 Sites Share]", f25), e["top10_site_share_2025"])
        add("Top 10 Fields Share", "2025", "share", one("[Top 10 Fields Share]", f25), e["top10_field_share_2025"])
        add("Top 10 Operators Share", "2025 (Unattributed excluded)", "share",
            one("[Top 10 Operators Share]", f25), e["top10_operator_share_2025"])

        add("CO2e (Mt)", "2025", "mt", one("[CO2e (Mt)]", f25), e["co2e_mt_2025"])
        add("Gas Energy (MMBtu)", "2025", "mmbtu", one("[Gas Energy (MMBtu)]", f25), e["energy_mmbtu_2025"])
        for m, k in [("Gas Value Low (USD)", "gas_value_low_usd_2025"),
                     ("Gas Value Central (USD)", "gas_value_central_usd_2025"),
                     ("Gas Value High (USD)", "gas_value_high_usd_2025"),
                     ("Implied Flare Fee Low (USD)", "implied_flare_fee_low_usd_2025"),
                     ("Implied Flare Fee High (USD)", "implied_flare_fee_high_usd_2025")]:
            add(m, "2025", "usd", one(f"[{m}]", f25), e[k])

        add("Residents within 2 km", "active_2025, all states (default)", "pop",
            one("[Residents within 2 km]"), e["res2_active_all"])
        add("Residents within 5 km", "active_2025, all states (default)", "pop",
            one("[Residents within 5 km]"), e["res5_active_all"])
        add("Residents within 5 km", "persistent, all states", "pop",
            one("[Residents within 5 km]", 'population_groups[group] = "persistent"'), e["res5_persistent_all"])
        add("Residents within 2 km", "active_2025, Rivers", "pop",
            one("[Residents within 2 km]", 'dim_state[state] = "Rivers"'), e["res2_active_rivers"])
        add("Residents within 2 km", "two states selected is BLANK", "pop",
            one("[Residents within 2 km]", 'dim_state[state] IN {"Rivers", "Delta"}'), None)
        add("Residents within 2 km", "site filter applied is BLANK", "pop",
            one("[Residents within 2 km]", 'dim_site[site_id] = "s_38320"'), None)
        add("Residents within 5 km (per site)", "site s_38320", "pop",
            one("[Residents within 5 km (per site)]", 'dim_site[site_id] = "s_38320"'), e["pop5_site_s_38320"])

        for yr in range(2021, 2026):
            fy = f"dim_year[year] = {yr}"
            add("Official Volume (bcm)", str(yr), "bcm", one("[Official Volume (bcm)]", fy), e[f"official_{yr}"])
            add("Satellite − Official (bcm)", str(yr), "bcm", one("[Satellite − Official (bcm)]", fy),
                e[f"sat_minus_off_{yr}"])
            add("Satellite ÷ Official", str(yr), "ratio", one("[Satellite ÷ Official]", fy),
                e[f"sat_over_off_{yr}"])
        add("Official Volume (bcm)", "2020 is BLANK", "bcm", one("[Official Volume (bcm)]", "dim_year[year] = 2020"),
            None)
        add("Official Volume (bcm)", "2020-2025 selected is BLANK (2020 has none)", "bcm",
            one("[Official Volume (bcm)]", "dim_year[year] >= 2020 && dim_year[year] <= 2025"), None)
    finally:
        pbi.close()

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"{int(df['pass'].sum())}/{len(df)} checks pass")
    if not df["pass"].all():
        print(df[~df["pass"]].to_string())


if __name__ == "__main__":
    main()
