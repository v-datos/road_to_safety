"use strict";

const data = JSON.parse(document.getElementById("evidence").textContent);
const integer = new Intl.NumberFormat("en-CA");
const percent = new Intl.NumberFormat("en-CA", {style: "percent", maximumFractionDigits: 2});
const number = new Intl.NumberFormat("en-CA", {minimumFractionDigits: 1, maximumFractionDigits: 1});
const svgNS = "http://www.w3.org/2000/svg";

function svgElement(name, attributes, label) {
  const element = document.createElementNS(svgNS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  if (label !== undefined) element.textContent = label;
  return element;
}

function updateTable(id, headers, records) {
  const table = document.getElementById(id);
  const header = document.createElement("tr");
  for (const label of headers) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = label;
    header.append(cell);
  }
  const body = document.createDocumentFragment();
  for (const record of records) {
    const row = document.createElement("tr");
    record.forEach((value, index) => {
      const cell = document.createElement(index === 0 ? "th" : "td");
      if (index === 0) cell.scope = "row";
      cell.textContent = value;
      row.append(cell);
    });
    body.append(row);
  }
  table.tHead.replaceChildren(header);
  table.tBodies[0].replaceChildren(body);
}

const annualMetric = document.getElementById("annual-metric");
const annualYear = document.getElementById("annual-year");

function trend() {
  const metric = annualMetric.value;
  const selected = Number(annualYear.value);
  const series = data.annual;
  const svg = document.getElementById("trend-plot");
  const top = Math.ceil(Math.max(...series.map(row => row[metric])) / (metric === "fatalities" ? 500 : 50000))
    * (metric === "fatalities" ? 500 : 50000);
  const x = year => 96 + (year - 2005) / 19 * 620;
  const y = value => 214 - value / top * 176;
  svg.replaceChildren();
  for (const value of [0, top / 2, top]) {
    svg.append(svgElement("line", {x1: 96, x2: 716, y1: y(value), y2: y(value), stroke: "#bdcdc5"}));
    svg.append(svgElement("text", {x: 85, y: y(value) + 4, "text-anchor": "end", class: "axis-label"}, integer.format(value)));
  }
  for (const year of [2005, 2010, 2015, 2020, 2024]) {
    svg.append(svgElement("text", {x: x(year), y: 240, "text-anchor": "middle", class: "axis-label"}, year));
  }
  const points = series.map(row => `${x(row.year)},${y(row[metric])}`).join(" ");
  svg.append(svgElement("polyline", {points, fill: "none", stroke: "#167c70", "stroke-width": 4}));
  const selectedValue = series.find(row => row.year === selected)[metric];
  svg.append(svgElement("circle", {cx: x(selected), cy: y(selectedValue), r: 8, fill: "#a9532d", stroke: "#fff", "stroke-width": 2}));
  document.getElementById("annual-reading").textContent =
    `${selected} · ${integer.format(selectedValue)} people ${metric === "fatalities" ? "killed" : "injured"}`;
  updateTable("annual-table", ["Year", "People killed", "People injured"],
    series.map(row => [row.year, integer.format(row.fatalities), integer.format(row.total_injuries)]));
}

const timingYear = document.getElementById("timing-year");
const timingMetric = document.getElementById("timing-metric");
const conditionField = document.getElementById("condition-field");
const fieldLabels = {"C_RALN": "Road alignment", "C_RCFG": "Road configuration",
  "C_RSUR": "Road surface", "C_TRAF": "Traffic control", "C_WTHR": "Weather"};

function currentRows(table) {
  return timingYear.value === "all" ? table.all : table.by_year.filter(row => row.C_YEAR === Number(timingYear.value));
}

