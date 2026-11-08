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
