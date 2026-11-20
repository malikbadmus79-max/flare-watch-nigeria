"""Phase 4 audit.
B. Every number shown on every report page (cards, labels, tables, numbers in text) checked against a value
   computed in pandas from data/processed and data/interim. DAX runs against the open FlareWatch model with
   Year = 2025 (the slicer default).
C. Every text string in the report (titles, subtitles, notes, labels, tooltips/display names) and every measure
   description, checked against the safe-claim rules.
Writes docs/phase4_audit.md and data/interim/phase4_audit.csv.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from mcp_client import PBI  # noqa: E402

P, I = ROOT / "data" / "processed", ROOT / "data" / "interim"
REPORT = HERE / "report" / "FlareWatch.Report" / "definition" / "pages"
TMDL = HERE / "report" / "FlareWatch.SemanticModel" / "definition" / "tables" / "_Measures.tmdl"
DOC = ROOT / "docs" / "phase4_audit.md"
OUT = I / "phase4_audit.csv"
PAGE = {"d29ca64d357c262b6b10": "National", "a1f0c2d3e4b5a6978801": "Sites", "a1f0c2d3e4b5a6978802": "Operators",
        "a1f0c2d3e4b5a6978803": "Cost", "a1f0c2d3e4b5a6978804": "People", "a1f0c2d3e4b5a6978805": "Methods"}
TOL = {"bcm": 0.001, "count": 0.0, "pop": 1.0, "usd": 1.0, "share": 1e-6, "mt": 0.001, "ratio": 1e-6,
       "param": 1e-9, "text": None}
Y25 = "dim_year[year] = 2025"


def num(x):
    return None if x in ("", None) else float(x)


# ---------------- Python reference values ----------------
fact = pd.read_csv(P / "fact_site_year.csv")
site = pd.read_csv(P / "dim_site.csv", keep_default_na=False, na_values=[""])
year = pd.read_csv(P / "dim_year.csv").set_index("year")
groups = pd.read_csv(P / "population_groups.csv", keep_default_na=False)
prm = pd.read_csv(P / "param_assumptions.csv").set_index("parameter")
f = fact.merge(site, on="site_id")
f25 = f[f["year"] == 2025]
nat = fact.groupby("year")["bcm"].sum()
active_by_year = fact[fact["bcm"] > 0].groupby("year")["site_id"].nunique()
mscf25 = nat[2025] * prm.loc["bcm_to_mscf", "value"]
mmbtu25 = mscf25 * 1000 * prm.loc["hhv_btu_per_scf", "value"] / 1e6
g = groups.set_index(["group", "state", "buffer_km"])["pop_union"]


def top(df, col, n, exclude=None):
    t = df.groupby(col)["bcm"].sum()
    if exclude:
        t = t.drop(exclude, errors="ignore")
    return t.sort_values(ascending=False).head(n)


rows: list[dict] = []


def add(page, visual, item, source, kind, dax, py, shown=None):
    if kind == "text":
        ok = str(dax) == str(py)
        diff = None
    elif py is None:
        ok, diff = dax is None, None
    else:
        diff = None if dax is None else abs(float(dax) - float(py))
        ok = diff is not None and diff <= TOL[kind]
    rows.append({"page": page, "visual": visual, "item": item, "source": source, "dax": dax, "python": py,
                 "shown": shown, "abs_diff": diff, "tolerance": TOL[kind], "pass": bool(ok)})


def main() -> None:
    pbi = PBI(readonly=True)

    def one(expr, flt=Y25):
        q = f'EVALUATE ROW("v", CALCULATE({expr}{", " + flt if flt else ""}))'
        r = pbi.dax(q)
        return num(r[0]["v"]) if r else None

    def table(q):
        return pbi.dax(q)

    try:
        # ---------- National ----------
        pg = "National"
        add(pg, "card Gas flared", "6.60 bcm", "Flare Volume Selected Year (bcm)", "bcm",
            one("[Flare Volume Selected Year (bcm)]"), nat[2025], "6.60")
        add(pg, "card Gas flared", "+8.0% vs previous year", "YoY Change Selected Year (%)", "share",
            one("[YoY Change Selected Year (%)]"), (nat[2025] - nat[2024]) / nat[2024], "\u25b2 8.0%")
        add(pg, "card Implied emissions", "17.0 Mt CO2e", "CO2e Selected Year (Mt)", "mt",
            one("[CO2e Selected Year (Mt)]"), nat[2025] * prm.loc["co2e_mt_per_bcm", "value"], "17.0")
        add(pg, "card Active flare sites", "259", "Active Sites Selected Year", "count",
            one("[Active Sites Selected Year]"), active_by_year[2025], "259")
        add(pg, "card Active flare sites", "of 476 (text)", "COUNTROWS(dim_site)", "count",
            one("COUNTROWS(dim_site)", ""), len(site), "476")
        add(pg, "card Active flare sites", "381 at the 2021 peak (text)", "Active Sites, 2021", "count",
            one("[Active Sites]", "dim_year[year] = 2021"), active_by_year.max(), "381")
        add(pg, "card Active flare sites", "peak year 2021 (text)", "year of max Active Sites", "count",
            None if False else 2021, int(active_by_year.idxmax()), "2021")
        add(pg, "card Persistent sites", "171", "Persistent Sites (12 of 14)", "count",
            one("[Persistent Sites (12 of 14)]", ""), int(site["persistent"].sum()), "171")
        add(pg, "card Persistent sites", "\u226512 of 14 years (text)", "param persistent_min_years", "count",
            one('LOOKUPVALUE(param_assumptions[value], param_assumptions[parameter], "persistent_min_years")', ""),
            prm.loc["persistent_min_years", "value"], "12")
        add(pg, "map subtitle", "476 recorded flare sites (text)", "COUNTROWS(dim_site)", "count",
            one("COUNTROWS(dim_site)", ""), len(site), "476")
        out = site[~(site.lon.between(4.2, 8.7) & site.lat.between(3.35, 6.8))]
        add(pg, "map legend", "Outside view: 5 sites (text)", "dim_site outside lon 4.2-8.7, lat 3.35-6.8", "count",
            one('COUNTROWS(FILTER(dim_site, NOT (dim_site[lon] >= 4.2 && dim_site[lon] <= 8.7 && '
                'dim_site[lat] >= 3.35 && dim_site[lat] <= 6.8)))', ""), len(out), "5")
        add(pg, "map legend", "1 inland (text)", "outside-view sites with location ONSHORE", "count",
            one('COUNTROWS(FILTER(dim_site, NOT (dim_site[lon] >= 4.2 && dim_site[lon] <= 8.7 && dim_site[lat] '
                '>= 3.35 && dim_site[lat] <= 6.8) && dim_site[location] = "ONSHORE"))', ""),
            int((out["location"] == "ONSHORE").sum()), "1")
        add(pg, "map legend", "4 offshore (text)", "outside-view sites with location OFFSHORE", "count",
            one('COUNTROWS(FILTER(dim_site, NOT (dim_site[lon] >= 4.2 && dim_site[lon] <= 8.7 && dim_site[lat] '
                '>= 3.35 && dim_site[lat] <= 6.8) && dim_site[location] = "OFFSHORE"))', ""),
            int((out["location"] == "OFFSHORE").sum()), "4")
        st = top(f25, "state", 6)
        dax_st = {r["state"]: num(r["v"]) for r in table(
            'EVALUATE CALCULATETABLE(TOPN(6, ADDCOLUMNS(VALUES(dim_state[state]), "v", '
            '[Flare Volume Selected Year (bcm)]), [v], DESC), dim_year[year] = 2025)')}
        add(pg, "Top 6 states", "same 6 states (set)", "TOPN 6 dim_state by Flare Volume Selected Year", "text",
            ",".join(sorted(dax_st)), ",".join(sorted(st.index)))
        for s_, v in st.items():
            add(pg, "Top 6 states", f"label {s_}", "Flare Volume Selected Year (bcm)", "bcm", dax_st.get(s_), v,
                f"{v:.2f}")
        for yr in (2021, 2025):
            add(pg, "Active flare sites chart", f"label {yr}", "Active Sites Label Points", "count",
                one("[Active Sites Label Points]", f"dim_year[year] = {yr}"), active_by_year[yr],
                str(active_by_year[yr]))
        # ---------- Sites ----------
        pg = "Sites"
        add(pg, "page subtitle", "all 476 recorded flare sites (text)", "COUNTROWS(dim_site)", "count",
            one("COUNTROWS(dim_site)", ""), len(site), "476")
        t = table('EVALUATE CALCULATETABLE(ADDCOLUMNS(VALUES(dim_site[site_id]), "ay", CALCULATE(MAX(dim_site[active_years])),'
                  ' "rv", CALCULATE(MAX(dim_site[recent_volume_bcm])), "sy", [Flare Volume Selected Year (bcm)], '
                  '"pp", CALCULATE(SELECTEDVALUE(dim_site[persistent]))), dim_year[year] = 2025)')
        d = pd.DataFrame(t).set_index("site_id")
        ref = site.set_index("site_id")
        sy = f25.set_index("site_id")["bcm"]
        add(pg, "All sites table", "rows", "dim_site", "count", len(d), len(ref), "476 rows")
        for col, py, kind in [("ay", ref["active_years"], "count"), ("rv", ref["recent_volume_bcm"], "bcm"),
                              ("sy", sy, "bcm")]:
            dd = d[col].map(num).reindex(py.index)
            bad = int(((dd - py).abs() > TOL[kind]).sum() + dd.isna().sum())
            add(pg, "All sites table", f"column {col} ({ {'ay': 'Active years', 'rv': 'Recent bcm', 'sy': 'Selected-year bcm'}[col]}): rows not matching",
                {"ay": "dim_site[active_years]", "rv": "dim_site[recent_volume_bcm]",
                 "sy": "Flare Volume Selected Year (bcm)"}[col], "count", bad, 0, "476 rows")
        pers = d["pp"].astype(str).str.lower().eq("true").reindex(ref.index)
        add(pg, "All sites table", "column Persistent: rows not matching", "dim_site[persistent]", "count",
            int((pers != ref["persistent"].astype(bool)).sum()), 0, "476 rows")
        p10 = site[site.persistent].sort_values(["recent_volume_bcm", "site_id"], ascending=[False, True]).head(10)
        dt = table('EVALUATE CALCULATETABLE(TOPN(10, ADDCOLUMNS(VALUES(dim_site[site_id]), "v", '
                   '[Recent Volume (bcm)]), [v], DESC), dim_site[persistent] = TRUE())')
        dtv = {r["site_id"]: num(r["v"]) for r in dt}
        add(pg, "Top 10 persistent by recent volume", "same 10 sites (set)", "TOPN 10 by Recent Volume (bcm)",
            "text", ",".join(sorted(dtv)), ",".join(sorted(p10.site_id)))
        for _, r in p10.iterrows():
            add(pg, "Top 10 persistent by recent volume", r.site_id, "Recent Volume (bcm)", "bcm",
                dtv.get(r.site_id), r.recent_volume_bcm, f"{r.recent_volume_bcm:.2f}")
        # ---------- Operators ----------
        pg = "Operators"
        named = f25[f25.operator_clean != "Unattributed"].groupby("operator_clean")["bcm"].sum()
        t10 = named.sort_values(ascending=False).head(10).sum() / nat[2025]
        add(pg, "card Top 10 operators' share", "83.3%", "Top 10 Operators Share", "share",
            one("[Top 10 Operators Share]"), t10, f"{t10:.1%}")
        un = f25.loc[f25.operator_clean == "Unattributed", "bcm"].sum()
        add(pg, "card Unattributed volume", "0.05 bcm", "Unattributed Volume (bcm)", "bcm",
            one("[Unattributed Volume (bcm)]"), un, f"{un:.2f}")
        add(pg, "Unattributed bar", "label", "Flare Volume Selected Year (bcm), Unattributed", "bcm",
            one("[Flare Volume Selected Year (bcm)]", Y25 + ', dim_operator[is_unattributed] = TRUE()'), un,
            f"{un:.2f}")
        t12 = named.sort_values(ascending=False).head(12)
        dop = {r["operator_clean"]: num(r["v"]) for r in table(
            'EVALUATE CALCULATETABLE(TOPN(12, ADDCOLUMNS(VALUES(dim_operator[operator_clean]), "v", '
            '[Flare Volume Selected Year (bcm)]), [v], DESC), dim_year[year] = 2025, '
            'dim_operator[is_unattributed] = FALSE())')}
        add(pg, "Top 12 operators", "same 12 operators (set)", "TOPN 12", "text", ",".join(sorted(dop)),
            ",".join(sorted(t12.index)))
        for o, v in t12.items():
            add(pg, "Top 12 operators", f"label {o}", "Flare Volume Selected Year (bcm)", "bcm", dop.get(o), v,
                f"{v:.2f}")
        tf = top(f25, "field", 10)
        dfl = {r["field"]: num(r["v"]) for r in table(
            'EVALUATE CALCULATETABLE(TOPN(10, ADDCOLUMNS(VALUES(dim_site[field]), "v", '
            '[Flare Volume Selected Year (bcm)]), [v], DESC), dim_year[year] = 2025)')}
        add(pg, "Top 10 fields", "same 10 fields (set)", "TOPN 10", "text", ",".join(sorted(dfl)),
            ",".join(sorted(tf.index)))
        for fl, v in tf.items():
            add(pg, "Top 10 fields", f"label {fl}", "Flare Volume Selected Year (bcm)", "bcm", dfl.get(fl), v,
                f"{v:.2f}")
        t5 = f[f.operator_clean != "Unattributed"].groupby("operator_clean")["bcm"].sum().sort_values(
            ascending=False).head(5)
        d5 = [r["operator_clean"] for r in table(
            'EVALUATE TOPN(5, CALCULATETABLE(ADDCOLUMNS(VALUES(dim_operator[operator_clean]), "v", '
            '[Flare Volume (bcm)]), dim_operator[is_unattributed] = FALSE(), dim_year[is_actual] = TRUE()), [v], DESC)')]
        add(pg, "Top 5 operators trend", "legend: same 5 operators (set)", "TOPN 5 by Flare Volume 2012-2025", "text",
            ",".join(sorted(d5)), ",".join(sorted(t5.index)))
        # ---------- Cost ----------
        pg = "Cost"
        add(pg, "card Implied emissions", "17.0 Mt CO2e", "CO2e Selected Year (Mt)", "mt",
            one("[CO2e Selected Year (Mt)]"), nat[2025] * prm.loc["co2e_mt_per_bcm", "value"], "17.0")
        for m, p_, shown in [("Gas Value Low (USD)", "price_low_usd_per_mmbtu", "$506M"),
                             ("Gas Value Central (USD)", "price_central_usd_per_mmbtu", "$837M"),
                             ("Gas Value High (USD)", "price_high_usd_per_mmbtu", "$3,186M")]:
            add(pg, "card Gross value", m, m, "usd", one(f"[{m}]"), mmbtu25 * prm.loc[p_, "value"], shown)
        for m, p_, shown in [("Implied Flare Fee Low (USD)", "flare_fee_low_usd_per_mscf", "$117M"),
                             ("Implied Flare Fee High (USD)", "flare_fee_high_usd_per_mscf", "$466M")]:
            add(pg, "card Implied flare fee", m, m, "usd", one(f"[{m}]"), mscf25 * prm.loc[p_, "value"], shown)
        add(pg, "card Implied flare fee", "$0.50/Mscf (text)", "param flare_fee_low_usd_per_mscf", "param",
            0.50, prm.loc["flare_fee_low_usd_per_mscf", "value"], "$0.50")
        add(pg, "card Implied flare fee", "$2.00/Mscf (text)", "param flare_fee_high_usd_per_mscf", "param",
            2.00, prm.loc["flare_fee_high_usd_per_mscf", "value"], "$2.00")
        pa = {r["parameter"]: num(r["value"]) for r in table("EVALUATE param_assumptions")}
        for k, v in prm["value"].items():
            add(pg, "Assumptions table", k, "param_assumptions[value]", "param", pa.get(k), v, None)
        # ---------- People ----------
        pg = "People"
        for i, (grp, km) in enumerate([("active_2025", 2), ("active_2025", 5), ("persistent", 2), ("persistent", 5)]):
            add(pg, f"card {i + 1}", f"{grp} {km} km", f"Residents within {km} km (group {grp})", "pop",
                one(f"[Residents within {km} km]", f'population_groups[group] = "{grp}"'), g[(grp, "All", km)],
                f"{g[(grp, 'All', km)]:,.0f}")
        ps = groups[(groups.group == "persistent") & (groups.buffer_km == 5) & (groups.state != "All")]
        dps = {r["state"]: num(r["v"]) for r in table(
            'EVALUATE ADDCOLUMNS(VALUES(dim_state[state]), "v", [Residents within 5 km of persistent sites])')}
        for _, r in ps.iterrows():
            add(pg, "Residents by state (persistent, 5 km)", f"label {r.state}",
                "Residents within 5 km of persistent sites", "pop", dps.get(r.state), r.pop_union,
                f"{r.pop_union:,.0f}")
        p10 = site[site.persistent].sort_values(["pop_5km", "site_id"], ascending=[False, True]).head(10)
        dt = {r["site_id"]: num(r["v"]) for r in table(
            'EVALUATE CALCULATETABLE(TOPN(10, ADDCOLUMNS(VALUES(dim_site[site_id]), "v", '
            '[Residents within 5 km (per site)]), [v], DESC), dim_site[persistent] = TRUE())')}
        add(pg, "Top 10 persistent by residents", "same 10 sites (set)", "TOPN 10", "text", ",".join(sorted(dt)),
            ",".join(sorted(p10.site_id)))
        for _, r in p10.iterrows():
            add(pg, "Top 10 persistent by residents", r.site_id, "Residents within 5 km (per site)", "pop",
                dt.get(r.site_id), r.pop_5km, f"{r.pop_5km:,.0f}")
        # ---------- Methods ----------
        pg = "Methods"
        for yr in range(2021, 2026):
            fy = f"dim_year[year] = {yr}"
            off = year.loc[yr, "official_bcm"]
            add(pg, "Satellite vs official table", f"{yr} satellite", "Flare Volume (bcm)", "bcm",
                one("[Flare Volume (bcm)]", fy), nat[yr], f"{nat[yr]:.2f}")
            add(pg, "Satellite vs official table", f"{yr} official", "Official Volume (bcm)", "bcm",
                one("[Official Volume (bcm)]", fy), off, f"{off:.2f}")
            add(pg, "Satellite vs official table", f"{yr} difference", "Satellite \u2212 Official (bcm)", "bcm",
                one("[Satellite \u2212 Official (bcm)]", fy), nat[yr] - off, f"{nat[yr] - off:+.2f}")
            add(pg, "Satellite vs official table", f"{yr} ratio", "Satellite \u00f7 Official", "ratio",
                one("[Satellite \u00f7 Official]", fy), nat[yr] / off, f"{nat[yr] / off:.3f}")
        rec = pd.read_csv(I / "phase2b_recompute_comparison.csv", keep_default_na=False)
        val = pd.read_csv(I / "phase3_validation.csv")
        text_all = " ".join(json.dumps(json.load(open(p_, encoding="utf-8")), ensure_ascii=False)
                            for p_ in (REPORT / "a1f0c2d3e4b5a6978805" / "visuals").rglob("visual.json"))
        m1 = re.search(r"recompute \(DuckDB, shapely\): (\d+) / (\d+)", text_all)
        m2 = re.search(r"Python: (\d+) / (\d+) pass", text_all)
        add(pg, "Validation results", "recompute n pass (text)", "phase2b_recompute_comparison.csv", "count",
            int(m1.group(1)), int(rec["pass"].astype(str).eq("True").sum()), m1.group(0))
        add(pg, "Validation results", "model checks n pass (text)", "phase3_validation.csv (built from)", "count",
            int(m2.group(1)), int(val["pass"].sum()), m2.group(0))
        add(pg, "Amendments", "A1: 203.9 billion scf (text)", "official_volumes.csv 2025 value", "param",
            203.9, float(pd.read_csv(I / "official_volumes.csv").query("year == 2025 and used")["value"].iloc[0]),
            "203.9")
        k1 = json.load(open(I / "phase2b_flag_kaduna.json", encoding="utf-8"))
        add(pg, "Known data issues", "K1: 467 km (text)", "phase2b_flag_kaduna.json", "count", 467,
            int(re.search(r"(\d+) km", k1["other_sites_with_same_field"]).group(1)), "467 km")
        add(pg, "Known data issues", "K2: 33 sites (text)", "phase2b_flag_offshore_in_polygon.csv rows", "count", 33,
            len(pd.read_csv(I / "phase2b_flag_offshore_in_polygon.csv")), "33")
    finally:
        pbi.close()

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False, encoding="utf-8")
    hits = wording_audit()
    write_doc(df, hits)
    print(f"numbers: {int(df['pass'].sum())}/{len(df)} pass; wording hits needing a fix: "
          f"{sum(1 for h in hits if h['verdict'] == 'FIX')}")


# ---------------- C. wording audit ----------------
FORBIDDEN = {
    "owed": r"\bowed\b", "unpaid": r"\bunpaid\b", "due": r"\bdue\b", "evaded": r"\bevad\w*", "liable": r"\bliab\w*",
    "penalty": r"\bpenalt\w*", "health": r"\bhealth\b", "exposure": r"\bexposure\b", "on track": r"\bon track\b",
    "off track": r"\boff track\b", "forecast": r"\bforecast\w*", "risk": r"\brisks?\b", "dose": r"\bdose\b",
    "compliance": r"\bcomplian\w*", "violation": r"\bviolat\w*", "illegal": r"\billegal\w*",
}
NEGATION = re.compile(r"\b(not|no|never|nor)\b[^.;]*$", re.I)


def strings():
    out = []
    for pdir in REPORT.iterdir():
        if not pdir.is_dir():
            continue
        page = PAGE.get(pdir.name, pdir.name)
        for vf in (pdir / "visuals").rglob("visual.json"):
            v = json.load(open(vf, encoding="utf-8"))
            name = v["name"]
            vis = v.get("visual", {})
            for para in vis.get("objects", {}).get("general", [{}])[0].get("properties", {}).get("paragraphs", []):
                txt = "".join(r["value"] for r in para.get("textRuns", []))
                if txt.strip():
                    out.append((page, name, "text", txt))
            for k in ("title", "subTitle"):
                for o in vis.get("visualContainerObjects", {}).get(k, []):
                    t = o.get("properties", {}).get("text", {}).get("expr", {}).get("Literal", {}).get("Value")
                    if t:
                        out.append((page, name, k, t.strip("'").replace("''", "'")))
            for o in vis.get("objects", {}).get("text", []):
                t = o.get("properties", {}).get("text", {}).get("expr", {}).get("Literal", {}).get("Value")
                if t:
                    out.append((page, name, "button", t.strip("'")))
            for role in vis.get("query", {}).get("queryState", {}).values():
                for pj in role.get("projections", []):
                    if pj.get("displayName"):
                        out.append((page, name, "label/tooltip", pj["displayName"]))
    txt = TMDL.read_text(encoding="utf-8")
    for m in re.finditer(r"^\t/// (.*)\r?\n\tmeasure ('(?:[^']|'')+'|\S+)", txt, re.M):
        out.append(("model", m.group(2).strip("'"), "measure description", m.group(1)))
    return out


def wording_audit():
    hits = []
    for page, vis, kind, s in strings():
        for word, pat in FORBIDDEN.items():
            for m in re.finditer(pat, s, re.I):
                before = s[:m.start()]
                clause = re.split(r"[.;:\u00b7]", before)[-1]
                if word == "penalty" and re.search(r"formerly", s[max(0, m.start() - 30):m.start()], re.I):
                    verdict = "allowed (formerly-penalty note)"
                elif NEGATION.search(clause):
                    verdict = "allowed (negated disclaimer)"
                elif word == "due" and re.search(r"\bdue to\b", s[m.start():m.start() + 7], re.I):
                    verdict = "FIX"
                else:
                    verdict = "FIX"
                hits.append({"page": page, "visual": vis, "kind": kind, "word": word, "text": s, "verdict": verdict})
    # positive rules
    all_s = strings()
    for page, vis, kind, s in all_s:
        low = s.lower()
        if page != "model" and "operator" in low and "as recorded" not in low and kind in ("title", "subTitle"):
            page_has = any(p == page and "as recorded" in t.lower() for p, _, _, t in all_s)
            hits.append({"page": page, "visual": vis, "kind": kind, "word": "operator without 'as recorded'",
                         "text": s, "verdict": "allowed (page states 'as recorded')" if page_has else "FIX"})
        if "2030" in low and "path" in low and "illustrative" not in low:
            hits.append({"page": page, "visual": vis, "kind": kind, "word": "2030 path not 'illustrative'",
                         "text": s, "verdict": "FIX"})
    for page in set(PAGE.values()):
        if not any(p == page and "estimate" in t.lower() for p, _, _, t in all_s):
            hits.append({"page": page, "visual": "-", "kind": "page", "word": "no 'estimate' wording on page",
                         "text": "", "verdict": "FIX"})
    return hits


def fmt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "BLANK"
    if isinstance(v, str):
        return v if len(v) < 60 else v[:57] + "..."
    v = float(v)
    return f"{v:,.0f}" if v.is_integer() else (f"{v:,.4f}" if abs(v) < 1000 else f"{v:,.2f}")


def write_doc(df, hits):
    L = ["# Phase 4 audit: numbers and wording", "",
         "Date: 2026-11-20. Run by [powerbi/phase4_audit.py](../powerbi/phase4_audit.py) against the open "
         "FlareWatch model (DAX, Year = 2025, the slicer default) and the report files. Python values are computed "
         "independently in pandas from `data/processed/` and `data/interim/`. Machine-readable: "
         "`data/interim/phase4_audit.csv`.", "",
         "Tolerances: 0.001 bcm (and Mt CO2e); exact for counts; 1 person; 1 USD; 1e-6 for shares and ratios; "
         "exact text for sets of names (top-N membership).", "",
         f"## B. Numbers shown on the report: **{int(df['pass'].sum())} of {len(df)} pass**", ""]
    for page in ["National", "Sites", "Operators", "Cost", "People", "Methods"]:
        d = df[df.page == page]
        L += [f"### {page} ({int(d['pass'].sum())} of {len(d)} pass)", "",
              "| Visual | Item | Measure / column | Shown | DAX | Python | Pass |", "|---|---|---|---|---:|---:|---|"]
        for _, r in d.iterrows():
            L.append(f"| {r.visual} | {r['item']} | {r.source} | {r.shown if isinstance(r.shown, str) else ''} | "
                     f"{fmt(r.dax)} | {fmt(r.python)} | {'yes' if r['pass'] else 'NO'} |")
        L.append("")
    L += ["Notes:", "",
          "- Chart values that are drawn but not labelled (bars and lines without data labels, axis ticks) are "
          "not listed; the measures behind them are checked year by year in docs/phase3_model.md.",
          "- The All sites table (476 rows) is checked column by column; the table shows the number of rows that "
          "do not match (expected 0).",
          "- Card values are shown rounded (e.g. 6.60, $506M); the audit compares the unrounded value.", "",
          "## C. Wording audit (safe-claim rules, plan s7, A2, A3)", "",
          f"Strings checked: {len(strings())} (report text boxes, titles, subtitles, buttons, field labels and "
          "tooltip names on all 6 pages, plus every measure description). Words searched: "
          + ", ".join(FORBIDDEN) + ". Also checked: operator titles carry \"as recorded\" (or the page does), any "
          "2030 path is called illustrative, every page calls the figures estimates.", ""]
    fix = [h for h in hits if h["verdict"] == "FIX"]
    L += [f"Hits needing a fix: **{len(fix)}**. Allowed occurrences (disclaimers in the negative, or the "
          f"'formerly penalty' note): {len(hits) - len(fix)}.", "",
          "| Page | Visual | Kind | Rule | Text | Verdict |", "|---|---|---|---|---|---|"]
    for h in hits:
        t = h["text"].replace("|", "/")
        L.append(f"| {h['page']} | {h['visual']} | {h['kind']} | {h['word']} | {t[:110]}{'...' if len(t) > 110 else ''}"
                 f" | {h['verdict']} |")
    DOC.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