function timing() {
  const all = currentRows(data.temporal.month);
  const monthRows = all.filter(row => /^([1-9]|1[0-2])$/.test(String(row.code)))
    .sort((a, b) => Number(a.code) - Number(b.code));
  const measure = timingMetric.value;
  const value = row => measure === "count" ? row.collisions : row.fatal_collisions / row.collisions;
  const format = measure === "count" ? integer.format : percent.format;
  const max = Math.max(...monthRows.map(value));
  const plot = document.getElementById("month-bars");
  plot.replaceChildren();
  for (const row of monthRows) {
    const bar = document.createElement("li");
    const label = document.createElement("span");
    label.textContent = row.label;
    const track = document.createElement("span");
    track.className = "bar-track";
    const fill = document.createElement("span");
    fill.style.width = `${100 * value(row) / max}%`;
    track.append(fill);
    const reading = document.createElement("strong");
    reading.textContent = format(value(row));
    bar.append(label, track, reading);
    plot.append(bar);
  }
  const omitted = all.filter(row => !monthRows.includes(row)).reduce((sum, row) => sum + row.collisions, 0);
  document.getElementById("month-note").textContent =
    `${integer.format(omitted)} collisions with an unknown or unavailable month are retained in the table.`;
  updateTable("month-table", ["Month", "Collisions", "Fatal collisions", "Fatal share"],
    all.map(row => [row.label, integer.format(row.collisions), integer.format(row.fatal_collisions),
      row.collisions ? percent.format(row.fatal_collisions / row.collisions) : "Unavailable"]));
  conditions();
}

function conditions() {
  const year = timingYear.value;
  const field = conditionField.value;
  const source = year === "all" ? data.conditions : data.conditions_by_year.filter(row => row.year === Number(year));
  const rows = source.filter(row => row.field === field).sort((a, b) => b.collisions - a.collisions);
  document.getElementById("condition-period").textContent =
    `${fieldLabels[field]} · ${year === "all" ? "1999–2021" : year}`;
  updateTable("condition-table", ["Category", "Collisions", "Fatal collisions", "Fatal share", "Coverage"],
    rows.map(row => [row.label, integer.format(row.collisions), integer.format(row.fatal_collisions),
      row.collisions ? percent.format(row.fatal_collisions / row.collisions) : "Unavailable",
      row.sparse_n_lt_100_or_fatal_lt_5 ? `${row.value_class} · sparse` : row.value_class]));
}

const rateMetric = document.getElementById("rate-metric");
const map = document.getElementById("jurisdiction-map");
const rateColors = ["#cfebe6", "#72b5a8", "#237d73", "#12463f"];
const descriptions = {
  fatalities_per_100k_population: "fatalities per 100,000 residents",
  injuries_per_100k_population: "injuries per 100,000 residents",
  fatalities_per_billion_vkm: "fatalities per billion vehicle-kilometres",
  injuries_per_billion_vkm: "injuries per billion vehicle-kilometres",
  fatalities_per_100k_licensed_drivers: "fatalities per 100,000 licensed drivers",
  injuries_per_100k_licensed_drivers: "injuries per 100,000 licensed drivers"
};
let focusedProvince = "Canada";
map.setAttribute("viewBox", data.geography.view_box.join(" "));
const paths = data.geography.jurisdictions.map(row => {
  const path = svgElement("path", {d: row.path, tabindex: 0, role: "button", "fill-rule": "evenodd"});
  const activate = () => {
    focusedProvince = row.location;
    mapReadout();
  };
  path.addEventListener("focus", activate);
  path.addEventListener("click", activate);
  path.addEventListener("keydown", event => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      activate();
    }
  });
  map.append(path);
  return {row, path};
});

function mapReadout() {
  const metric = rateMetric.value;
  const province = data.geography.jurisdictions.find(row => row.location === focusedProvince);
  const value = province ? province.rates[metric] : data.geography.canada[metric];
  document.getElementById("map-reading").textContent =
    `${focusedProvince} · ${number.format(value)} ${descriptions[metric]}`;
}

