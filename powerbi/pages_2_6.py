"""Pages 2-6 (Sites, Operators, Cost, People, Methods) in the National night style.

Each builder returns (visuals, no_filter_pairs): no_filter_pairs are (source, target) visual names
whose interaction is set to NoFilter. Shared pieces (rail, header, Year chip, footer, fonts, map)
come from page_night_build. Wording follows the safe-claim rules (plan s7, A1-A3).
"""
from __future__ import annotations

import csv
from pathlib import Path

from page_night_build import (  # noqa: F401
    AXIS, BLUE, C, FONT, FONT_BOLD, FONT_SEMI, GREY_DOT, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, MUTED,
    ORANGE, ORANGE_DARK, ORANGE_SOFT, PANEL, TEXT, TEXT_2, actual_years, c_proj, categorical_filter, chrome,
    color, column, container, fill_box, footer, header, label, lit, m_proj, map_glow, map_scatter, measure,
    para, props, rail, run, text_h, textbox, top_n_filter, year_slicer,
)

ROOT = Path(__file__).resolve().parents[1]
EYEBROW = "FLARE WATCH NIGERIA"
TOP = 104          # content top (same as National cards)
BOTTOM = 693       # content bottom (above footer)
GRID = "#222A35"
GREY_BAR = "#8B95A3"
# Top 5 operators by total estimated volume 2012-2025 (checked in Python) -> distinct theme colours
TOP5_COLOURS = [("ExxonMobil", "#FF7A1A"), ("NEPL", "#5AB0F0"), ("Oando Oil", "#8B95A3"),
                ("Chevron", "#3FB8AF"), ("NNPC Limited", "#B07CC6")]


# ---------- generic pieces ----------
def frame(page_name, title, subtitle):
    return rail(page_name) + header(EYEBROW, title, subtitle) + year_slicer() + footer()


def eq_filter(name, m, value):
    """Visual-level filter: measure m = value (integer)."""
    return {
        "name": name, "field": measure(m), "type": "Advanced",
        "filter": {"Version": 2, "From": [{"Name": "m", "Entity": "_Measures", "Type": 0}],
                   "Where": [{"Condition": {"Comparison": {
                       "ComparisonKind": 0, "Left": measure(m, source="m"),
                       "Right": {"Literal": {"Value": f"{value}L"}}}}}]},
        "howCreated": "User"}


def filters(*fs):
    return {"filters": list(fs)} if fs else None


def value_card(name, x, y, w, h, z, projections, size, colour, font=FONT_BOLD, show_labels=False,
               filter_config=None):
    visual = {
        "visualType": "multiRowCard",
        "query": {"queryState": {"Values": {"projections": projections}}},
        "objects": {
            "dataLabels": [{"properties": props(color=C(colour), fontSize=float(size), fontFamily=font)}],
            "categoryLabels": [{"properties": props(show=show_labels, color=C(MUTED), fontSize=8.0,
                                                    fontFamily=FONT)}],
            "cardTitle": [{"properties": props(show=False)}],
            "card": [{"properties": props(outline="None", barShow=False, barWeight=0.0, cardPadding=0.0,
                                          cardBackground=C(PANEL))}],
        },
        "visualContainerObjects": chrome(panel=False),
    }
    return container(name, x, y, w, h, z, visual, filter_config=filter_config)


def kpi(prefix, x, y, w, h, z, title, m, colour=TEXT, unit=None, ux=110, sub=None, size=26, flt=None, vw=150):
    v = [textbox(f"{prefix}Panel", x, y, w, h, z, [para(run(title, 10.0, TEXT_2, FONT_SEMI))],
                 panel=True, pad=(10, 0, 16, 16)),
         value_card(f"{prefix}Value", x + 10, y + 30, w - 20 if not unit else vw, 50, z + 1, [m_proj(m)], size,
                    colour, filter_config=flt)]
    if unit:
        v.append(label(f"{prefix}Unit", x + ux, y + 48, min(140, w - ux - 6), z + 2, unit, 11.0, MUTED, FONT_SEMI))
    if sub:
        lines = 2 if len(sub) > (w - 32) / 5.2 else 1
        assert 76 + text_h(8.5, lines) <= h, (prefix, "card too short for its sub-text")
        v.append(label(f"{prefix}Sub", x + 16, y + 76, w - 28, z + 3, sub, 8.5, MUTED, lines=lines))
    return v


