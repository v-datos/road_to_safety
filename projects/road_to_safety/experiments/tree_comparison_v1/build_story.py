"""Render a self-contained public story from the validated technical portfolio."""
import argparse
from html import escape
import json
from zipfile import ZIP_DEFLATED, ZipFile

from portfolio import DELIVERY, HERE, NOTES, TC, NCDB, STATCAN, collect, model_panel, page

STYLE = """
header{background:#153a38;overflow:hidden;position:relative}
header .kicker,header h1,header p{position:relative;z-index:1}
.hero-map{position:absolute;right:-1%;top:-26%;width:min(66vw,780px);opacity:.32;color:#9bc9b8;pointer-events:none}
@media(max-width:640px){.hero-map{right:-18%;top:-4%;width:92vw;opacity:.19}}
header h1{animation:arrive .55s ease-out both}
@keyframes arrive{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.controls{display:flex;flex-wrap:wrap;gap:14px 20px;align-items:center;margin:18px 0}
.controls label{display:flex;flex-wrap:wrap;align-items:center;gap:7px;font-weight:650;font-size:.92rem}
.controls select{max-width:100%}svg{display:block;width:100%;height:auto}
.axis-label{fill:#425b57;font-size:13px}
.reading{font-family:Georgia,serif;font-size:clamp(1.25rem,3vw,2.1rem);color:#146f64}
.bar-list{padding:0;list-style:none;max-width:880px}
.bar-list li{display:grid;grid-template-columns:100px 1fr 75px;gap:10px;align-items:center;padding:4px 0;font-size:.88rem}
.bar-track{height:13px;background:#dbe8e2}
.bar-track span{display:block;height:100%;background:#26877b;transition:width .28s ease}
.bar-list strong{text-align:right;font-variant-numeric:tabular-nums}
.map{background:#e9eee6;border:1px solid #c6d5cb;padding:15px;border-radius:6px}
.map path{stroke:white;stroke-width:.55;cursor:pointer;transition:fill .22s ease}
.map path:hover,.map path:focus-visible{stroke:#ac552b;stroke-width:2.1;outline:none}
.legend{list-style:none;display:flex;flex-wrap:wrap;gap:8px 16px;padding:0;font-size:.84rem}
.legend span{width:13px;height:13px;display:inline-block;vertical-align:-2px;margin-right:5px;border:1px solid #465d55}
@media(max-width:520px){.bar-list li{grid-template-columns:80px 1fr 60px;gap:6px;font-size:.79rem}.map{padding:8px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
"""


def empty_table(id, caption):
    return f'<div class="table-scroll"><table id="{id}"><caption>{caption}</caption><thead></thead><tbody></tbody></table></div>'