function showRates() {
  const metric = rateMetric.value;
  const ordered = [...data.geography.jurisdictions].sort((a, b) => b.rates[metric] - a.rates[metric]);
  const max = Math.max(...ordered.map(row => row.rates[metric]));
  const scale = metric === "fatalities_per_100k_population" ? [5, 8, 12] : [max / 4, max / 2, max * .75];
  for (const {row, path} of paths) {
    const value = row.rates[metric];
    const index = scale.filter(limit => value >= limit).length;
    path.setAttribute("fill", rateColors[index]);
    path.setAttribute("aria-label", `${row.location}, ${number.format(value)} ${descriptions[metric]}`);
    path.replaceChildren(svgElement("title", {}, `${row.location} · ${number.format(value)}`));
  }
  const legend = document.getElementById("map-legend");
  const labels = [`Below ${number.format(scale[0])}`, `${number.format(scale[0])} to under ${number.format(scale[1])}`,
    `${number.format(scale[1])} to under ${number.format(scale[2])}`, `${number.format(scale[2])} and above`];
  legend.replaceChildren(...labels.map((label, index) => {
    const item = document.createElement("li");
    const chip = document.createElement("span");
    chip.style.backgroundColor = rateColors[index];
    item.append(chip, label);
    return item;
  }));
  updateTable("jurisdiction-table", ["Jurisdiction", descriptions[metric]],
    [["Canada", number.format(data.geography.canada[metric])],
      ...ordered.map(row => [row.location, number.format(row.rates[metric])])]);
  mapReadout();
}

annualMetric.addEventListener("change", trend);
annualYear.addEventListener("input", trend);
timingYear.addEventListener("change", timing);
timingMetric.addEventListener("change", timing);
conditionField.addEventListener("change", conditions);
rateMetric.addEventListener("change", showRates);
trend();
timing();
showRates();