def multi_kpi(prefix, x, y, w, h, z, title, items, colour=TEXT, sub=None, size=20):
    """Panel with one classic card per item, shown in USD millions (display units) with the item label below."""
    v = [textbox(f"{prefix}Panel", x, y, w, h, z, [para(run(title, 10.0, TEXT_2, FONT_SEMI))],
                 panel=True, pad=(10, 0, 16, 16))]
    cw = (w - 20) // len(items)
    for i, (m, disp) in enumerate(items):
        visual = {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [m_proj(m, disp)]}}},
            "objects": {
                "labels": [{"properties": props(color=C(colour), fontSize=float(size), fontFamily=FONT_BOLD,
                                                labelDisplayUnits=1000000.0, labelPrecision=0)}],
                "categoryLabels": [{"properties": props(show=True, color=C(MUTED), fontSize=8.0, fontFamily=FONT)}],
            },
            "visualContainerObjects": chrome(panel=False),
        }
        v.append(container(f"{prefix}Value{i}", x + 10 + i * cw, y + 26, cw, 54, z + 1 + i, visual))
    if sub:
        v.append(label(f"{prefix}Sub", x + 16, y + h - 6 - text_h(8.5), w - 28, z + 9, sub, 8.5, MUTED))
    return v


def text_panel(name, x, y, w, h, z, title, lines, size=8.5, title_size=11.0):
    paras = [para(run(title, title_size, TEXT, FONT_SEMI))] + [para(run(t, size, TEXT_2)) for t in lines]
    return textbox(name, x, y, w, h, z, paras, panel=True, pad=(10, 10, 14, 14))


def slicer_chip(prefix, x, y, w, z, label_text, field_proj, single=False):
    visual = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [field_proj]}}},
        "objects": {
            "data": [{"properties": props(mode="Dropdown")}],
            "selection": [{"properties": props(singleSelect=single, strictSingleSelect=False,
                                               selectAllCheckboxEnabled=not single)}],
            "header": [{"properties": props(show=False)}],
            "items": [{"properties": props(fontColor=C(TEXT), background=C(PANEL), textSize=9.0,
                                           fontFamily=FONT_SEMI, outline="None")}],
        },
        "visualContainerObjects": chrome(panel=False),
    }
    lw = 8 + int(len(label_text) * 6.2)
    return [fill_box(f"{prefix}Chip", x, y, w, 36, z, PANEL, radius=18.0),
            label(f"{prefix}Label", x + 12, y + 7, lw, z + 1, label_text, 9.0, MUTED),
            container(prefix, x + 12 + lw, y + 4, w - 24 - lw, 28, z + 2, visual)]


def axis_props(show=True, size=8.0, colour=AXIS, **kw):
    return props(show=show, showAxisTitle=False, labelColor=C(colour), fontSize=size, **kw)


def bar_chart(name, x, y, w, h, z, title, subtitle, cat_proj, m, display, bar_colour=ORANGE, flt=None,
              decimals=2, title_size=12.0, inner=25.0, font=8.0):
    visual = {
        "visualType": "clusteredBarChart",
        "query": {"queryState": {"Category": {"projections": [cat_proj]},
                                 "Y": {"projections": [m_proj(m, display)]}},
                  "sortDefinition": {"sort": [{"field": measure(m), "direction": "Descending"}],
                                     "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": axis_props(size=font, colour=TEXT_2, innerPadding=inner)}],
            "valueAxis": [{"properties": props(show=False, showAxisTitle=False, gridlineShow=False)}],
            "dataPoint": [{"properties": {"fill": color(bar_colour)}}],
            "labels": [{"properties": props(show=True, color=C(TEXT), fontSize=8.0, labelDisplayUnits=1.0,
                                            labelPrecision=decimals)}],
            "legend": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": {**chrome(title=title, subtitle=subtitle, pad=(10, 6, 14, 14)),
                                   "title": [{"properties": props(show=True, text=title, fontColor=C(TEXT),
                                                                  fontSize=title_size, fontFamily=FONT_SEMI,
                                                                  titleWrap=False)}]},
    }
    return container(name, x, y, w, h, z, visual, filter_config=flt)


