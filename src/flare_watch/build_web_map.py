"""Build the interactive web map (map/index.html) for GitHub Pages.

The page is a single self-contained HTML file: Leaflet is loaded from a CDN, the basemap is OpenStreetMap
(darkened with CSS; see TILE_URL), and all data are embedded as JSON generated from data/processed/ (dim_site.csv,
fact_site_year.csv). No Power BI is needed.

Run from the project root:
    .venv/Scripts/python src/flare_watch/build_web_map.py

Safe-claim rules (plan section 7, amendments A2 and A3) apply to every word on the page:
volumes are satellite estimates; operators are shown as recorded (World Bank 2026 release);
BCM = 0 is "no flaring detected"; resident counts describe proximity only.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
OUT = ROOT / "map" / "index.html"
REPO_URL = "https://github.com/malikbadmus79-max/flare-watch-nigeria"
YEARS = list(range(2012, 2026))

# Basemap. CARTO Dark Matter (https://{s}.basemaps.cartocdn.com/dark_all/...) was the first choice, but in
# November 2026 its anonymous tiles return an "API KEY REQUIRED" placeholder for every referer. The page
# therefore uses standard OpenStreetMap tiles, darkened in the browser with a CSS filter (TILE_FILTER).
# To switch provider, change these three constants and rebuild.
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
TILE_FILTER = "invert(100%) hue-rotate(180deg) brightness(78%) contrast(88%) saturate(35%)"


def _sig(x: float, digits: int = 5) -> float:
    """Round to `digits` significant figures (keeps tiny positive volumes positive)."""
    return 0.0 if x == 0 else float(f"{x:.{digits}g}")


def build_data(processed: Path = PROCESSED) -> dict:
    site = pd.read_csv(processed / "dim_site.csv")
    fact = pd.read_csv(processed / "fact_site_year.csv")
    assert sorted(fact["year"].unique()) == YEARS
    wide = fact.pivot(index="site_id", columns="year", values="bcm").reindex(columns=YEARS)
    nat = fact.groupby("year").agg(bcm=("bcm", "sum"), active=("active", "sum")).reindex(YEARS)

    sites = []
    for r in site.itertuples(index=False):
        vols = [_sig(float(v)) for v in wide.loc[r.site_id]]
        sites.append([
            r.site_id, round(float(r.lat), 5), round(float(r.lon), 5), r.field, r.operator_clean,
            r.state, r.lga, r.location, int(r.active_years), int(bool(r.persistent)),
            round(float(r.pop_2km)), round(float(r.pop_5km)), vols,
        ])
    return {
        "years": YEARS,
        "national_bcm": [round(float(v), 6) for v in nat["bcm"]],
        "national_active": [int(v) for v in nat["active"]],
        "n_sites": int(len(site)),
        "n_persistent": int(site["persistent"].sum()),
        "max_bcm": _sig(float(fact["bcm"].max())),
        "fields": ["site_id", "lat", "lon", "field", "operator", "state", "lga", "location",
                   "active_years", "persistent", "pop_2km", "pop_5km", "bcm_by_year"],
        "sites": sites,
    }


def build_html(processed: Path = PROCESSED) -> str:
    data = json.dumps(build_data(processed), separators=(",", ":"), ensure_ascii=False)
    data = data.replace("</", "<\\/")
    html = TEMPLATE.replace("__REPO_URL__", REPO_URL).replace("__TILE_URL__", TILE_URL)
    html = html.replace("__TILE_ATTRIBUTION__", TILE_ATTRIBUTION).replace("__TILE_FILTER__", TILE_FILTER)
    return html.replace("__DATA__", data)


def main() -> None:
    html = build_html()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.1f} KB)")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Flare Watch Nigeria — interactive map</title>
<meta name="description" content="Satellite estimates of gas flaring at 476 flare sites in Nigeria, 2012–2025 (World Bank GFMR 2026 release).">
<meta name="author" content="Malik Kolawole Badmus">
<meta name="theme-color" content="#0D1117">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<style>
:root{--bg:#0D1117;--panel:#151B23;--panel2:#1C2430;--line:#283241;--text:#E6EDF3;--muted:#8B97A6;
--orange:#FF7A1A;--blue:#5AB0F0;--grey:#6E7681}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--text);font:14px/1.45 "Segoe UI",Inter,system-ui,-apple-system,Roboto,Arial,sans-serif;
display:flex;flex-direction:column;height:100vh;height:100dvh;overflow:hidden}
button{font:inherit;color:inherit}
a{color:var(--blue)}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 16px;
border-bottom:1px solid var(--line);flex:none}
h1{margin:0;font-size:18px;font-weight:600;letter-spacing:.1px}
h1 .sub{color:var(--muted);font-weight:400}
h1 .dot{color:var(--orange)}
.iconbtn{display:inline-flex;align-items:center;gap:6px;background:var(--panel);border:1px solid var(--line);
border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px;white-space:nowrap}
.iconbtn:hover{border-color:var(--blue)}
main{flex:1;display:flex;min-height:0}
#map{flex:1;min-width:0;background:var(--bg)}
#panel{width:360px;flex:none;background:var(--panel);border-left:1px solid var(--line);display:flex;flex-direction:column;min-height:0}
#handle{display:none}
.scroll{overflow-y:auto;padding:16px;flex:1;min-height:0}
.yearrow{display:flex;align-items:center;gap:12px}
#play{width:40px;height:40px;border-radius:50%;border:0;background:var(--orange);color:#0D1117;cursor:pointer;
display:inline-flex;align-items:center;justify-content:center;flex:none}
#play:focus-visible,.iconbtn:focus-visible,input:focus-visible+.track{outline:2px solid var(--blue);outline-offset:2px}
#yearLabel{font-size:28px;font-weight:600;font-variant-numeric:tabular-nums;min-width:62px}
.slider{flex:1;min-width:0}
input[type=range]{width:100%;accent-color:var(--orange);margin:0}
.ticks{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;margin-top:2px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}
.card{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.card .lab{color:var(--muted);font-size:12px;line-height:1.3}
.card .val{font-size:26px;font-weight:600;font-variant-numeric:tabular-nums;margin-top:4px}
.card .val small{font-size:13px;color:var(--muted);font-weight:400;margin-left:4px}
.card.o .val{color:var(--orange)}
.card.b .val{color:var(--blue)}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);font-weight:600;margin:18px 0 8px}
.switch{display:flex;align-items:center;gap:10px;cursor:pointer;margin-top:16px;user-select:none}
.switch input{position:absolute;opacity:0;width:1px;height:1px}
.track{width:36px;height:20px;border-radius:10px;background:#2B3542;position:relative;flex:none;transition:background .2s}
.track:after{content:"";position:absolute;left:3px;top:3px;width:14px;height:14px;border-radius:50%;background:#C9D1D9;transition:transform .2s}
.switch input:checked+.track{background:var(--blue)}
.switch input:checked+.track:after{transform:translateX(16px);background:#fff}
#filterNote{color:var(--muted);font-size:12px;margin:6px 0 0 46px}
#spark{width:100%;height:auto;display:block}
#spark .hit{fill:transparent;cursor:pointer}
ol{list-style:none;margin:0;padding:0}
#top5 li button{display:grid;grid-template-columns:20px 1fr auto;gap:8px;align-items:center;width:100%;text-align:left;
background:none;border:0;border-bottom:1px solid var(--line);padding:8px 2px;cursor:pointer}
#top5 li button:hover{background:var(--panel2)}
#top5 .rk{color:var(--muted);font-variant-numeric:tabular-nums}
#top5 .nm{font-weight:600}
#top5 .op{color:var(--muted);font-size:12px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#top5 .v{color:var(--orange);font-variant-numeric:tabular-nums;white-space:nowrap}
#top5 .empty{color:var(--muted);padding:8px 2px}
.legend{display:flex;flex-direction:column;gap:6px;color:var(--muted);font-size:12px}
.legend span{display:inline-flex;align-items:center;gap:8px}
.sw{display:inline-block;border-radius:50%;flex:none}
.foot{flex:none;border-top:1px solid var(--line);padding:10px 16px;color:var(--muted);font-size:11.5px;line-height:1.4;
display:flex;gap:10px;align-items:center;justify-content:space-between}
.foot .iconbtn{font-size:12px;padding:4px 8px}
/* Leaflet theming */
.leaflet-container{background:var(--bg);font:inherit}
.leaflet-tile-pane{filter:__TILE_FILTER__}
.leaflet-control-attribution{background:rgba(13,17,23,.75)!important;color:var(--muted)!important;font-size:10.5px}
.leaflet-control-attribution a{color:#9CC9F0!important}
.leaflet-bar a{background:var(--panel)!important;color:var(--text)!important;border-color:var(--line)!important}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:var(--panel);color:var(--text);border:1px solid var(--line);box-shadow:0 6px 24px rgba(0,0,0,.5)}
.leaflet-popup-content{margin:12px 14px;font-size:13px;line-height:1.45}
.leaflet-container a.leaflet-popup-close-button{color:var(--muted)}
.pp h3{margin:0 0 2px;font-size:15px}
.pp .badge{display:inline-block;font-size:11px;padding:1px 6px;border-radius:9px;margin-left:6px;vertical-align:2px;
background:rgba(90,176,240,.15);color:var(--blue);border:1px solid rgba(90,176,240,.4)}
.pp table{border-collapse:collapse;margin-top:6px;width:100%}
.pp td{padding:2px 0;vertical-align:top}
.pp td:first-child{color:var(--muted);padding-right:10px;white-space:nowrap}
.pp .vol{color:var(--orange);font-weight:600}
.pp .note{color:var(--muted);font-size:11px;margin-top:6px}
/* info dialog */
dialog{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:12px;max-width:640px;width:calc(100% - 32px);
padding:0;max-height:calc(100% - 32px)}
dialog::backdrop{background:rgba(0,0,0,.6)}
.dlg{padding:18px 20px;overflow-y:auto}
.dlg h3{margin:0 0 10px;font-size:17px}
.dlg h4{margin:16px 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.dlg ul{margin:0;padding-left:18px}
.dlg li{margin:4px 0}
.dlg .close{float:right}
.notebox{border-left:3px solid var(--orange);background:var(--panel2);padding:8px 12px;border-radius:0 8px 8px 0}
@media (max-width:720px){
  header{padding:8px 16px}
  h1{font-size:15px;line-height:1.25}
  h1 .dash{display:none}
  h1 .sub{display:block;font-size:12px}
  .iconbtn .txt{display:none}
  main{flex-direction:column}
  #panel{width:auto;border-left:0;border-top:1px solid var(--line);border-radius:14px 14px 0 0;max-height:68%;
    box-shadow:0 -6px 20px rgba(0,0,0,.4)}
  #handle{display:flex;justify-content:center;align-items:center;gap:8px;background:none;border:0;width:100%;
    padding:8px 0 0;cursor:pointer;color:var(--muted);font-size:11px}
  #handle .bar{width:36px;height:4px;border-radius:2px;background:#3A4656}
  .scroll{padding:8px 16px 10px}
  #yearLabel{font-size:24px;min-width:54px}
  #play{width:36px;height:36px}
  .stats{margin-top:10px;gap:8px}
  .card{padding:8px 10px}
  .card .val{font-size:21px}
  #panel:not(.open) .more{display:none}
  .foot{padding:8px 16px;padding-bottom:max(8px,env(safe-area-inset-bottom))}
}
</style>
</head>
<body>
<header>
  <h1>Flare Watch Nigeria<span class="dash"> — </span><span class="sub">every gas flare site, 2012–2025</span></h1>
  <button class="iconbtn" id="infoBtn" aria-haspopup="dialog" aria-label="Sources, licences and notes">
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.5"/><rect x="7.25" y="7" width="1.5" height="5" rx=".7" fill="currentColor"/><circle cx="8" cy="4.6" r="1" fill="currentColor"/></svg>
    <span class="txt">Sources &amp; notes</span>
  </button>
</header>
<main>
  <div id="map" role="region" aria-label="Map of flare sites"></div>
  <aside id="panel" aria-label="Year controls and summary">
    <button id="handle" aria-expanded="false" aria-controls="more"><span class="bar"></span><span id="handleTxt">More details</span></button>
    <div class="scroll">
      <div class="yearrow">
        <button id="play" aria-label="Play through the years"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path id="playIcon" d="M4 2.5v11l9.5-5.5z" fill="currentColor"/></svg></button>
        <div id="yearLabel" aria-live="polite">2025</div>
        <div class="slider">
          <input type="range" id="year" min="2012" max="2025" step="1" value="2025" aria-label="Year">
          <div class="ticks"><span>2012</span><span>2025</span></div>
        </div>
      </div>
      <div class="stats">
        <div class="card o"><div class="lab">Estimated national flaring, <span class="yr">2025</span></div><div class="val"><span id="natBcm">–</span><small>bcm</small></div></div>
        <div class="card b"><div class="lab">Sites with flaring detected, <span class="yr">2025</span></div><div class="val"><span id="natActive">–</span><small>of <span id="nSites"></span></small></div></div>
      </div>
      <div class="more" id="more">
        <label class="switch"><input type="checkbox" id="persist"><span class="track"></span><span>Persistent sites only (≥12 of 14 years)</span></label>
        <div id="filterNote" hidden></div>
        <h2>Estimated national flaring, 2012–2025 (bcm)</h2>
        <svg id="spark" viewBox="0 0 320 96" role="img" aria-label="Trend of estimated national flaring, 2012 to 2025"></svg>
        <h2 id="topTitle">Top 5 sites by estimated volume, 2025 · operator as recorded (World Bank 2026 release)</h2>
        <ol id="top5"></ol>
        <h2>Legend</h2>
        <div class="legend">
          <span><i class="sw" style="width:16px;height:16px;background:rgba(255,122,26,.65);box-shadow:0 0 8px #FF7A1A"></i>Flaring detected; circle area ∝ estimated volume in the selected year</span>
          <span><i class="sw" style="width:6px;height:6px;background:#6E7681;margin:0 5px"></i>No flaring detected in the selected year</span>
        </div>
      </div>
    </div>
    <div class="foot">
      <span>Satellite estimates · NOAA, Payne Institute (Colorado School of Mines), World Bank GFMR</span>
      <button class="iconbtn" id="infoBtn2">Sources</button>
    </div>
  </aside>
</main>

<dialog id="info" aria-labelledby="infoTitle">
  <div class="dlg">
    <button class="iconbtn close" id="infoClose" aria-label="Close">Close</button>
    <h3 id="infoTitle">About this map</h3>
    <p>Estimated gas flaring at each of the <span id="nSites2"></span> flare sites in Nigeria in the World Bank GFMR 2026 release, 2012–2025. Use the slider or play button to change the year; click a site for its details.</p>
    <p class="notebox">All volumes are satellite estimates; operators as recorded; not a statement about any company's conduct; proximity only, not exposure or health.</p>
    <h4>Definitions</h4>
    <ul>
      <li><b>Estimated flaring</b>: satellite-based volume estimate in billion cubic metres (bcm). National values are the sum over all sites.</li>
      <li><b>Flaring detected</b>: estimated volume above zero in that year. A volume of zero is shown as "no flaring detected".</li>
      <li><b>Persistent site</b>: flaring detected in at least 12 of the 14 years 2012–2025.</li>
      <li><b>Operator and field</b>: as recorded in the World Bank 2026 release and applied to all years. "Unattributed" means the release names no operator.</li>
      <li><b>Residents within 2 km / 5 km</b>: WorldPop 2025 residents within that distance of the site. Counts are per site and may overlap between neighbouring sites, so they cannot be added up. They describe proximity only.</li>
    </ul>
    <h4>Sources and licences</h4>
    <ul>
      <li>Flare volumes, sites, fields and operators: World Bank Global Gas Flaring Reduction Partnership (GFMR), flare volume estimates by flare location 2012–2025, 2026 release; satellite data by NOAA and the Payne Institute (Colorado School of Mines). No explicit licence stated; World Bank disclaimer applies.</li>
      <li>Population: WorldPop 2025, 100 m constrained (R2025A v1), <a href="https://doi.org/10.5258/SOTON/WP00839">doi:10.5258/SOTON/WP00839</a>. CC BY 4.0.</li>
      <li>States and LGAs: geoBoundaries gbOpen (from GRID3 2022), <a href="https://www.geoboundaries.org">geoboundaries.org</a>. CC BY 4.0.</li>
      <li>Basemap: © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL), tiles darkened for display. Map library: <a href="https://leafletjs.com">Leaflet</a> (BSD-2-Clause).</li>
      <li>This map: code MIT; derived data and text CC BY 4.0.</li>
    </ul>
    <h4>Project</h4>
    <p>By Malik Kolawole Badmus. Methods, validation and the full dashboard: <a href="__REPO_URL__">GitHub repository</a>.</p>
  </div>
</dialog>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
"use strict";
const D = JSON.parse(document.getElementById("data").textContent);
const YEARS = D.years, LAST = YEARS.length - 1;
const S = D.sites.map(function(a){ return {id:a[0], lat:a[1], lon:a[2], field:a[3], op:a[4], state:a[5], lga:a[6],
  loc:a[7], ay:a[8], persistent:a[9] === 1, p2:a[10], p5:a[11], v:a[12]}; });
let yi = LAST, persistOnly = false, timer = null, openIdx = -1;

const $ = function(id){ return document.getElementById(id); };
function esc(s){ return String(s).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
function fmtBcm(v){ if (v >= 0.01) return v.toFixed(3); if (v >= 0.0001) return v.toFixed(4); return "<0.0001"; }
function fmtPop(n){ if (n === 0) return "0"; if (n < 10) return "<10"; return (Math.round(n / 10) * 10).toLocaleString("en-US"); }
function title(s){ return s.charAt(0) + s.slice(1).toLowerCase(); }

$("nSites").textContent = D.n_sites; $("nSites2").textContent = D.n_sites;

// ---- map ----
const map = L.map("map", {zoomControl: true, minZoom: 5, maxZoom: 14, zoomSnap: 0.25});
L.tileLayer("__TILE_URL__", {maxZoom: 19, attribution: '__TILE_ATTRIBUTION__'}).addTo(map);
function q(a, p){ const b = a.slice().sort(function(x, y){ return x - y; }); return b[Math.floor(p * (b.length - 1))]; }
const LATS = S.map(function(s){ return s.lat; }), LONS = S.map(function(s){ return s.lon; });
// initial view: the 1st-99th percentile of site coordinates (a few outlying sites would otherwise zoom the map far out)
map.fitBounds([[q(LATS, .01), q(LONS, .01)], [q(LATS, .99), q(LONS, .99)]], {padding: [24, 24]});
const renderer = L.svg({padding: 0.5}).addTo(map);  // after the view is set, so its <svg> exists
(function addGlow(){
  const ns = "http://www.w3.org/2000/svg", svg = renderer._container;
  const defs = document.createElementNS(ns, "defs");
  defs.innerHTML = '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>';
  svg.insertBefore(defs, svg.firstChild);
  const st = document.createElement("style");
  st.textContent = ".flare{filter:url(#glow)}";
  document.head.appendChild(st);
})();
const group = L.featureGroup().addTo(map);
const markers = S.map(function(s, i){
  const m = L.circleMarker([s.lat, s.lon], {renderer: renderer, radius: 3, weight: 1});
  m.bindPopup(function(){ return popupHtml(i); }, {maxWidth: 290, minWidth: 230, autoPanPaddingTopLeft: [10, 10]});
  m.on("popupopen", function(){ openIdx = i; });
  m.on("popupclose", function(){ if (openIdx === i) openIdx = -1; });
  return m;
});

// on narrow screens (< 600px) bubbles are drawn at 55% of the desktop radius so sites stay distinct
const NARROW = window.matchMedia("(max-width:599px)");
function radius(v){
  const k = NARROW.matches ? 0.55 : 1;
  return v > 0 ? Math.max(2, (3 + 24 * Math.sqrt(v / D.max_bcm)) * k) : (NARROW.matches ? 1.8 : 2.2);
}
if (NARROW.addEventListener) NARROW.addEventListener("change", function(){ render(); });

function popupHtml(i){
  const s = S[i], y = YEARS[yi], v = s.v[yi];
  const where = s.loc === "OFFSHORE" ? "Offshore" : esc(s.state) + " / " + esc(s.lga);
  const vol = v > 0 ? '<span class="vol">' + fmtBcm(v) + " bcm</span>" : "No flaring detected";
  return '<div class="pp"><h3>' + esc(s.id) + (s.persistent ? '<span class="badge">persistent</span>' : "") + "</h3>" +
    "<table>" +
    "<tr><td>Field</td><td>" + esc(s.field) + "</td></tr>" +
    "<tr><td>Operator</td><td>" + esc(s.op) + '<br><span style="color:var(--muted);font-size:11px">as recorded, World Bank 2026 release</span></td></tr>' +
    "<tr><td>State / LGA</td><td>" + where + "</td></tr>" +
    "<tr><td>Location</td><td>" + title(s.loc) + "</td></tr>" +
    "<tr><td>Estimated volume, " + y + "</td><td>" + vol + "</td></tr>" +
    "<tr><td>Years with flaring</td><td>" + s.ay + " of 14</td></tr>" +
    "<tr><td>Persistent (≥12 of 14)</td><td>" + (s.persistent ? "Yes" : "No") + "</td></tr>" +
    "<tr><td>Residents within 2 km</td><td>" + fmtPop(s.p2) + "</td></tr>" +
    "<tr><td>Residents within 5 km</td><td>" + fmtPop(s.p5) + "</td></tr>" +
    "</table>" +
    '<div class="note">Satellite estimate. Resident counts (WorldPop 2025) are per site and may overlap with neighbouring sites; proximity only.</div></div>';
}

function visible(i){ return !persistOnly || S[i].persistent; }

function render(){
  const y = YEARS[yi];
  $("year").value = y; $("yearLabel").textContent = y;
  document.querySelectorAll(".yr").forEach(function(e){ e.textContent = y; });
  $("natBcm").textContent = D.national_bcm[yi].toFixed(2);
  $("natActive").textContent = D.national_active[yi];

  const order = [];
  markers.forEach(function(m, i){
    const on = visible(i);
    if (on && !group.hasLayer(m)) group.addLayer(m);
    if (!on && group.hasLayer(m)) group.removeLayer(m);
    if (!on) return;
    const v = S[i].v[yi];
    m.setRadius(radius(v));
    m.setStyle(v > 0
      ? {color: "#FFB27A", weight: 0.8, opacity: 0.9, fillColor: "#FF7A1A", fillOpacity: 0.45}
      : {color: "#6E7681", weight: 0, opacity: 0, fillColor: "#6E7681", fillOpacity: 0.7});
    const el = m.getElement();
    if (el) el.classList.toggle("flare", v > 0);
    order.push(i);
  });
  // zero sites at the bottom, then flaring sites from largest to smallest so small circles stay clickable
  order.sort(function(a, b){ return S[b].v[yi] - S[a].v[yi]; });
  order.filter(function(i){ return S[i].v[yi] === 0; }).forEach(function(i){ markers[i].bringToFront(); });
  order.filter(function(i){ return S[i].v[yi] > 0; }).forEach(function(i){ markers[i].bringToFront(); });

  // filter note
  if (persistOnly) {
    let tot = 0, act = 0;
    S.forEach(function(s){ if (s.persistent) { tot += s.v[yi]; if (s.v[yi] > 0) act++; } });
    $("filterNote").hidden = false;
    $("filterNote").textContent = "Showing " + D.n_persistent + " persistent sites; flaring detected at " + act +
      " in " + y + ", together " + tot.toFixed(2) + " bcm (estimated). Totals above are national.";
  } else { $("filterNote").hidden = true; }

  // top 5 among shown sites (ties by ascending site id, plan section 8)
  const ranked = order.filter(function(i){ return S[i].v[yi] > 0; }).sort(function(a, b){
    return (S[b].v[yi] - S[a].v[yi]) || (S[a].id < S[b].id ? -1 : 1); }).slice(0, 5);
  $("topTitle").textContent = "Top 5 " + (persistOnly ? "persistent " : "") + "sites by estimated volume, " + y +
    " · operator as recorded (World Bank 2026 release)";
  $("top5").innerHTML = ranked.length ? ranked.map(function(i, k){
    const s = S[i];
    return '<li><button data-i="' + i + '"><span class="rk">' + (k + 1) + '</span><span><span class="nm">' + esc(s.id) +
      "</span> · " + esc(s.field) + '<span class="op">' + esc(s.op) + " · " + (s.loc === "OFFSHORE" ? "Offshore" : esc(s.state)) +
      '</span></span><span class="v">' + fmtBcm(s.v[yi]) + " bcm</span></button></li>";
  }).join("") : '<li class="empty">No flaring detected at the shown sites.</li>';

  drawSparkDot();
  if (openIdx >= 0) {
    if (visible(openIdx)) markers[openIdx].getPopup().update(); else map.closePopup();
  }
}

// ---- sparkline ----
const SW = 320, SH = 96, PL = 30, PR = 10, PT = 12, PB = 20;
const ymax = Math.ceil(Math.max.apply(null, D.national_bcm));
function sx(k){ return PL + k * (SW - PL - PR) / LAST; }
function sy(v){ return PT + (1 - v / ymax) * (SH - PT - PB); }
(function drawSpark(){
  const pts = D.national_bcm.map(function(v, k){ return sx(k).toFixed(1) + "," + sy(v).toFixed(1); });
  let h = "";
  [0, ymax / 2, ymax].forEach(function(t){
    h += '<line x1="' + PL + '" x2="' + (SW - PR) + '" y1="' + sy(t) + '" y2="' + sy(t) + '" stroke="#283241" stroke-width="1"/>' +
      '<text x="' + (PL - 6) + '" y="' + (sy(t) + 3.5) + '" fill="#8B97A6" font-size="10" text-anchor="end">' + t + "</text>";
  });
  h += '<polygon points="' + sx(0) + "," + sy(0) + " " + pts.join(" ") + " " + sx(LAST) + "," + sy(0) + '" fill="rgba(255,122,26,.12)"/>';
  h += '<polyline points="' + pts.join(" ") + '" fill="none" stroke="#FF7A1A" stroke-width="2" stroke-linejoin="round"/>';
  h += '<line id="spLine" y1="' + PT + '" y2="' + sy(0) + '" stroke="#5AB0F0" stroke-width="1" stroke-dasharray="2 2"/>';
  h += '<circle id="spDot" r="4.5" fill="#0D1117" stroke="#5AB0F0" stroke-width="2.5"/>';
  h += '<text id="spLab" font-size="10.5" fill="#E6EDF3" font-weight="600"></text>';
  h += '<text x="' + sx(0) + '" y="' + (SH - 4) + '" fill="#8B97A6" font-size="10" text-anchor="start">2012</text>';
  h += '<text x="' + sx(LAST) + '" y="' + (SH - 4) + '" fill="#8B97A6" font-size="10" text-anchor="end">2025</text>';
  const w = (SW - PL - PR) / LAST;
  YEARS.forEach(function(y, k){ h += '<rect class="hit" data-k="' + k + '" x="' + (sx(k) - w / 2) + '" y="0" width="' + w + '" height="' + SH + '"><title>' + y + ": " + D.national_bcm[k].toFixed(2) + " bcm</title></rect>"; });
  $("spark").innerHTML = h;
  $("spark").addEventListener("click", function(e){ const k = e.target.getAttribute("data-k"); if (k !== null) { stop(); yi = +k; render(); } });
})();
function drawSparkDot(){
  const x = sx(yi), y = sy(D.national_bcm[yi]);
  $("spDot").setAttribute("cx", x); $("spDot").setAttribute("cy", y);
  $("spLine").setAttribute("x1", x); $("spLine").setAttribute("x2", x);
  const lab = $("spLab");
  lab.textContent = D.national_bcm[yi].toFixed(2);
  lab.setAttribute("x", x + (yi > LAST - 3 ? -7 : 7)); lab.setAttribute("y", Math.max(y - 7, 10));
  lab.setAttribute("text-anchor", yi > LAST - 3 ? "end" : "start");
}

// ---- controls ----
const PLAY = "M4 2.5v11l9.5-5.5z", PAUSE = "M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z";
function stop(){ if (timer) { clearInterval(timer); timer = null; } $("playIcon").setAttribute("d", PLAY); $("play").setAttribute("aria-label", "Play through the years"); }
$("play").addEventListener("click", function(){
  if (timer) { stop(); return; }
  if (yi === LAST) { yi = 0; render(); }
  $("playIcon").setAttribute("d", PAUSE); $("play").setAttribute("aria-label", "Pause");
  timer = setInterval(function(){ if (yi >= LAST) { stop(); return; } yi++; render(); if (yi >= LAST) stop(); }, 900);
});
$("year").addEventListener("input", function(e){ stop(); yi = +e.target.value - YEARS[0]; render(); });
$("persist").addEventListener("change", function(e){ persistOnly = e.target.checked; render(); });
$("top5").addEventListener("click", function(e){
  const b = e.target.closest("button"); if (!b) return;
  const i = +b.getAttribute("data-i");
  if (window.matchMedia("(max-width:720px)").matches) setOpen(false);
  map.setView([S[i].lat, S[i].lon], Math.max(map.getZoom(), 10));
  markers[i].openPopup();
});
function setOpen(open){
  $("panel").classList.toggle("open", open);
  $("handle").setAttribute("aria-expanded", open); $("handleTxt").textContent = open ? "Less" : "More details";
  setTimeout(function(){ map.invalidateSize(); }, 50);
}
$("handle").addEventListener("click", function(){ setOpen(!$("panel").classList.contains("open")); });
const dlg = $("info");
function openInfo(){ if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", ""); }
$("infoBtn").addEventListener("click", openInfo); $("infoBtn2").addEventListener("click", openInfo);
$("infoClose").addEventListener("click", function(){ if (dlg.close) dlg.close(); else dlg.removeAttribute("open"); });
dlg.addEventListener("click", function(e){ if (e.target === dlg) dlg.close(); });
window.addEventListener("resize", function(){ map.invalidateSize(); });

render();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