const operationalView = document.getElementById("operational-view");
function renderOperational() {
  if (!operationalView || !data.operational) return;
  const view = operationalView.value;
  const op = data.operational;
  const plot = document.getElementById("operational-bars");
  const reading = document.getElementById("operational-reading");
  plot.replaceChildren();
  let bars = [];
  if (view === "corridors") {
    const rows = op.corridor_top.slice(0, 10);
    reading.textContent = "Spadina Ave · 13.98 EB KSI per 100M VKT (40 of 43 KSI crashes involve Vulnerable Road Users)";
    bars = rows.map(r => ({label: r.LINEAR_NAME_FULL, val: r.eb_ksi_per_100m_vkt, text: `${r.eb_ksi_per_100m_vkt.toFixed(2)}`}));
    updateTable("operational-table",
      ["Corridor", "Length (km)", "Mean AADT", "KSI Crashes", "Fatal", "VRU KSI", "Observed KSI / 100M VKT", "EB KSI / 100M VKT", "PSI Excess KSI"],
      rows.map(r => [r.corridor_name, r.monitored_length_km.toFixed(2), integer.format(Math.round(r.mean_aadt)),
        integer.format(r.ksi_crashes), integer.format(r.fatal_crashes), integer.format(r.vru_ksi_crashes),
        r.observed_ksi_per_100m_vkt.toFixed(2), r.eb_ksi_per_100m_vkt.toFixed(2),
        (r.psi_excess_ksi >= 0 ? "+" : "") + r.psi_excess_ksi.toFixed(2)]));
  } else if (view === "road_classes") {
    const rows = op.corridor_classes.slice(0, 7);
    reading.textContent = "Major Arterials · 5.35 KSI per 100M VKT (12.6x higher per-VKT rate than Expressways at 0.42)";
    bars = rows.map(r => ({label: r.road_class, val: r.ksi_per_100m_vkt, text: `${r.ksi_per_100m_vkt.toFixed(2)}`}));
    updateTable("operational-table",
      ["Road Class", "Monitored Segments", "Length (km)", "Mean AADT", "KSI Crashes", "Fatal", "VRU KSI", "KSI / 100M VKT", "Fatal / 100M VKT", "VRU KSI / 100M VKT"],
      rows.map(r => [r.road_class, integer.format(r.monitored_segments), r.monitored_length_km.toFixed(1),
        integer.format(Math.round(r.mean_aadt)), integer.format(r.ksi_crashes), integer.format(r.fatal_crashes),
        integer.format(r.vru_ksi_crashes), r.ksi_per_100m_vkt.toFixed(3), r.fatal_per_100m_vkt.toFixed(3),
        r.vru_ksi_per_100m_vkt.toFixed(3)]));
  } else if (view === "typology") {
    const rows = op.typology_or.slice(0, 10);
    reading.textContent = "M2 Full Typology · ROC-AUC 0.7628 (+6.70 pp vs M0) · PR-AUC 7.47% (+80.0% lift)";
    bars = rows.map(r => ({label: r.feature.replace(/^has_/, ""), val: r.odds_ratio, text: `${r.odds_ratio.toFixed(2)}x`}));
    updateTable("operational-table",
      ["Typology Factor", "Group", "Collisions (1999–2021)", "Fatal Collisions", "Unadjusted Fatal %", "Adjusted Odds Ratio"],
      rows.map(r => [r.label, r.feature_group, integer.format(r.collisions_all_years),
        integer.format(r.fatal_collisions_all_years), `${r.unadjusted_fatality_rate_pct.toFixed(2)}%`, `${r.odds_ratio.toFixed(2)}x`]));
  } else if (view === "triage") {
    const rows = op.triage_bands;
    reading.textContent = "Band 1 Critical (Top 1.10% of Crashes) · 14.27% Fatality Rate (14.24x Relative Risk vs Routine)";
    bars = rows.map(r => ({label: r.band.replace(/_/g, " ").slice(0, 16), val: r.within_band_fatality_rate_pct, text: `${r.within_band_fatality_rate_pct.toFixed(2)}%`}));
    updateTable("operational-table",
      ["Risk Band (2020–2021 Test)", "Collisions", "Share of Crashes", "Fatal Crashes", "Share of Fatals", "Within-Band Fatal %", "Relative Risk vs Routine"],
      rows.map(r => [r.band, integer.format(r.collisions), `${r.share_of_all_collisions_pct.toFixed(2)}%`,
        integer.format(r.fatal_collisions), `${r.share_of_all_fatals_pct.toFixed(2)}%`,
        `${r.within_band_fatality_rate_pct.toFixed(2)}%`, `${r.relative_risk_vs_routine.toFixed(2)}x`]));
  } else if (view === "monitoring") {
    const rows = op.monitoring_drift;
    reading.textContent = "Prospective Governance · 2017–2019 GREEN (O/E 0.96–1.01) · 2020–2021 Pandemic Shift RED (O/E 1.20–1.22)";
    bars = rows.map(r => ({label: String(r.release).slice(0, 14), val: r.m2_oe_ratio, text: `${r.m2_oe_ratio.toFixed(2)} (${r.alert_status})`}));
    updateTable("operational-table",
      ["Release / Cohort", "Collisions", "Observed Fatal %", "M2 Pred Fatal %", "M2 O/E Ratio", "Max Covariate PSI", "Alert Status", "Governance Action"],
      rows.map(r => [r.release, integer.format(r.collisions), `${r.observed_fatality_pct.toFixed(3)}%`,
        `${r.m2_mean_pred_pct.toFixed(3)}%`, r.m2_oe_ratio.toFixed(3),
        `${r.max_covariate_psi.toFixed(5)} (${r.max_psi_feature})`, r.alert_status, r.recommended_action]));
  }
  const maxVal = Math.max(...bars.map(b => b.val), 0.01);
  for (const item of bars) {
    const li = document.createElement("li");
    const lbl = document.createElement("span");
    lbl.textContent = item.label;
    const track = document.createElement("span");
    track.className = "bar-track";
    const fill = document.createElement("span");
    fill.style.width = `${Math.min(100, 100 * item.val / maxVal)}%`;
    track.append(fill);
    const valNode = document.createElement("strong");
    valNode.textContent = item.text;
    li.append(lbl, track, valNode);
    plot.append(li);
  }
}
if (operationalView) {
  operationalView.addEventListener("change", renderOperational);
  renderOperational();
}