def line_chart(name, x, y, w, h, z, title, subtitle, series, legend_proj=None, flt=None, legend=False,
               y_start=None, series_colours=None):
    qs = {"Category": {"projections": [c_proj("dim_year", "year", "Year")]},
          "Y": {"projections": series}}
    if legend_proj:
        qs["Series"] = {"projections": [legend_proj]}
    visual = {
        "visualType": "lineChart",
        "query": {"queryState": qs,
                  "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                                     "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": axis_props(axisType="Scalar", start=2012.0, end=2025.0)}],
            "valueAxis": [{"properties": axis_props(gridlineShow=True, gridlineColor=C(GRID),
                                                    **({"start": float(y_start)} if y_start is not None else {}))}],
            "legend": [{"properties": props(show=legend, position="TopRight", showTitle=False,
                                            labelColor=C(MUTED), fontSize=8.0)}],
            "lineStyles": [{"properties": props(strokeWidth=2.0, showMarker=False)}],
            "labels": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": chrome(title=title, subtitle=subtitle, pad=(10, 8, 14, 14)),
    }
    if not legend_proj:
        visual["objects"]["dataPoint"] = [{"properties": {"fill": color(ORANGE)}}]
    elif series_colours:  # one colour per legend value (operator)
        tbl, col = legend_proj["queryRef"].split(".", 1)
        visual["objects"]["dataPoint"] = [
            {"properties": {"fill": color(hexc)},
             "selector": {"data": [{"scopeId": {"Comparison": {
                 "ComparisonKind": 0, "Left": column(tbl, col),
                 "Right": {"Literal": {"Value": "'" + val.replace("'", "''") + "'"}}}}}]}}
            for val, hexc in series_colours]
    return container(name, x, y, w, h, z, visual, filter_config=flt)


def column_chart(name, x, y, w, h, z, title, subtitle, m, display, flt=None):
    visual = {
        "visualType": "clusteredColumnChart",
        "query": {"queryState": {"Category": {"projections": [c_proj("dim_year", "year", "Year")]},
                                 "Y": {"projections": [m_proj(m, display)]}},
                  "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                                     "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": axis_props(axisType="Categorical", concatenateLabels=False)}],
            "valueAxis": [{"properties": axis_props(gridlineShow=True, gridlineColor=C(GRID), start=0.0)}],
            "dataPoint": [{"properties": {"fill": color(ORANGE_DARK)}}],
            "labels": [{"properties": props(show=False)}],
            "legend": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": chrome(title=title, subtitle=subtitle, pad=(10, 8, 14, 14)),
    }
    return container(name, x, y, w, h, z, visual, filter_config=flt)


def table(name, x, y, w, h, z, title, subtitle, projections, sort_field=None, flt=None, size=8.0, wrap=False,
          widths=None, title_size=12.0):
    q = {"queryState": {"Values": {"projections": projections}}}
    if sort_field:
        q["sortDefinition"] = {"sort": [{"field": sort_field, "direction": "Descending"}], "isDefaultSort": False}
    visual = {
        "visualType": "tableEx",
        "query": q,
        "objects": {
            "columnHeaders": [{"properties": props(fontColor=C(MUTED), backColor=C(PANEL), fontSize=size,
                                                   fontFamily=FONT_SEMI, wordWrap=True, outline="None")}],
            "values": [{"properties": props(fontColorPrimary=C(TEXT_2), backColorPrimary=C(PANEL),
                                            fontColorSecondary=C(TEXT_2), backColorSecondary=C("#18202A"),
                                            fontSize=size, fontFamily=FONT, wordWrap=wrap, outline="None")}],
            "grid": [{"properties": props(gridHorizontal=True, gridHorizontalColor=C(GRID), gridVertical=False,
                                          outlineColor=C(PANEL), rowPadding=1.0)}],
            "total": [{"properties": props(totals=False)}],
            **({"columnWidth": [{"properties": props(value=float(wpx)), "selector": {"metadata": ref}}
                                for ref, wpx in widths.items()]} if widths else {}),
        },
        "visualContainerObjects": {**chrome(title=title, subtitle=subtitle, pad=(10, 8, 14, 14)),
                                   "title": [{"properties": props(show=True, text=title, fontColor=C(TEXT),
                                                                  fontSize=title_size, fontFamily=FONT_SEMI,
                                                                  titleWrap=False)}]},
    }
    return container(name, x, y, w, h, z, visual, filter_config=flt)


# ---------- PAGE 2: Sites ----------
def sites(page):
    v = frame(page, "Every flare site, 2012\u20132025",
              "Satellite estimates for all 476 recorded flare sites; click a table row to find it on the map")
    rule = eq_filter("fRule", "Site Passes Persistence Rule", 1)
    v += slicer_chip("ruleSlicer", 96, TOP, 300, 50, "Persistence rule",
                     c_proj("Persistence Rule", "Rule", "Persistence rule"), single=True)
    v += slicer_chip("typeSlicer", 404, TOP, 230, 50, "Field type", c_proj("dim_site", "field_type", "Field type"))
    v += slicer_chip("locSlicer", 642, TOP, 250, 50, "Onshore/offshore", c_proj("dim_site", "location", "Location"))
    # map panel
    px, py, pw = 96, 150, 560
    mw = 532
    mh = round(mw * (LAT_MAX - LAT_MIN) / (LON_MAX - LON_MIN))
    v.append(textbox("mapPanel", px, py, pw, BOTTOM - py, 300,
                     [para(run("Where the flares are", 12.0, TEXT, FONT_SEMI)),
                      para(run("Bubble size = gas flared in the selected year \u00b7 sites filtered by the "
                               "slicers above", 9.0, MUTED))], panel=True, pad=(12, 12, 14, 14)))
    my = py + 58
    v.append(map_glow(my, x=px + 14, w=mw, h=mh, filter_config=filters(rule), name="sitesMapGlow", z=305))
    v.append(map_scatter(my, name="sitesMap", z=310, x=px + 14, w=mw, h=mh, filter_config=filters(rule)))
    v.append(textbox("mapLegend", px + 14, my + mh + 4, mw, text_h(8.0, 2), 320, [
        para(run("\u25cf ", 8.0, ORANGE), run("Flaring in selected year    ", 8.0, TEXT_2),
             run("\u25cf ", 8.0, GREY_DOT), run("No flaring detected", 8.0, TEXT_2)),
        para(run("Outside view: 5 sites (1 inland, 4 offshore)", 8.0, MUTED))]))
    # site table
    tx, tw = 664, 592
    v.append(table("sitesTable", tx, py, tw, 262, 400, "All sites", "Sorted by recent volume (mean 2023\u201325) "
                   "\u00b7 operator as recorded (World Bank 2026 release)", [
                       c_proj("dim_site", "site_id", "Site"),
                       c_proj("dim_site", "field", "Field"),
                       c_proj("dim_site", "operator_clean", "Operator (as recorded)"),
                       c_proj("dim_site", "state", "State"),
                       c_proj("dim_site", "active_years", "Active years"),
                       c_proj("dim_site", "recent_volume_bcm", "Recent bcm"),
                       m_proj("Flare Volume Selected Year (bcm)", "Selected-year bcm"),
                       c_proj("dim_site", "persistent", "Persistent"),
                   ], sort_field=column("dim_site", "recent_volume_bcm"), flt=filters(rule), size=7.0,
                   widths={"dim_site.site_id": 50.0, "dim_site.field": 100.0, "dim_site.operator_clean": 116.0,
                           "dim_site.state": 58.0, "dim_site.active_years": 46.0,
                           "dim_site.recent_volume_bcm": 54.0,
                           "_Measures.Flare Volume Selected Year (bcm)": 64.0, "dim_site.persistent": 54.0}))
    by = py + 270
    v.append(line_chart("siteTrend", tx, by, 280, BOTTOM - by, 410, "Gas flared by year",
                        "bcm \u00b7 selected sites, or all filtered sites",
                        [m_proj("Flare Volume (bcm)", "Gas flared (bcm)")], flt=actual_years("fActualTrend"),
                        y_start=0))
    top10 = {"filters": [categorical_filter("fPersistentTop", "dim_site", "persistent", [True]),
                         top_n_filter("fTop10Recent", "dim_site", "site_id", "Recent Volume (bcm)", 10)]}
    v.append(table("top10Persistent", tx + 288, by, tw - 288, BOTTOM - by, 420,
                   "Top 10 persistent sites by recent volume", "\u226512 of 14 years \u00b7 mean bcm 2023\u201325 "
                   "\u00b7 ties by site_id", [
                       c_proj("dim_site", "site_id", "Site"),
                       c_proj("dim_site", "field", "Field"),
                       m_proj("Recent Volume (bcm)", "Recent bcm"),
                   ], sort_field=measure("Recent Volume (bcm)"), flt=top10, size=7.0, title_size=10.0))
    nf = [("yearSlicer", "siteTrend"), ("yearSlicer", "top10Persistent"),
          ("ruleSlicer", "top10Persistent"), ("typeSlicer", "top10Persistent"), ("locSlicer", "top10Persistent"),
          ("sitesTable", "top10Persistent")]
    return v, nf


# ---------- PAGE 3: Operators ----------
def operators(page):
    v = frame(page, "Flaring by operator and field",
              "Satellite estimates grouped by operator and field as recorded")
    v.append(textbox("banner", 96, TOP, 1160, 30, 50, [para(
        run("\u24d8  ", 9.0, ORANGE), run("Operator as recorded in the World Bank 2026 release, applied to all "
                                         "years. Not a statement about any company's conduct.", 9.0, TEXT_2))],
        panel=True, pad=(6, 4, 14, 14)))
    y1 = 142
    named = categorical_filter("fNamedOps", "dim_operator", "is_unattributed", [False])
    v += kpi("cardTop10", 96, y1, 280, 100, 100, "Top 10 operators' share, selected year", "Top 10 Operators Share",
             ORANGE, sub="Unattributed excluded from the ranking")
    v += kpi("cardUnattr", 384, y1, 280, 100, 110, "Unattributed volume, selected year", "Unattributed Volume (bcm)",
             GREY_BAR, unit="bcm", ux=104, sub="Sites with no operator recorded")
    v.append(line_chart(
        "top5Trend", 672, y1, 584, 250, 200, "Top 5 operators, gas flared 2012\u20132025",
        "bcm \u00b7 ranked by total 2012\u20132025 \u00b7 operator as recorded (World Bank 2026 release)",
        [m_proj("Flare Volume (bcm)", "Gas flared (bcm)")],
        legend_proj=c_proj("dim_operator", "operator_clean", "Operator"), legend=True,
        series_colours=TOP5_COLOURS,
        flt={"filters": [categorical_filter("fActualTop5", "dim_year", "is_actual", [True]), named,
                         top_n_filter("fTop5Ops", "dim_operator", "operator_clean", "Flare Volume (bcm)", 5)]}))
    v.append(bar_chart(
        "opsBars", 96, 250, 568, 330, 300, "Top 12 operators by gas flared, selected year",
        "bcm \u00b7 operator as recorded (World Bank 2026 release)",
        c_proj("dim_operator", "operator_clean", "Operator"), "Flare Volume Selected Year (bcm)", "Gas flared (bcm)",
        flt={"filters": [named, top_n_filter("fTop12Ops", "dim_operator", "operator_clean",
                                             "Flare Volume Selected Year (bcm)", 12)]}))
    v.append(bar_chart(
        "unattrBar", 96, 588, 568, BOTTOM - 588, 310, "Unattributed (no operator recorded), selected year", None,
        c_proj("dim_operator", "operator_clean", "Operator"), "Flare Volume Selected Year (bcm)", "Gas flared (bcm)",
        bar_colour=GREY_BAR, title_size=10.0,
        flt=filters(categorical_filter("fUnattr", "dim_operator", "is_unattributed", [True]))))
    v.append(bar_chart(
        "fieldBars", 672, 400, 584, BOTTOM - 400, 320, "Top 10 fields by gas flared, selected year",
        "bcm \u00b7 field as recorded",
        c_proj("dim_site", "field", "Field"), "Flare Volume Selected Year (bcm)", "Gas flared (bcm)",
        inner=15.0, font=7.5,
        flt=filters(top_n_filter("fTop10Fields", "dim_site", "field", "Flare Volume Selected Year (bcm)", 10))))
    return v, [("yearSlicer", "top5Trend")]


# ---------- PAGE 4: Cost ----------
def cost(page):
    v = frame(page, "What the flared gas represents",
              "Implied emissions, gross gas value and implied flare fees for the estimated volumes")
    h = 118
    v += kpi("cardCo2", 96, TOP, 300, h, 100, "Implied emissions, selected year", "CO2e Selected Year (Mt)", TEXT,
             unit="Mt CO\u2082e", ux=104,
             sub="Implied average CO\u2082e per bcm from World Bank 2025 global totals (98% combustion efficiency)")
    v += multi_kpi("cardValue", 404, TOP, 470, h, 110,
                   "Gross value of gas flared at market prices, selected year",
                   [("Gas Value Low (USD)", "Low"), ("Gas Value Central (USD)", "Central"),
                    ("Gas Value High (USD)", "High")], ORANGE,
                   sub="At 2025 prices \u00b7 not net revenue")
    v += multi_kpi("cardFee", 882, TOP, 374, h, 120, "Implied flare fee at regulatory rates, selected year",
                   [("Implied Flare Fee Low (USD)", "Low ($0.50/Mscf)"),
                    ("Implied Flare Fee High (USD)", "High ($2.00/Mscf)")], TEXT,
                   sub="Not amounts owed or paid")
    y2 = TOP + h + 8
    v.append(column_chart("co2Columns", 96, y2, 560, 340, 200, "Implied emissions by year",
                          "Mt CO\u2082e \u00b7 implied average factor from World Bank 2025 global totals",
                          "CO2e (Mt)", "Implied CO\u2082e (Mt)", flt=actual_years("fActualCo2")))
    v.append(text_panel("costNote", 96, y2 + 348, 560, BOTTOM - (y2 + 348), 210, "Note", [
        "Gross value at market prices, not net revenue. Fees implied at regulatory rates ($0.50/$2.00 per Mscf); "
        "not amounts owed or paid."], size=9.0))
    v.append(table("assumptions", 664, y2, 592, BOTTOM - y2, 300, "Assumptions",
                   "From param_assumptions (plan s5) \u00b7 full sources on the Methods page", [
                       c_proj("param_assumptions", "parameter", "Parameter"),
                       c_proj("param_assumptions", "value", "Value"),
                       c_proj("param_assumptions", "unit", "Unit"),
                       m_proj("Assumption Source (short)", "Source"),
                       c_proj("param_assumptions", "status", "Status"),
                   ], size=7.0, wrap=True,
                   widths={"param_assumptions.parameter": 134.0, "param_assumptions.value": 82.0,
                           "param_assumptions.unit": 92.0, "_Measures.Assumption Source (short)": 172.0,
                           "param_assumptions.status": 80.0}))
    return v, [("yearSlicer", "co2Columns")]


# ---------- PAGE 5: People ----------
def people(page):
    v = frame(page, "People living near flare sites",
              "Residents within 2 km and 5 km of flare sites (WorldPop 2025); each person counted once")
    xs = [96, 389, 682, 975]
    grp = lambda g, n: filters(categorical_filter(n, "population_groups", "group", [g]))  # noqa: E731
    spec = [("Within 2 km of sites active in 2025", "Residents within 2 km", "active_2025"),
            ("Within 5 km of sites active in 2025", "Residents within 5 km", "active_2025"),
            ("Within 2 km of persistent sites", "Residents within 2 km", "persistent"),
            ("Within 5 km of persistent sites", "Residents within 5 km", "persistent")]
    for i, (x, (title, m, g)) in enumerate(zip(xs, spec)):
        v += kpi(f"pop{i}", x, TOP, 281, 100, 100 + 10 * i, title, m, ORANGE if i < 2 else TEXT,
                 unit="residents", ux=176, sub="Union of buffers; each person counted once", size=22, vw=166,
                 flt=grp(g, f"fGroup{i}"))
    y2 = TOP + 108
    v.append(bar_chart(
        "popByState", 96, y2, 560, 380, 200, "Residents within 5 km of persistent sites, by state",
        "Union of buffers of the persistent sites in each state; buffers can cross state lines",
        c_proj("dim_state", "state", "State"), "Residents within 5 km of persistent sites", "Residents",
        decimals=0))
    v.append(text_panel("peopleNote", 96, y2 + 388, 560, BOTTOM - (y2 + 388), 210, "Note", [
        "Counts of residents living near flare sites (WorldPop 2025). Proximity only \u2014 not a measure of "
        "exposure or health effects."], size=9.0))
    top10 = {"filters": [categorical_filter("fPersistentPop", "dim_site", "persistent", [True]),
                         top_n_filter("fTop10Pop", "dim_site", "site_id", "Residents within 5 km (per site)", 10)]}
    v.append(table("top10Pop", 664, y2, 592, BOTTOM - y2, 300,
                   "Top 10 persistent sites by residents within 5 km",
                   "Per-site counts can overlap between neighbouring sites \u00b7 operator as recorded "
                   "(World Bank 2026 release)", [
                       c_proj("dim_site", "site_id", "Site"),
                       c_proj("dim_site", "field", "Field"),
                       c_proj("dim_site", "operator_clean", "Operator (as recorded)"),
                       c_proj("dim_site", "state", "State"),
                       m_proj("Residents within 5 km (per site)", "Residents within 5 km"),
                   ], sort_field=measure("Residents within 5 km (per site)"), flt=top10, size=8.0))
    return v, []


# ---------- PAGE 6: Methods ----------
def _validation_counts():
    rec = list(csv.DictReader(open(ROOT / "data" / "interim" / "phase2b_recompute_comparison.csv",
                                   encoding="utf-8")))
    val = list(csv.DictReader(open(ROOT / "data" / "interim" / "phase3_validation.csv", encoding="utf-8")))
    return (sum(r["pass"] == "True" for r in rec), len(rec), sum(r["pass"] == "True" for r in val), len(val))


def methods(page):
    v = frame(page, "Sources, methods and checks",
              "How the figures are made, what they can and cannot show, and how they were checked")
    years = filters(categorical_filter("fOfficialYears", "dim_year", "year", [2021, 2022, 2023, 2024, 2025]))
    visual = {
        "visualType": "lineStackedColumnComboChart",
        "query": {"queryState": {
            "Category": {"projections": [c_proj("dim_year", "year", "Year")]},
            "Y": {"projections": [m_proj("Flare Volume (bcm)", "Satellite estimate")]},
            "Y2": {"projections": [m_proj("Official Volume (bcm)", "Official (NUPRC)")]}},
            "sortDefinition": {"sort": [{"field": column("dim_year", "year"), "direction": "Ascending"}],
                               "isDefaultSort": False}},
        "objects": {
            "categoryAxis": [{"properties": axis_props(axisType="Categorical")}],
            "valueAxis": [{"properties": axis_props(gridlineShow=True, gridlineColor=C(GRID), start=0.0, end=8.0,
                                                    secShow=False, secStart=0.0, secEnd=8.0)}],
            "legend": [{"properties": props(show=True, position="TopRight", showTitle=False,
                                            labelColor=C(MUTED), fontSize=8.0)}],
            "dataPoint": [
                {"properties": {"defaultColor": color(ORANGE_DARK)}},
                {"properties": {"fill": color(ORANGE_DARK)}, "selector": {"metadata": "_Measures.Flare Volume (bcm)"}},
                {"properties": {"fill": color(BLUE)}, "selector": {"metadata": "_Measures.Official Volume (bcm)"}}],
            "lineStyles": [{"properties": props(strokeWidth=2.0, showMarker=True, markerSize=4.0)}],
            "labels": [{"properties": props(show=False)}],
        },
        "visualContainerObjects": chrome(title="Satellite estimates and official figures, 2021\u20132025",
                                         subtitle="bcm \u00b7 differences are reported, not explained",
                                         pad=(10, 8, 14, 14)),
    }
    h1 = 270
    v.append(container("satVsOfficial", 96, TOP, 560, h1, 200, visual, filter_config=years))
    v.append(table("satVsOfficialTable", 664, TOP, 592, h1, 210, "Satellite vs official, by year",
                   "Official 2021\u201324: NUPRC via BudgIT; 2025: NUPRC figure as reported in the press (A1)", [
                       c_proj("dim_year", "year", "Year"),
                       m_proj("Flare Volume (bcm)", "Satellite (bcm)"),
                       m_proj("Official Volume (bcm)", "Official (bcm)"),
                       m_proj("Satellite \u2212 Official (bcm)", "Difference (bcm)"),
                       m_proj("Satellite \u00f7 Official", "Ratio"),
                   ], flt=years, size=8.5))
    r_ok, r_n, v_ok, v_n = _validation_counts()
    y2 = TOP + h1 + 8
    ph = (BOTTOM - y2 - 8) // 2
    cols = [96, 486, 876]
    pw = [382, 382, 380]
    panels = [
        ("Data sources and licences", [
            "Flares: World Bank GFMR satellite estimates (NOAA, Payne Institute), 2026 release.",
            "WorldPop 2025, geoBoundaries (CC BY 4.0); official: NUPRC via BudgIT, press (2025).",
            "NOSDRA flare tracker not updated after May 2025 (SweetCrude Reports, 30 Nov 2025).",
            "NUPRC target: end routine flaring by 2030 (NAN, 28 Oct 2026).",
            "Nine countries incl. Nigeria: 83% of 2025 flaring (World Bank Tracker, p.18)."]),
        ("Key definitions", [
            "Active: bcm > 0 in a year; bcm = 0 means \u201cno flaring detected\u201d.",
            "Persistent: active in at least 12 of the 14 years (sensitivity: 10 and 14).",
            "Recent volume: mean annual bcm over 2023\u20132025, zero years counted as 0."]),
        ("Known data issues (kept as recorded)", [
            "K1: site s_38320 in Kaduna (Chikun), field \u201cObi Ayima\u201d, active only in 2025; the "
            "only other site with that field is in Delta, 467 km away.",
            "K2: 33 sites labelled OFFSHORE fall inside a state\u2019s land boundary; they stay \u201cOffshore\u201d."]),
        ("Amendments to the frozen plan", [
            "A1: 2025 official figure from press reporting of NUPRC (203.9 billion scf).",
            "A2: now \u201cimplied flare fee at regulatory rates\u201d (formerly \u201cpenalty\u201d); values "
            "unchanged.",
            "A3: year table extended to 2030 for the illustrative path; no values changed."]),
        ("Safe-claim rules", [
            "Satellite figures are estimates, not measurements. Operators as recorded (World Bank 2026 release); "
            "no statement about any company\u2019s conduct.",
            "Fees implied at regulatory rates; not amounts owed or paid. Residents near sites = proximity only; "
            "no exposure or health claim.",
            "The 2030 path is illustrative, not a forecast."]),
        ("Validation results", [
            f"Independent recompute (DuckDB, shapely): {r_ok} / {r_n} pass",
            f"Power BI measures vs Python: {v_ok} / {v_n} pass",
            "Tolerances: 0.001 bcm; exact counts; 1 USD; 1 person",
            "Satellite vs official compared for 2021\u20132025"]),
    ]
    for i, (title, lines) in enumerate(panels):
        x, w = cols[i % 3], pw[i % 3]
        y = y2 + (i // 3) * (ph + 8)
        v.append(text_panel(f"methods{i}", x, y, w, ph, 300 + i, title, lines, size=7.0 if i == 0 else 7.5,
                            title_size=10.0))
    return v, [("yearSlicer", "satVsOfficial"), ("yearSlicer", "satVsOfficialTable")]


BUILDERS = {"Sites": sites, "Operators": operators, "Cost": cost, "People": people, "Methods": methods}