def build(draft=False):
    if not draft and not (DELIVERY / "technical-report.html").is_file():
        raise ValueError("The technical portfolio must be built first")
    if not draft and not (DELIVERY / "road-to-safety-policy-brief.pdf").is_file():
        raise ValueError("The policy brief must be built before the public story")
    evidence = collect(draft)
    if draft:
        summary = "Preview. The expanded model comparison is running. The final story will include reviewed results."
        crosslinks = '<a href="technical-preview.html">Read the technical preview</a>'
    else:
        model = evidence["model"]
        fitted = [row for row in model["stress"] if row["period"] == "pooled" and row["model"] != "prevalence"]
        best = min(fitted, key=lambda row: row["log_loss"])
        best_name = model["names"][best["model"]]
        summary = (f"The comparison used eight recorded conditions and timing fields. {best_name} had the lowest pooled "
                   f"log loss among the fitted models in the reused 2020–2021 comparison. "
                   f"Its threshold detected {best['recall']:.0%} of fatal collisions, "
                   f"and {best['precision']:.1%} of flagged collisions were fatal.")
        crosslinks = ('<a href="technical-report.html">Read the technical report</a> · '
                      '<a href="road-to-safety-policy-brief.pdf">Read the policy brief</a>')
    options = '<option value="all">All years · 1999–2021</option>' + "".join(
        f'<option value="{year}">{year}</option>' for year in range(1999, 2022))
    recommendations = "".join(
        f'<h3>{escape(row["title"])}</h3><p>{escape(row["action"])} {escape(row["evaluation"])} '
        f'<a href="{row["url"]}">{escape(row["source_label"])}</a></p>'
        for row in evidence["policies"])
    narrative = f"""
<nav aria-label="Story sections"><a href="#trend">National trend</a><a href="#when">When</a>
<a href="#roads">Conditions</a><a href="#where">Where</a><a href="#prediction">Severity</a><a href="#operational">Operational Toolkit</a><a href="#actions">Actions</a></nav>
<section id="trend"><div class="kicker">01 · Canada in view</div><h2>Road casualties over two decades</h2>
<p>Transport Canada recorded 2,050 road fatalities and 130,551 injuries in 2024. Explore annual published totals since 2005.</p>
<div class="controls"><label>People <select id="annual-metric"><option value="fatalities">Killed</option>
<option value="total_injuries">Injured</option></select></label>
<label>Year <input id="annual-year" type="range" min="2005" max="2024" value="2024"></label></div>
<p id="annual-reading" class="reading" aria-live="polite"></p>
<svg id="trend-plot" viewBox="0 0 760 260" role="img" aria-label="National casualty trend"></svg>
<details><summary>National data table</summary>{empty_table('annual-table','Published national counts, 2005–2024')}</details>
</section>
<section id="when"><div class="kicker">02 · Time of collision</div><h2>Busier times can have a lower fatal share</h2>
<p>The 1999–2021 records count fatal and injury collisions. In the full cohort, the late afternoon had the most collisions and 02:00 had the highest fatal share among known hours.</p>
<div class="controls"><label>Collision year <select id="timing-year">{options}</select></label>
<label>Measure <select id="timing-metric"><option value="count">Reported collisions</option>
<option value="share">Fatal share of reported collisions</option></select></label></div>
<ol class="bar-list" id="month-bars" aria-label="Monthly collision pattern"></ol>
<p id="month-note" class="note" aria-live="polite"></p>
<details><summary>Monthly data table</summary>{empty_table('month-table','Selected NCDB collisions by recorded month')}</details>
</section>
<section id="roads"><div class="kicker">03 · Conditions</div><h2>Reported outcomes vary with road conditions</h2>
<p>Explore how fatal share varies across recorded conditions. Small groups are marked. The year selection above also applies here.</p>
<div class="controls"><label>Condition <select id="condition-field">
<option value="C_RALN">Road alignment</option><option value="C_RCFG">Road configuration</option>
<option value="C_RSUR">Road surface</option><option value="C_TRAF">Traffic control</option>
<option value="C_WTHR">Weather</option></select></label></div>
<p id="condition-period" aria-live="polite"></p>
{empty_table('condition-table','Collision counts and fatal share by recorded condition')}
</section>
<section id="where"><div class="kicker">04 · Geography</div><h2>Compare published rates across Canada</h2>
<p>All 13 provinces and territories appear in the 2024 publication. Select a measure and a jurisdiction to see its reported rate.</p>
<div class="controls"><label>Rate measure <select id="rate-metric">
<option value="fatalities_per_100k_population">Fatalities per 100,000 residents</option>
<option value="injuries_per_100k_population">Injuries per 100,000 residents</option>
<option value="fatalities_per_billion_vkm">Fatalities per billion vehicle-kilometres</option>
<option value="injuries_per_billion_vkm">Injuries per billion vehicle-kilometres</option>
<option value="fatalities_per_100k_licensed_drivers">Fatalities per 100,000 licensed drivers</option>
<option value="injuries_per_100k_licensed_drivers">Injuries per 100,000 licensed drivers</option></select></label></div>
<p class="reading" id="map-reading" aria-live="polite"></p>
<div class="map"><svg id="jurisdiction-map" role="group" aria-label="Map of Canadian provinces and territories"></svg></div>
<ul id="map-legend" class="legend" aria-label="Rate colour bands"></ul>
<p class="note">{escape(NOTES)} The map uses simplified Statistics Canada 2021 boundaries.</p>
<details><summary>Jurisdiction data table</summary>{empty_table('jurisdiction-table','Published casualty rates for 2024')}</details>
</section>
<section id="prediction"><div class="kicker">05 · Severity prediction</div><h2>Models estimate severity among reported collisions</h2>
<p>{escape(summary)}</p>
<p class="note">The model estimates fatal severity among recorded collisions with casualties. Predicting whether a crash will happen requires traffic exposure and observations of uneventful travel. The tested years were previously examined.</p>
<details><summary>Model results and reliability</summary>{model_panel(evidence)}</details></section>
<section id="operational"><div class="kicker">06 · Operational Decision-Support Toolkit (Phases 1–4)</div><h2>Corridor exposure rates, road-user typologies, 3-tier triage and drift monitoring</h2>
<p>Explore the four operational extensions (retrospective research prototypes): Toronto Centreline + AADT corridor safety performance functions (exposure-proxy screening rates), person/vehicle typology severity drivers (<code>P_USER</code> and <code>V_TYPE</code>), cost-utility 3-tier operational triage, and prospective 2022+ NCDB drift monitoring (live ingestion pending).</p>
<div class="controls"><label>Operational view <select id="operational-view">
<option value="corridors">Phase 1 · Top Empirical Bayes Priority Corridors (Toronto KSI / 100M VKT)</option>
<option value="road_classes">Phase 1 · Exposure-Normalized Rates by Functional Road Class</option>
<option value="typology">Phase 2 · Road-User &amp; Vehicle Typology Adjusted Odds Ratios (M2)</option>
<option value="triage">Phase 3 · 3-Tier Operational Triage &amp; Mutually Exclusive Risk Bands (2020–2021)</option>
<option value="monitoring">Phase 4 · Prospective 2022+ NCDB Calibration &amp; Covariate Drift Monitor</option>
</select></label></div>
<p id="operational-reading" class="reading" aria-live="polite"></p>
<ol class="bar-list" id="operational-bars" aria-label="Operational decision-support comparison"></ol>
{empty_table('operational-table','Operational decision-support evidence table')}
</section>
<section id="actions"><div class="kicker">07 · Practical next steps</div><h2>Where local evidence can guide action</h2>{recommendations}
<p>{crosslinks}</p>
<p><a href="{TC}">Transport Canada statistics</a> · <a href="{NCDB}">NCDB public data</a> · <a href="{STATCAN}">Statistics Canada boundaries</a></p></section>
<noscript><p>Enable JavaScript for the controls. The technical report and policy brief include static figures and tables.</p></noscript>"""
    public_evidence = {key: evidence.get(key) for key in ("annual", "temporal", "conditions", "conditions_by_year", "geography", "operational")}
    public_evidence["temporal"].pop("weekday_hour")
    payload = json.dumps(public_evidence, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    script = f'<script type="application/json" id="evidence">{payload}</script><script>{(HERE / "story.js").read_text()}</script>'
    geography = evidence["geography"]
    view_box = " ".join(str(value) for value in geography["view_box"])
    outlines = "".join(f'<path d="{region["path"]}"/>' for region in geography["jurisdictions"])
    hero = f'<svg aria-hidden="true" class="hero-map" viewBox="{view_box}" fill="currentColor">{outlines}</svg>'
    destination = DELIVERY / ("public-preview.html" if draft else "index.html")
    destination.write_text(page("Road to Safety", "Explore when Canadian collisions are reported, how severe they are, and how published rates vary across the country.",
                                narrative, STYLE, script, hero))
    if not draft:
        with ZipFile(DELIVERY / "road-to-safety-portfolio.zip", "w", ZIP_DEFLATED) as bundle:
            for filename in ("index.html", "technical-report.html", "road-to-safety-policy-brief.pdf"):
                bundle.write(DELIVERY / filename, filename)
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true")
    build(parser.parse_args().draft)
