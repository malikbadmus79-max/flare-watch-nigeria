"""Phase 3 report, page 1 ("National") + empty navigation pages, written as PBIR JSON.

Writes a complete `definition/pages` tree into powerbi/pbir_staging/ (validated by
pbir_validate.py), which is then copied into FlareWatch.Report/definition/.
Design: powerbi/design/page1_mockup.png (2560x1440 -> 1280x720, coordinates halved).
Uses existing _Measures only; the semantic model is not changed.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGING = HERE / "pbir_staging" / "definition"
PAGES_DIR = STAGING / "pages"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
PAGE_SCHEMA = f"{SCHEMA}/page/2.1.0/schema.json"
PAGES_SCHEMA = f"{SCHEMA}/pagesMetadata/1.0.0/schema.json"
VC_SCHEMA = f"{SCHEMA}/visualContainer/2.8.0/schema.json"

ORANGE, BLUE, GREY = "#D9531E", "#2F5E8C", "#3D4148"
ORANGE_LIGHT = "#EBA383"
INK, MUTED, CREAM, WHITE, LINE = "#1B1D22", "#5C5F66", "#F5F2EC", "#FFFFFF", "#E6E0D3"
FONT, FONT_BOLD = "Segoe UI", "Segoe UI Semibold"

NATIONAL = "d29ca64d357c262b6b10"  # existing page, renamed
PAGES = [  # (name, displayName)
    (NATIONAL, "National"),
    ("a1f0c2d3e4b5a6978801", "Sites"),
    ("a1f0c2d3e4b5a6978802", "Operators"),
    ("a1f0c2d3e4b5a6978803", "Cost"),
    ("a1f0c2d3e4b5a6978804", "People"),
    ("a1f0c2d3e4b5a6978805", "Methods"),
]
SOURCE_LINE = ("Source: NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR, 2026 release. "
               "Official: NUPRC via BudgIT (2021–24); NUPRC as reported in the press (2025). "
               "All figures are estimates.")


# ---------- expression helpers ----------
def lit(v):
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, int):
        s = f"{v}L"
    elif isinstance(v, float):
        s = f"{v}D"
    else:
        s = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": s}}}


def color(hex_):
    return {"solid": {"color": lit(hex_)}}


def props(**kw):
    out = {}
    for k, v in kw.items():
        out[k] = color(v[1:]) if isinstance(v, str) and v.startswith("@#") else (v if isinstance(v, dict) else lit(v))
    return out


def C(h):  # mark a colour value
    return "@" + h


def measure(name):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}}


def column(table, col):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}}


def proj(field, query_ref, display=None):
    p = {"field": field, "queryRef": query_ref, "nativeQueryRef": query_ref.split(".", 1)[1]}
    if display:
        p["displayName"] = display
    return p


def m_proj(name, display=None):
    return proj(measure(name), f"_Measures.{name}", display)


def year_proj():
    return proj(column("dim_year", "year"), "dim_year.year", "Year")


def is_actual_filter(name):
    return {"filters": [{
        "name": name,
        "field": column("dim_year", "is_actual"),
        "type": "Categorical",
        "filter": {"Version": 2, "From": [{"Name": "d", "Entity": "dim_year", "Type": 0}],
                   "Where": [{"Condition": {"In": {
                       "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}},
                                                   "Property": "is_actual"}}],
                       "Values": [[{"Literal": {"Value": "true"}}]]}}}]},
        "howCreated": "User",
    }]}


# ---------- container formatting ----------
def chrome(title=None, subtitle=None, bg=WHITE, border=True, pad=None, title_size=12):
    o = {
        "background": [{"properties": props(show=bg is not None, color=C(bg or WHITE), transparency=0.0)}],
        "border": [{"properties": props(show=border, color=C(LINE), radius=8.0, width=1.0)}],
        "dropShadow": [{"properties": props(show=False)}],
        "visualHeader": [{"properties": props(show=False)}],
    }
    if pad is not None:
        o["padding"] = [{"properties": props(top=float(pad[0]), bottom=float(pad[1]),
                                             left=float(pad[2]), right=float(pad[3]))}]
    if title:
        o["title"] = [{"properties": props(show=True, text=title, fontColor=C(INK), fontSize=float(title_size),
                                           fontFamily=FONT_BOLD, bold=False, titleWrap=True)}]
    else:
        o["title"] = [{"properties": props(show=False)}]
    if subtitle:
        o["subTitle"] = [{"properties": props(show=True, text=subtitle, fontColor=C(MUTED), fontSize=9.0,
                                              fontFamily=FONT, titleWrap=True)}]
    else:
        o["subTitle"] = [{"properties": props(show=False)}]
    return o


def container(name, x, y, w, h, z, visual, filter_config=None):
    vc = {"$schema": VC_SCHEMA, "name": name,
          "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
          "visual": visual}
    if filter_config:
        vc["filterConfig"] = filter_config
    return vc


# ---------- text boxes ----------
def run(text, size=10, color_=INK, font=FONT, bold=False, italic=False):
    style = {"fontFamily": font, "fontSize": f"{size}pt", "color": color_}
    if bold:
        style["fontWeight"] = "bold"
    if italic:
        style["fontStyle"] = "italic"
    return {"value": text, "textStyle": style}


def para(*runs, align="left"):
    return {"textRuns": list(runs), "horizontalTextAlignment": align}


def textbox(name, x, y, w, h, z, paragraphs, bg=None, border=False, pad=(0, 0, 0, 0)):
    visual = {"visualType": "textbox",
              "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
              "visualContainerObjects": chrome(bg=bg, border=border, pad=pad),
              "drillFilterOtherVisuals": True}
    return container(name, x, y, w, h, z, visual)


# ---------- page 1 visuals ----------
def card(name, x, z, m, title, label, value_color=INK):
    visual = {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [m_proj(m, label)]}}},
        "objects": {
            "labels": [{"properties": props(color=C(value_color), fontSize=26.0, fontFamily=FONT_BOLD,
                                            labelDisplayUnits=1.0)}],
            "categoryLabels": [{"properties": props(show=True, color=C(MUTED), fontSize=9.0, fontFamily=FONT)}],
        },
        "visualContainerObjects": chrome(title=title, pad=(8, 8, 14, 14), title_size=10),
        "drillFilterOtherVisuals": True,
    }
    return container(name, x, 92, 236, 84, z, visual)


def main_chart():
    name = "nationalCombo"
    y2025 = {"data": [{"scopeId": {"Comparison": {
        "ComparisonKind": 0, "Left": column("dim_year", "year"), "Right": {"Literal": {"Value": "2025L"}}}}}]}
    visual = {
        "visualType": "lineClusteredColumnComboChart",
        "query": {"queryState": {
            "Category": {"projections": [year_proj()]},
            "Y": {"projections": [m_proj("Flare Volume (bcm)", "Satellite estimate")]},
            "Y2": {"projections": [m_proj("Official Volume (bcm)", "Official (NUPRC)"),
                                   m_proj("Illustrative Path 2030 (bcm)", "Illustrative path")]},
        },
            "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": props(axisType="Categorical", show=True, showAxisTitle=False,
                                                  labelColor=C(MUTED), fontSize=9.0, concatenateLabels=False)}],
            "valueAxis": [{"properties": props(show=True, showAxisTitle=True, titleText="bcm", start=0.0,
                                               secShow=False, labelColor=C(MUTED), fontSize=9.0,
                                               gridlineShow=True)}],
            "legend": [{"properties": props(show=True, position="TopLeft", showTitle=False, labelColor=C(INK),
                                            fontSize=9.0)}],
            "dataPoint": [
                {"properties": {"fill": color(ORANGE_LIGHT)}, "selector": {"metadata": "_Measures.Flare Volume (bcm)"}},
                {"properties": {"fill": color(ORANGE)}, "selector": y2025},
                {"properties": {"fill": color(BLUE)}, "selector": {"metadata": "_Measures.Official Volume (bcm)"}},
                {"properties": {"fill": color(GREY)},
                 "selector": {"metadata": "_Measures.Illustrative Path 2030 (bcm)"}},
            ],
            "lineStyles": [
                {"properties": props(strokeWidth=2.0, showMarker=True, markerSize=4.0, lineStyle="solid"),
                 "selector": {"metadata": "_Measures.Official Volume (bcm)"}},
                {"properties": props(strokeWidth=2.0, showMarker=True, markerSize=4.0, lineStyle="dashed"),
                 "selector": {"metadata": "_Measures.Illustrative Path 2030 (bcm)"}},
            ],
            "labels": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": chrome(
            title="Estimated flaring by year, with official figures and an illustrative path to 2030",
            subtitle="Billion cubic metres (bcm). Satellite estimates for all upstream flaring; NUPRC official "
                     "figures from 2021.",
            pad=(10, 10, 14, 14)),
        "drillFilterOtherVisuals": True,
    }
    return container(name, 24, 190, 799, 482, 2000, visual)


def sites_chart():
    visual = {
        "visualType": "lineChart",
        "query": {"queryState": {
            "Category": {"projections": [year_proj()]},
            "Y": {"projections": [m_proj("Active Sites", "Active flare sites")]},
        },
            "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": props(axisType="Categorical", show=True, showAxisTitle=False,
                                                  labelColor=C(MUTED), fontSize=9.0)}],
            "valueAxis": [{"properties": props(show=True, showAxisTitle=False, labelColor=C(MUTED), fontSize=9.0,
                                               gridlineShow=True)}],
            "legend": [{"properties": props(show=False)}],
            "dataPoint": [{"properties": {"fill": color(ORANGE)}, "selector": {"metadata": "_Measures.Active Sites"}}],
            "lineStyles": [{"properties": props(strokeWidth=2.0, showMarker=False)}],
            "labels": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": chrome(title="Active flare sites by year", subtitle="Sites with any flaring detected",
                                         pad=(10, 10, 14, 14)),
        "drillFilterOtherVisuals": True,
    }
    return container("activeSitesLine", 836, 190, 420, 226, 3000, visual,
                     filter_config=is_actual_filter("fActualSitesLine"))


def year_slicer():
    default = {"filter": {"Version": 2, "From": [{"Name": "d", "Entity": "dim_year", "Type": 0}],
                          "Where": [{"Condition": {"In": {
                              "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}},
                                                          "Property": "year"}}],
                              "Values": [[{"Literal": {"Value": "2025L"}}]]}}}]}}
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [year_proj()]}},
                  "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Descending"}],
                                     "isDefaultSort": False}},
        "objects": {
            "data": [{"properties": props(mode="Dropdown")}],
            "selection": [{"properties": props(singleSelect=True, strictSingleSelect=True, selectAllCheckboxEnabled=False)}],
            "general": [{"properties": {"filter": default}}],
            "header": [{"properties": props(show=True, text="Year", fontColor=C(MUTED), textSize=9.0,
                                            fontFamily=FONT, outline="None")}],
            "items": [{"properties": props(fontColor=C(INK), textSize=10.0, fontFamily=FONT_BOLD)}],
        },
        "visualContainerObjects": chrome(pad=(2, 2, 8, 8)),
        "drillFilterOtherVisuals": True,
    }
    return container("yearSlicer", 1164, 18, 92, 50, 1000, visual,
                     filter_config=is_actual_filter("fActualSlicer"))


def navigator():
    visual = {
        "visualType": "pageNavigator",
        "objects": {
            "shape": [{"properties": props(tileShape="pill")}],
            "fill": [
                {"properties": props(show=True, fillColor=C(WHITE), transparency=0.0), "selector": {"id": "default"}},
                {"properties": props(show=True, fillColor=C(INK), transparency=0.0), "selector": {"id": "selected"}},
                {"properties": props(show=True, fillColor=C(CREAM), transparency=0.0), "selector": {"id": "hover"}},
            ],
            "text": [
                {"properties": props(show=True, fontColor=C(INK), fontSize=10.0, fontFamily=FONT),
                 "selector": {"id": "default"}},
                {"properties": props(show=True, fontColor=C(WHITE), fontSize=10.0, fontFamily=FONT_BOLD),
                 "selector": {"id": "selected"}},
            ],
            "outline": [{"properties": props(show=True, lineColor=C(LINE), weight=1.0),
                         "selector": {"id": "default"}}],
            "layout": [{"properties": props(cellPadding=6.0)}],
        },
        "visualContainerObjects": chrome(bg=None, border=False, pad=(0, 0, 0, 0)),
    }
    return container("pageNav", 760, 33, 395, 30, 1100, visual)


def national_visuals():
    v = []
    # top colour strip (orange 60%, blue 40%)
    v.append(textbox("stripOrange", 0, 0, 768, 5, 0, [para(run(" ", 1))], bg=ORANGE))
    v.append(textbox("stripBlue", 768, 0, 512, 5, 1, [para(run(" ", 1))], bg=BLUE))
    # header
    v.append(textbox("eyebrow", 20, 14, 520, 22, 10, [para(
        run("●  ", 8, ORANGE), run("FLARE WATCH NIGERIA · PAGE 1 OF 6", 9, MUTED, FONT_BOLD))]))
    v.append(textbox("pageTitle", 20, 30, 720, 38, 11, [para(
        run("National flaring, 2012–2025", 22, INK, FONT_BOLD))]))
    v.append(textbox("pageSubtitle", 20, 62, 720, 22, 12, [para(
        run("Estimated gas flared at upstream oil and gas sites, from World Bank satellite data", 11, MUTED))]))
    v.append(navigator())
    v.append(year_slicer())
    # cards
    xs = [24, 274, 523, 771, 1020]
    v.append(card("cardVolume", xs[0], 100, "Flare Volume Selected Year (bcm)", "Estimated flaring, selected year",
                  "bcm · satellite estimate", ORANGE))
    v.append(card("cardChange2012", xs[1], 101, "Change since 2012 (%)", "Change since 2012",
                  "estimated bcm, selected year vs 2012"))
    v.append(card("cardChange2023", xs[2], 102, "Change since 2023 (%)", "Change since 2023 low",
                  "estimated bcm, selected year vs 2023"))
    v.append(card("cardActive", xs[3], 103, "Active Sites Selected Year", "Active flare sites, selected year",
                  "of 476 recorded sites"))
    v.append(card("cardPersistent", xs[4], 104, "Persistent Sites (12 of 14)", "Persistent sites",
                  "flaring ≥12 of 14 years"))
    # charts
    v.append(main_chart())
    v.append(textbox("pathNote", 690, 456, 120, 36, 2100, [para(
        run("Illustrative straight line to zero by 2030", 9, MUTED, italic=True))]))
    v.append(sites_chart())
    # explainer
    bullets = [
        "Estimated flaring fell from 9.28 bcm in 2012 to 5.10 bcm in 2023, then rose in 2024 and 2025.",
        "Satellite estimates were below official figures in 2021–2023 and above them in 2024–2025.",
        "The 2030 line is illustrative: satellites measure all flaring, not only routine flaring.",
    ]
    paras = [para(run("What this page shows", 12, INK, FONT_BOLD))] + [
        para(run("•  " + b, 10, INK)) for b in bullets]
    v.append(textbox("whatThisShows", 836, 430, 420, 242, 4000, paras, bg=WHITE, border=True, pad=(12, 12, 14, 14)))
    # footer
    v.append(textbox("footerSource", 20, 696, 960, 18, 5000, [para(run(SOURCE_LINE, 8, MUTED))]))
    v.append(textbox("footerAuthor", 1056, 696, 200, 18, 5001, [para(run("Malik Kolawole Badmus · v1.0", 8, MUTED),
                                                                     align="right")]))
    return v


def page_json(name, display, interactions=None):
    p = {"$schema": PAGE_SCHEMA, "name": name, "displayName": display, "displayOption": "FitToPage",
         "height": 720, "width": 1280,
         "objects": {
             "background": [{"properties": {"color": color(CREAM), "transparency": lit(0.0)}}],
             "outspace": [{"properties": {"color": color(CREAM), "transparency": lit(0.0)}}],
         }}
    if interactions:
        p["visualInteractions"] = interactions
    return p


def placeholder_visuals(display, index):
    return [
        textbox("stripOrange", 0, 0, 768, 5, 0, [para(run(" ", 1))], bg=ORANGE),
        textbox("stripBlue", 768, 0, 512, 5, 1, [para(run(" ", 1))], bg=BLUE),
        textbox("eyebrow", 20, 14, 520, 22, 10, [para(
            run("●  ", 8, ORANGE), run(f"FLARE WATCH NIGERIA · PAGE {index} OF 6", 9, MUTED, FONT_BOLD))]),
        textbox("pageTitle", 20, 30, 720, 38, 11, [para(run(display, 22, INK, FONT_BOLD))]),
        navigator(),
    ]


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    if STAGING.parent.exists():
        shutil.rmtree(STAGING.parent)
    write(PAGES_DIR / "pages.json", {"$schema": PAGES_SCHEMA, "pageOrder": [n for n, _ in PAGES],
                                     "activePageName": NATIONAL})
    no_filter = [{"source": "yearSlicer", "target": t, "type": "NoFilter"}
                 for t in ("nationalCombo", "activeSitesLine")]
    for i, (name, display) in enumerate(PAGES, start=1):
        if name == NATIONAL:
            write(PAGES_DIR / name / "page.json", page_json(name, display, no_filter))
            visuals = national_visuals()
        else:
            write(PAGES_DIR / name / "page.json", page_json(name, display))
            visuals = placeholder_visuals(display, i)
        for vc in visuals:
            write(PAGES_DIR / name / "visuals" / vc["name"] / "visual.json", vc)
    n = sum(1 for _ in STAGING.rglob("*.json"))
    print(f"wrote {n} JSON files to {STAGING.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
