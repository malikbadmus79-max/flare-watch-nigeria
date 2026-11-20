"""Night redesign (polish round 2): left rail on all 6 pages + "National" page per
powerbi/design/page1_v2_night.png.

Writes PBIR JSON to powerbi/pbir_staging/definition/pages (validated by pbir_validate.py),
then copied into FlareWatch.Report/definition/pages. Coordinates are the mockup (2560x1440)
halved. Measures used exist in _Measures. Text boxes are sized from their font size so no
text box needs a scrollbar.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402
sys.path.insert(0, str(HERE))
STAGING = HERE / "pbir_staging" / "definition"
PAGES_DIR = STAGING / "pages"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
PAGE_SCHEMA = f"{SCHEMA}/page/2.1.0/schema.json"
PAGES_SCHEMA = f"{SCHEMA}/pagesMetadata/1.0.0/schema.json"
VC_SCHEMA = f"{SCHEMA}/visualContainer/2.8.0/schema.json"

# night palette (flare_watch_theme_night.json + mockup)
PAGE_BG, RAIL_BG, PANEL, PANEL_LINE = "#0D1117", "#0A0D12", "#151B23", "#232B36"
ORANGE, ORANGE_DARK, ORANGE_SOFT, ORANGE_NAV, ACTIVE_BG = "#FF7A1A", "#9C4519", "#FFB27A", "#FF9A4D", "#1E1410"
BLUE, GREY_PATH, GREY_DOT = "#5AB0F0", "#8B95A3", "#3A4452"
# Power BI ignored scatter transparency, so the look is pre-blended over the panel colour #151B23:
MAP_ORANGE = "#E36F1C"   # #FF7A1A at ~85% opacity
MAP_GLOW = "#3B2A21"     # #FF7A1A at ~17% opacity (soft halo layer drawn underneath)
TEXT, TEXT_2, MUTED, AXIS = "#E8EAED", "#C9CED6", "#8B95A3", "#6B7685"
# font stacks as Power BI Desktop writes them (a bare "Segoe UI Bold" fell back to a serif font)
FONT = "'Segoe UI', wf_segoe-ui_normal, helvetica, arial, sans-serif"
FONT_SEMI = "'Segoe UI Semibold', wf_segoe-ui_semibold, helvetica, arial, sans-serif"
FONT_BOLD = "'Segoe UI Bold', wf_segoe-ui_bold, helvetica, arial, sans-serif"

NATIONAL = "d29ca64d357c262b6b10"
PAGES = [  # name, displayName, rail icon
    (NATIONAL, "National", "◉"),
    ("a1f0c2d3e4b5a6978801", "Sites", "⌖"),
    ("a1f0c2d3e4b5a6978802", "Operators", "▤"),
    ("a1f0c2d3e4b5a6978803", "Cost", "$"),
    ("a1f0c2d3e4b5a6978804", "People", "◍"),
    ("a1f0c2d3e4b5a6978805", "Methods", "ⓘ"),
]
SOURCE_LINE = ("Source: NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR, 2026 release · "
               "Official: NUPRC via BudgIT (2021–24), NUPRC as reported in the press (2025) · "
               "All figures are estimates; 2030 path illustrative.")

# map window (task spec) and plot size chosen so 1 degree lon ~ 1 degree lat on screen
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = 4.2, 8.7, 3.35, 6.8
MAP_W = 487
MAP_H = round(MAP_W * (LAT_MAX - LAT_MIN) / (LON_MAX - LON_MIN))  # 373

# vertical layout (polish round 2: subtitle >= 6px below title; everything shifted to fit)
Y_CARDS, H_CARDS = 102, 104   # cards 102..206
Y_MID = 214                     # combo chart + map panel top
H_COMBO = 254                   # combo 214..468
Y_LOW, H_LOW = 478, 215         # bottom row 478..693


def text_h(pt: float, lines: int = 1) -> int:
    """Height a text box needs for `lines` lines at `pt` points (line height 1.35, 6px slack)."""
    return math.ceil(pt * 4 / 3 * 1.35 * lines) + 6


# ---------- expression helpers ----------
def lit_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}L"
    if isinstance(v, float):
        return f"{v}D"
    return "'" + str(v).replace("'", "''") + "'"


def lit(v):
    return {"expr": {"Literal": {"Value": lit_value(v)}}}


def color(hex_):
    return {"solid": {"color": lit(hex_)}}


def C(h):
    return "@" + h


def props(**kw):
    out = {}
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith("@#"):
            out[k] = color(v[1:])
        elif isinstance(v, dict):
            out[k] = v
        else:
            out[k] = lit(v)
    return out


def measure(name, source=None):
    ref = {"Source": source} if source else {"Entity": "_Measures"}
    return {"Measure": {"Expression": {"SourceRef": ref}, "Property": name}}


def column(table, col):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": col}}


def agg(table, col, fn):
    return {"Aggregation": {"Expression": column(table, col), "Function": fn}}


AGG_NAME = {1: "Average", 3: "Min"}


def proj(field, query_ref, display=None):
    p = {"field": field, "queryRef": query_ref, "nativeQueryRef": query_ref.split(".", 1)[1].rstrip(")")}
    if display:
        p["displayName"] = display
    return p


def m_proj(name, display=None):
    return proj(measure(name), f"_Measures.{name}", display)


def c_proj(table, col, display=None):
    return proj(column(table, col), f"{table}.{col}", display)


def a_proj(table, col, fn, display=None):
    return proj(agg(table, col, fn), f"{AGG_NAME[fn]}({table}.{col})", display)


ALL_POINTS = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}


def categorical_filter(name, table, col, values):
    return {
        "name": name, "field": column(table, col), "type": "Categorical",
        "filter": {"Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                   "Where": [{"Condition": {"In": {
                       "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": col}}],
                       "Values": [[{"Literal": {"Value": lit_value(v)}}] for v in values]}}}]},
        "howCreated": "User"}


def measure_gt_zero_filter(name, m):
    return {
        "name": name, "field": measure(m), "type": "Advanced",
        "filter": {"Version": 2, "From": [{"Name": "m", "Entity": "_Measures", "Type": 0}],
                   "Where": [{"Condition": {"Comparison": {
                       "ComparisonKind": 1, "Left": measure(m, source="m"),
                       "Right": {"Literal": {"Value": "0D"}}}}}]},
        "howCreated": "User"}


def actual_years(name):
    return {"filters": [categorical_filter(name, "dim_year", "is_actual", [True])]}


# ---------- container formatting ----------
def chrome(title=None, subtitle=None, panel=True, pad=(0, 0, 0, 0), bg=PANEL, border=True, border_color=PANEL_LINE,
           radius=12.0):
    return {
        "background": [{"properties": props(show=panel, color=C(bg), transparency=0.0)}],
        "border": [{"properties": props(show=panel and border, color=C(border_color), radius=radius, width=1.0)}],
        "dropShadow": [{"properties": props(show=False)}],
        "visualHeader": [{"properties": props(show=False)}],
        "padding": [{"properties": props(top=float(pad[0]), bottom=float(pad[1]), left=float(pad[2]),
                                         right=float(pad[3]))}],
        "title": [{"properties": props(show=bool(title), **({"text": title, "fontColor": C(TEXT), "fontSize": 12.0,
                                                             "fontFamily": FONT_SEMI} if title else {}))}],
        "subTitle": [{"properties": props(show=bool(subtitle), **({"text": subtitle, "fontColor": C(MUTED),
                                                                   "fontSize": 9.0, "fontFamily": FONT}
                                                                  if subtitle else {}))}],
    }


def container(name, x, y, w, h, z, visual, filter_config=None):
    vc = {"$schema": VC_SCHEMA, "name": name,
          "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
          "visual": visual}
    if filter_config:
        vc["filterConfig"] = filter_config
    return vc


# ---------- text ----------
def run(text, size=10.0, color_=TEXT, font=FONT, italic=False):
    style = {"fontFamily": font, "fontSize": f"{size}pt", "color": color_}
    if italic:
        style["fontStyle"] = "italic"
    return {"value": text, "textStyle": style}


def para(*runs, align="left"):
    return {"textRuns": list(runs), "horizontalTextAlignment": align}


def textbox(name, x, y, w, h, z, paragraphs, panel=False, bg=PANEL, border=True, border_color=PANEL_LINE,
            pad=(0, 0, 0, 0), radius=12.0):
    visual = {"visualType": "textbox",
              "objects": {"general": [{"properties": {"paragraphs": paragraphs}}]},
              "visualContainerObjects": chrome(panel=panel, bg=bg, border=border, border_color=border_color,
                                               pad=pad, radius=radius)}
    return container(name, x, y, w, h, z, visual)


def fill_box(name, x, y, w, h, z, bg, radius=0.0):
    """Solid rectangle (an empty text box with a background)."""
    return textbox(name, x, y, w, h, z, [para(run("", 1.0))], panel=True, bg=bg, border=False, radius=radius)


def label(name, x, y, w, z, text, size, color_=TEXT, font=FONT, align="left", italic=False, lines=1):
    return textbox(name, x, y, w, text_h(size, lines), z, [para(run(text, size, color_, font, italic), align=align)])


def panel(name, x, y, w, h, z, title=None, subtitle=None):
    paras = [para(run(title, 12.0, TEXT, FONT_SEMI))] if title else [para(run(" ", 1.0))]
    if title and subtitle:
        paras.append(para(run(subtitle, 9.0, MUTED)))
    return textbox(name, x, y, w, h, z, paras, panel=True, pad=(12, 12, 14, 14))


# ---------- rail (all pages) ----------
RAIL_Y = [72, 126, 179, 232, 285, 338]
ITEM_H = 48


def rail(current: str):
    v = [fill_box("railBg", 0, 0, 76, 720, 0, RAIL_BG),
         label("railFlame", 8, 6, 60, 1, "●", 28.0, ORANGE, align="center")]
    for i, ((name, display, icon), y) in enumerate(zip(PAGES, RAIL_Y)):
        active = name == current
        col = ORANGE_NAV if active else MUTED
        if active:
            v.append(fill_box("railActive", 6, y, 64, ITEM_H, 2, ACTIVE_BG, radius=6.0))
            v.append(fill_box("railAccent", 6, y + 4, 3, ITEM_H - 8, 3, ORANGE))
        v.append(label(f"railIcon{i}", 6, y + 3, 64, 4 + i, icon, 11.0, col, align="center"))
        v.append(label(f"railLabel{i}", 4, y + 25, 68, 10 + i, display, 7.5, col,
                       FONT_SEMI if active else FONT, align="center"))
        btn = {
            "visualType": "actionButton",
            "objects": {
                "icon": [{"properties": props(show=False)}],
                "text": [{"properties": props(show=False)}],
                "fill": [{"properties": props(show=False), "selector": {"id": s}}
                         for s in ("default", "hover", "press")],
                "outline": [{"properties": props(show=False)}] + [
                    {"properties": props(show=False), "selector": {"id": s}} for s in ("default", "hover", "press")],
            },
            "visualContainerObjects": {
                **chrome(panel=False, pad=(0, 4, 0, 0)),
                "visualLink": [{"properties": props(show=True, type="PageNavigation", navigationSection=name)}],
            },
        }
        v.append(container(f"railNav{i}", 6, y, 64, ITEM_H, 20 + i, btn))
    return v


def header(eyebrow, title, subtitle=None):
    v = [label("eyebrow", 92, 6, 520, 30, eyebrow, 9.0, ORANGE, FONT_BOLD),
         label("pageTitle", 92, 24, 780, 31, title, 20.0, TEXT, FONT_BOLD)]  # 24..66
    if subtitle:
        v.append(label("pageSubtitle", 92, 72, 780, 32, subtitle, 10.5, MUTED))  # >= 6px below title box
    return v


def footer():
    return [label("footerSource", 92, 697, 1004, 5000, SOURCE_LINE, 6.5, AXIS),
            label("footerAuthor", 1096, 697, 160, 5001, "Malik Kolawole Badmus · v1.0", 6.5, AXIS, align="right")]


# ---------- National visuals ----------
def year_slicer():
    default = {"filter": {"Version": 2, "From": [{"Name": "d", "Entity": "dim_year", "Type": 0}],
                          "Where": [{"Condition": {"In": {
                              "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}},
                                                          "Property": "year"}}],
                              "Values": [[{"Literal": {"Value": "2025L"}}]]}}}]}}
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [c_proj("dim_year", "year", "Year")]}},
                  "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Descending"}],
                                     "isDefaultSort": False}},
        "objects": {
            "data": [{"properties": props(mode="Dropdown")}],
            "selection": [{"properties": props(singleSelect=True, strictSingleSelect=True,
                                               selectAllCheckboxEnabled=False)}],
            "general": [{"properties": {"filter": default}}],
            "header": [{"properties": props(show=False)}],
            "items": [{"properties": props(fontColor=C(TEXT), background=C(PANEL), textSize=10.0,
                                           fontFamily=FONT_BOLD, outline="None")}],
        },
        "visualContainerObjects": chrome(panel=False),
        "syncGroup": {"groupName": "Year", "fieldChanges": True, "filterChanges": True},
    }
    return [
        fill_box("yearChip", 1124, 44, 132, 36, 40, PANEL, radius=18.0),
        label("yearLabel", 1136, 57, 46, 41, "Year", 9.0, MUTED),
        container("yearSlicer", 1180, 48, 70, 28, 42, visual, filter_config=actual_years("fActualSlicer")),
    ]


def value_card(name, x, y, w, h, z, m, size, color_, font):
    visual = {
        "visualType": "multiRowCard",
        "query": {"queryState": {"Values": {"projections": [m_proj(m)]}}},
        "objects": {
            "dataLabels": [{"properties": props(color=C(color_), fontSize=float(size), fontFamily=font)}],
            "categoryLabels": [{"properties": props(show=False)}],
            "cardTitle": [{"properties": props(show=False)}],
            "card": [{"properties": props(outline="None", barShow=False, barWeight=0.0, cardPadding=0.0,
                                          cardBackground=C(PANEL))}],
        },
        "visualContainerObjects": chrome(panel=False),
    }
    return container(name, x, y, w, h, z, visual)


def kpi_cards():
    xs = [96, 389, 682, 975]
    y, w, h = Y_CARDS, 281, H_CARDS
    value_pt = 30
    spec = [  # title, measure, value colour, unit, unit x-offset (from card x), sub
        ("Gas flared, selected year", "Flare Volume Selected Year (bcm)", ORANGE, "bcm", 108,
         ("measure", "YoY Change Selected Year (%)", "vs previous year")),
        ("Implied emissions, selected year", "CO2e Selected Year (Mt)", TEXT, "Mt CO₂e", 108,
         ("text", "World Bank average factor")),
        ("Active flare sites, selected year", "Active Sites Selected Year", TEXT, "of 476", 96,
         ("text", "381 at the 2021 peak")),
        ("Persistent sites", "Persistent Sites (12 of 14)", TEXT, "sites", 96,
         ("text", "flaring ≥12 of 14 years")),
    ]
    v = []
    for i, (x, (title, m, col, unit, ux, sub)) in enumerate(zip(xs, spec)):
        z = 100 + 10 * i
        v.append(textbox(f"card{i}Panel", x, y, w, h, z, [para(run(title, 10.0, TEXT_2, FONT_SEMI))],
                         panel=True, pad=(10, 0, 16, 16)))
        v.append(value_card(f"card{i}Value", x + 10, y + 32, 130, 56, z + 1, m, value_pt, col, FONT_BOLD))
        v.append(label(f"card{i}Unit", x + ux, y + 52, 120, z + 2, unit, 11.0, MUTED, FONT_SEMI))
        if sub[0] == "measure":
            v.append(value_card(f"card{i}Sub", x + 10, y + 76, 66, 26, z + 3, sub[1], 9, ORANGE_SOFT, FONT_SEMI))
            v.append(label(f"card{i}SubText", x + 72, y + 79, 150, z + 4, sub[2], 9.0, ORANGE_SOFT))
        else:
            v.append(label(f"card{i}SubText", x + 16, y + 79, 255, z + 3, sub[1], 9.0, MUTED))
    return v


def combo_legend():
    x = 96 + 631 - 14 - 330
    return textbox("comboLegend", x, Y_MID + 12, 330, text_h(8.5), 205, [para(
        run("■ ", 9.0, ORANGE_DARK), run("Satellite     ", 8.5, MUTED),
        run("— ", 9.0, BLUE, FONT_BOLD), run("Official (NUPRC)     ", 8.5, MUTED),
        run("- - ", 8.5, GREY_PATH, FONT_BOLD), run("Illustrative", 8.5, MUTED), align="right")])


def combo_chart():
    excl, only = "Flare Volume excl 2025 (bcm)", "Flare Volume 2025 only (bcm)"
    visual = {
        "visualType": "lineStackedColumnComboChart",
        "query": {"queryState": {
            "Category": {"projections": [c_proj("dim_year", "year", "Year")]},
            "Y": {"projections": [m_proj(excl, "Satellite"), m_proj(only, "Satellite 2025")]},
            "Y2": {"projections": [m_proj("Official Volume (bcm)", "Official (NUPRC)"),
                                   m_proj("Illustrative Path 2030 (bcm)", "Illustrative")]},
        },
            "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": props(axisType="Categorical", show=True, showAxisTitle=False,
                                                  labelColor=C(AXIS), fontSize=8.0, concatenateLabels=False)}],
            "valueAxis": [{"properties": props(show=True, showAxisTitle=False, start=0.0, end=10.0,
                                               labelColor=C(AXIS), fontSize=8.0, gridlineShow=True,
                                               gridlineColor=C("#222A35"),
                                               secShow=False, secStart=0.0, secEnd=10.0)}],
            "legend": [{"properties": props(show=False)}],
            "dataPoint": [
                {"properties": {"fill": color(ORANGE_DARK)}, "selector": {"metadata": f"_Measures.{excl}"}},
                {"properties": {"fill": color(ORANGE)}, "selector": {"metadata": f"_Measures.{only}"}},
                {"properties": {"fill": color(BLUE)}, "selector": {"metadata": "_Measures.Official Volume (bcm)"}},
                {"properties": {"fill": color(GREY_PATH)},
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
            title="Gas flared each year",
            subtitle="Billion cubic metres · satellite estimate vs official figures", pad=(12, 10, 14, 14)),
    }
    return container("nationalCombo", 96, Y_MID, 631, H_COMBO, 200, visual)


def map_scatter(y, name="flareMap", z=310, bubble=-22.0, colour=MAP_ORANGE, zero_colour=GREY_DOT,
                x=755, w=MAP_W, h=MAP_H, filter_config=None):
    zero_grey = {"solid": {"color": {"expr": {"Conditional": {
        "Cases": [{"Condition": {"Comparison": {"ComparisonKind": 1,
                                                 "Left": measure("Flare Volume Selected Year (bcm)"),
                                                 "Right": {"Literal": {"Value": "0D"}}}},
                   "Value": {"Literal": {"Value": f"'{colour}'"}}}],
        "DefaultValue": {"Literal": {"Value": f"'{zero_colour}'"}}}}}}}
    visual = {
        "visualType": "scatterChart",
        "query": {"queryState": {
            "Category": {"projections": [c_proj("dim_site", "site_id", "Site")]},
            "X": {"projections": [a_proj("dim_site", "lon", 1, "Longitude")]},
            "Y": {"projections": [a_proj("dim_site", "lat", 1, "Latitude")]},
            "Size": {"projections": [m_proj("Flare Volume Selected Year (bcm)", "Gas flared (bcm)")]},
            "Tooltips": {"projections": [
                a_proj("dim_site", "field", 3, "Field"),
                a_proj("dim_site", "operator_clean", 3, "Operator (as recorded)"),
                a_proj("dim_site", "state", 3, "State"),
            ]},
        }},
        "objects": {
            "categoryAxis": [{"properties": props(show=False, start=LON_MIN, end=LON_MAX, gridlineShow=False,
                                                  showAxisTitle=False)}],
            "valueAxis": [{"properties": props(show=False, start=LAT_MIN, end=LAT_MAX, gridlineShow=False,
                                               showAxisTitle=False)}],
            "dataPoint": [{"properties": {"fill": zero_grey}, "selector": ALL_POINTS}],
            "bubbles": [{"properties": props(bubbleSize=bubble)}],
            "legend": [{"properties": props(show=False)}],
            "categoryLabels": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": chrome(panel=False),
    }
    return container(name, x, y, w, h, z, visual, filter_config=filter_config)


def map_glow(y, x=755, w=MAP_W, h=MAP_H, filter_config=None, name="flareMapGlow", z=305):
    """Same scatter, larger and mostly transparent, drawn underneath for a soft glow; zero sites invisible."""
    return map_scatter(y, name=name, z=z, bubble=-8.0, colour=MAP_GLOW, zero_colour=PANEL, x=x, w=w, h=h,
                       filter_config=filter_config)


def state_bars():
    m = "Flare Volume Selected Year (bcm)"
    visual = {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {
            "Category": {"projections": [c_proj("dim_state", "state", "State")]},
            "Y": {"projections": [m_proj(m, "Gas flared (bcm)")]},
        },
            "sortDefinition": {"sort": [{"field": measure(m), "direction": "Descending"}], "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": props(show=True, showAxisTitle=False, labelColor=C(TEXT_2),
                                                  fontSize=8.0, innerPadding=25.0)}],
            "valueAxis": [{"properties": props(show=False, showAxisTitle=False, gridlineShow=False)}],
            "dataPoint": [{"properties": {"fill": color(ORANGE)}}],
            "labels": [{"properties": props(show=True, color=C(TEXT), fontSize=8.0, labelDisplayUnits=1.0,
                                            labelPrecision=2)}],
            "legend": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": {**chrome(title="Top 6 states by gas flared, selected year", subtitle="bcm",
                                            pad=(10, 6, 14, 14)),
                                   "title": [{"properties": props(show=True,
                                              text="Top 6 states by gas flared, selected year",
                                              fontColor=C(TEXT), fontSize=10.5, fontFamily=FONT_SEMI,
                                              titleWrap=False)}]},
    }
    return container("stateBars", 96, Y_LOW, 350, H_LOW, 400, visual,
                     filter_config={"filters": [top_n_filter("fStateTop6", "dim_state", "state", m, 6)]})


def top_n_filter(name, table, col, m, n):
    """Visual-level Top N filter on table[col] by measure m (Power BI subquery form)."""
    return {
        "name": name, "field": column(table, col), "type": "TopN",
        "filter": {"Version": 2, "From": [
            {"Name": "subquery", "Expression": {"Subquery": {"Query": {
                "Version": 2,
                "From": [{"Name": "d", "Entity": table, "Type": 0}, {"Name": "m", "Entity": "_Measures", "Type": 0}],
                "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": col},
                            "Name": "field"}],
                "OrderBy": [{"Direction": 2, "Expression": measure(m, source="m")}],
                "Top": n}}}, "Type": 2},
            {"Name": "d", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": col}}],
                "Table": {"SourceRef": {"Source": "subquery"}}}}}]},
        "howCreated": "User"}


def active_sites():
    visual = {
        "visualType": "lineChart",
        "query": {"queryState": {
            "Category": {"projections": [c_proj("dim_year", "year", "Year")]},
            "Y": {"projections": [m_proj("Active Sites", "Active flare sites"),
                                  m_proj("Active Sites Label Points", "Labelled years")]},
        },
            "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": props(axisType="Scalar", show=True, showAxisTitle=False,
                                                  labelColor=C(AXIS), fontSize=8.0, start=2012.0, end=2025.0)}],
            "valueAxis": [{"properties": props(show=True, showAxisTitle=False, start=200.0, end=400.0,
                                               labelColor=C(AXIS), fontSize=8.0, gridlineShow=True,
                                               gridlineColor=C("#222A35"))}],
            "legend": [{"properties": props(show=False)}],
            "dataPoint": [
                {"properties": {"fill": color(ORANGE)}, "selector": {"metadata": "_Measures.Active Sites"}},
                {"properties": {"fill": color(ORANGE)},
                 "selector": {"metadata": "_Measures.Active Sites Label Points"}},
            ],
            "lineStyles": [
                {"properties": props(strokeWidth=2.0, showMarker=False, shadeArea=True),
                 "selector": {"metadata": "_Measures.Active Sites"}},
                {"properties": props(strokeWidth=0.0, showMarker=True, markerSize=4.0, shadeArea=False),
                 "selector": {"metadata": "_Measures.Active Sites Label Points"}},
            ],
            "labels": [
                {"properties": props(show=True, color=C(TEXT), fontSize=9.0, labelDisplayUnits=1.0)},
                {"properties": props(showSeries=False), "selector": {"metadata": "_Measures.Active Sites"}},
                {"properties": props(showSeries=True, color=C(ORANGE_SOFT)),
                 "selector": {"metadata": "_Measures.Active Sites Label Points"}},
            ],
        },
        "visualContainerObjects": chrome(title="Active flare sites", subtitle="Sites with any flaring detected",
                                         pad=(10, 8, 14, 14)),
    }
    return container("activeSitesLine", 458, Y_LOW, 269, H_LOW, 410, visual,
                     filter_config=actual_years("fActualSitesLine"))


def national_visuals():
    v = rail(NATIONAL)
    v += header("FLARE WATCH NIGERIA", "Nigeria's gas flares, 2012–2025",
                "Satellite estimates of gas flared at upstream oil and gas sites")
    v += year_slicer()
    v += kpi_cards()
    v.append(combo_chart())
    v.append(combo_legend())
    v.append(label("pathNote", 596, Y_MID + 124, 120, 210, "Illustrative path to zero by 2030", 8.0, MUTED,
                   italic=True, lines=2))
    v.append(panel("mapPanel", 741, Y_MID, 515, 693 - Y_MID, 300, "Where the flares are",
                   "476 recorded flare sites · bubble size = gas flared in the selected year"))
    map_y = Y_MID + 60
    v.append(map_glow(map_y))
    v.append(map_scatter(map_y))
    v.append(textbox("mapLegend", 755, map_y + MAP_H + 4, 495, text_h(8.0, 2), 320, [
        para(run("● ", 8.0, ORANGE), run("Flaring in selected year    ", 8.0, TEXT_2),
             run("● ", 8.0, GREY_DOT), run("No flaring detected", 8.0, TEXT_2)),
        para(run("Outside view: 5 sites (1 inland, 4 offshore)", 8.0, MUTED))]))
    v.append(state_bars())
    v.append(active_sites())
    v += footer()
    return v


def other_visuals(name, display):
    return rail(name) + header("FLARE WATCH NIGERIA", display)


def page_json(name, display, interactions=None):
    p = {"$schema": PAGE_SCHEMA, "name": name, "displayName": display, "displayOption": "FitToPage",
         "height": 720, "width": 1280,
         "objects": {
             "background": [{"properties": {"color": color(PAGE_BG), "transparency": lit(0.0)}}],
             "outspace": [{"properties": {"color": color(PAGE_BG), "transparency": lit(0.0)}}],
         }}
    if interactions:
        p["visualInteractions"] = interactions
    return p


def write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_layout(visuals, page) -> None:
    for vc in visuals:
        p = vc["position"]
        assert 0 <= p["x"] and p["x"] + p["width"] <= 1280, (page, vc["name"], "x")
        assert 0 <= p["y"] and p["y"] + p["height"] <= 720, (page, vc["name"], "y")


def main() -> None:
    if STAGING.parent.exists():
        shutil.rmtree(STAGING.parent)
    write(PAGES_DIR / "pages.json", {"$schema": PAGES_SCHEMA, "pageOrder": [n for n, _, _ in PAGES],
                                     "activePageName": NATIONAL})
    no_filter = [{"source": "yearSlicer", "target": t, "type": "NoFilter"}
                 for t in ("nationalCombo", "activeSitesLine")]
    import pages_2_6  # noqa: E402  (imports this module's helpers)
    for name, display, _ in PAGES:
        if name == NATIONAL:
            write(PAGES_DIR / name / "page.json", page_json(name, display, no_filter))
            visuals = national_visuals()
        else:
            visuals, pairs = pages_2_6.BUILDERS[display](name)
            inter = [{"source": s_, "target": t, "type": "NoFilter"} for s_, t in pairs]
            write(PAGES_DIR / name / "page.json", page_json(name, display, inter or None))
        names = [vc["name"] for vc in visuals]
        assert len(names) == len(set(names)), f"duplicate visual names on {display}"
        check_layout(visuals, display)
        for vc in visuals:
            write(PAGES_DIR / name / "visuals" / vc["name"] / "visual.json", vc)
    n = sum(1 for _ in STAGING.rglob("*.json"))
    print(f"wrote {n} JSON files to {STAGING.relative_to(HERE.parent)}; map plot {MAP_W}x{MAP_H}")


if __name__ == "__main__":
    main()
