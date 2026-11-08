"""Join official Statistics Canada cartographic features to the published 2024 rates."""
import csv
from hashlib import file_digest
import json
from pathlib import Path

from matplotlib import pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import PathPatch
from matplotlib.path import Path as PlotPath
import numpy as np
from shapely.geometry import shape
from shapely.geometry.polygon import orient

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/geography/provinces_2021.geojson"
RATES = ROOT / "data/reference/aggregate_jurisdiction_rates_2024.csv"
OUTPUT = ROOT / "data/reference/geography"
FIGURES = ROOT / "reports/figures"
URL = (
    "https://geo.statcan.gc.ca/geo_wa/rest/services/2021/Cartographic_boundary_files/MapServer/0/query"
    "?where=1%3D1&outFields=PRUID%2CPRNAME&outSR=3347&maxAllowableOffset=2000"
    "&returnGeometry=true&f=geojson"
)
CODES = dict(zip(
    ["10", "11", "12", "13", "24", "35", "46", "47", "48", "59", "60", "61", "62"],
    ["NL", "PE", "NS", "NB", "QC", "ON", "MB", "SK", "AB", "BC", "YT", "NT", "NU"],
))
COLORS = ["#cfebe6", "#72b5a8", "#237d73", "#12463f"]
LIMITS = [0, 5, 8, 12, 20]
METRIC = "fatalities_per_100k_population"


def load():
    with RATES.open() as stream:
        rows = list(csv.DictReader(stream))
    rates = {row["location"]: {key: float(value) for key, value in row.items()
                              if key not in {"year", "location"}} for row in rows}
    boundary = json.loads(SOURCE.read_text())
    if "3347" not in str(boundary.get("crs")) or len(boundary["features"]) != 13:
        raise ValueError("Unexpected boundary projection or feature count")
    shapes = {}
    for feature in boundary["features"]:
        info = feature["properties"]
        name = info["PRNAME"].split(" / ")[0]
        code = info["PRUID"]
        if name in shapes or code not in CODES:
            raise ValueError("Duplicate or invalid jurisdiction")
        geometry = shape(feature["geometry"]).simplify(5000, preserve_topology=False).buffer(0)
        polygons = list(geometry.geoms) if hasattr(geometry, "geoms") else [geometry]
        polygons = [orient(p) for p in polygons if p.geom_type == "Polygon" and p.area >= 25e6]
        if not polygons or not all(p.is_valid for p in polygons):
            raise ValueError(f"Invalid display geometry for {name}")
        shapes[name] = (code, polygons)
    if set(shapes) != set(rates) - {"Canada"} or len({c for c, _ in shapes.values()}) != 13:
        raise ValueError("Rates and boundary jurisdictions do not match one to one")
    if len(rows) != 14 or {row["year"] for row in rows} != {"2024"}:
        raise ValueError("Unexpected rates table population")
    return rates, shapes


def build():
    rates, shapes = load()
    palette = ListedColormap(COLORS)
    norm = BoundaryNorm(LIMITS, palette.N)
    bounds = np.array([p.bounds for _, polygons in shapes.values() for p in polygons])
    xmin, ymin = bounds[:, :2].min(axis=0)
    xmax, ymax = bounds[:, 2:].max(axis=0)
    scale = 1000 / (xmax - xmin)
    height = round((ymax - ymin) * scale, 2)
    svg = []
    fig, ax = plt.subplots(figsize=(9, 6.2), layout="constrained")
    for name, (code, polygons) in shapes.items():
        rings = [ring for p in polygons for ring in (p.exterior, *p.interiors)]
        paths = []
        commands = []
        for ring in rings:
            coordinates = list(ring.coords)
            paths.append(PlotPath(coordinates, [PlotPath.MOVETO] + [PlotPath.LINETO] * (len(coordinates) - 2)
                                  + [PlotPath.CLOSEPOLY]))
            points = [f"{(x-xmin)*scale:.2f},{(ymax-y)*scale:.2f}" for x, y in coordinates[:-1]]
            commands.append("M" + "L".join(points) + "Z")
        value = rates[name][METRIC]
        ax.add_patch(PathPatch(PlotPath.make_compound_path(*paths), facecolor=palette(norm(value)),
                               edgecolor="white", linewidth=.35))
        svg.append({"pruid": code, "abbreviation": CODES[code], "location": name,
                    "path": "".join(commands), "rates": rates[name]})
    ax.set(xlim=(xmin, xmax), ylim=(ymin, ymax), aspect="equal")
    ax.set_axis_off()
    fig.suptitle("Road fatalities per 100,000 residents", fontweight="bold", fontsize=16)
    ax.set_title("2024 published casualty rates · Canada benchmark 4.9", fontsize=10)
    colorbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=palette), ax=ax,
                           orientation="horizontal", shrink=.48, pad=.02)
    colorbar.set_ticks([2.5, 6.5, 10, 16], labels=["<5", "5–<8", "8–<12", "12+"])
    fig.savefig(FIGURES / "geography_map_2024.png", dpi=180, facecolor="white")
    plt.close(fig)

    order = sorted(shapes, key=lambda name: rates[name][METRIC])
    values = [rates[name][METRIC] for name in order]
    fig, ax = plt.subplots(figsize=(8.4, 5), layout="constrained")
    bars = ax.barh(order, values, color=[palette(norm(v)) for v in values], height=.67)
    ax.bar_label(bars, fmt="%.1f", padding=4, fontsize=9)
    ax.axvline(rates["Canada"][METRIC], color="#a3552c", linestyle="--", linewidth=1.3, label="Canada 4.9")
    ax.set(xlim=(0, max(values) * 1.14), xlabel="Fatalities per 100,000 residents")
    ax.set_title("Published 2024 casualty rates", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["right", "top", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.savefig(FIGURES / "geography_comparison_2024.png", dpi=180, facecolor="white")
    plt.close(fig)

    with SOURCE.open("rb") as stream:
        source_hash = file_digest(stream, "sha256").hexdigest()
    with RATES.open("rb") as stream:
        rates_hash = file_digest(stream, "sha256").hexdigest()
    OUTPUT.mkdir(exist_ok=True)
    payload = {"rate_year": 2024, "boundary_vintage": 2021, "projection": "EPSG:3347",
               "view_box": [0, 0, 1000, height], "canada": rates["Canada"], "jurisdictions": svg,
               "source_url": URL, "boundary_sha256": source_hash, "rates_sha256": rates_hash,
               "publisher": "Statistics Canada, Statistical Geomatics Centre",
               "licence": "https://open.canada.ca/en/open-government-licence-canada",
               "processing": "Official service response, 2 km offset request. Validated in projected metres. Display geometry simplified at 5 km, repaired with a zero-width buffer and polygon parts below 25 square kilometres omitted.",
               "retrieved_on": "2026-11-04"}
    (OUTPUT / "jurisdictions_2024.json").write_text(json.dumps(payload, ensure_ascii=False) + "\n")
    print("Verified 13 jurisdiction joins and Canada benchmark")


if __name__ == "__main__":
    build()
