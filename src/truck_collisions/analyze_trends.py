"""Reproduce descriptive casualty-collision trends from validated NCDB events.

Run from the repository root: PYTHONPATH=src .venv/bin/python -m
truck_collisions.analyze_trends. No source or derived dataset is modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb


GROUPS = {
    "road_tractor": ("is_road_tractor", "Road tractor (08)"),
    "heavy_unit_truck": ("is_heavy_unit_truck", "Heavy unit truck (07)"),
    "no_recorded_tractor": ("NOT is_road_tractor", "No recorded tractor"),
    "no_recorded_tractor_known_types": ("NOT is_road_tractor AND NOT has_unknown_vehicle_type", "No recorded tractor, known types only"),
}
PERIODS = [(2012, 2021), (2012, 2019), (2016, 2021), (2016, 2019), (2019, 2020), (2020, 2021), (2019, 2021)]
BENCHMARK_URL = "https://tc.canada.ca/en/road-transportation/statistics-data/commercial-vehicle-collisions/2021/commercial-vehicle-collisions-canada-2012-2021"


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def query_rows(connection: duckdb.DuckDBPyConnection, sql: str) -> list[dict]:
    result = connection.execute(sql)
    names = [column[0] for column in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def change(first: dict, last: dict) -> dict:
    result = {}
    for measure in ["casualty_collisions", "fatal_collisions", "injury_collisions"]:
        result[f"start_{measure}"] = first[measure]
        result[f"end_{measure}"] = last[measure]
        result[f"change_{measure}"] = last[measure] - first[measure]
        result[f"pct_change_{measure}"] = 100 * (last[measure] / first[measure] - 1)
    result["start_fatal_share_pct"] = first["fatal_share_pct"]
    result["end_fatal_share_pct"] = last["fatal_share_pct"]
    result["change_fatal_share_pp"] = last["fatal_share_pct"] - first["fatal_share_pct"]
    return result


def make_figures(output: Path, annual: list[dict], benchmark: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter, StrMethodFormatter

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none", "savefig.dpi": 180})
    observed = {group: [r for r in annual if r["group"] == group and r["subset"] == "observed"]
                for group in GROUPS if group != "no_recorded_tractor_known_types"}
    colors = {"road_tractor": "#1f5b85", "heavy_unit_truck": "#a86719", "no_recorded_tractor": "#626a70"}
    styles = {"road_tractor": "-", "heavy_unit_truck": "--", "no_recorded_tractor": ":"}

    def decorate(ax, start=1999):
        ax.grid(axis="y", color="#dedede", linewidth=.7)
        ticks = [1999, 2004, 2009, 2012, 2016, 2021] if start == 1999 else [2012, 2014, 2016, 2018, 2021]
        ax.set_xticks(ticks)
        ax.set_xlim(start - .25, 2021.25)
        ax.set_ylim(bottom=0)
        ax.set_xlabel("Calendar year")

    def save(fig, name, note):
        fig.text(.07, .022, note, fontsize=9, color="#444444", va="bottom")
        fig.subplots_adjust(bottom=.19, top=.83, hspace=.42, wspace=.29)
        for extension in ["png", "svg"]:
            fig.savefig(output / f"{name}.{extension}", facecolor="white")
        plt.close(fig)

    tractor = observed["road_tractor"]
    strict = [r for r in annual if r["group"] == "road_tractor" and r["subset"] == "strict"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
    fig.suptitle("Road-tractor casualty collisions, Canada, 1999–2021", y=.97, fontsize=17)
    for ax, measure, title in zip(axes, ["injury_collisions", "fatal_collisions"], ["Injury collisions", "Fatal collisions"]):
        ax.plot([r["year"] for r in tractor], [r[measure] for r in tractor], color=colors["road_tractor"], marker="o", markersize=3, label="Observed release")
        ax.plot([r["year"] for r in strict], [r[measure] for r in strict], color="#a86719", linestyle="--", label="Strict subset")
        ax.scatter([r["year"] for r in benchmark], [r[f"published_{'fatal' if measure.startswith('fatal') else 'injury'}"] for r in benchmark], facecolors="none", edgecolors="#252525", marker="s", s=37, label="Published TC benchmark", zorder=3)
        ax.set_title(title + " (independent y scales)")
        ax.set_ylabel("Unique collision events")
        ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        decorate(ax)
    axes[0].legend(frameon=False, loc="upper right", fontsize=9)
    save(fig, "tractor_counts", "Fatal/injury events only; 08 includes road tractors with or without semitrailers.\nStrict series nearly overlaps observed; residual benchmark differences remain explicit.")

    fig, ax = plt.subplots(figsize=(11, 5.7))
    fig.suptitle("Fatal collision share among reported casualty collisions", y=.97, fontsize=17)
    for group, rows in observed.items():
        ax.plot([r["year"] for r in rows], [r["fatal_share_pct"] for r in rows], color=colors[group], linestyle=styles[group], label=GROUPS[group][1], linewidth=2)
    decorate(ax)
    ax.set_ylabel("Fatal collisions / (fatal + injury collisions)")
    ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(.5, 1.10), ncol=3, fontsize=10)
    save(fig, "fatal_share", "Observed release. This is an event severity share, not deaths per collision or risk per kilometre.\nGroups overlap: 07 may co-occur with 08; no recorded tractor includes events with unknown vehicle types.")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8))
    fig.suptitle("Changes in casualty-collision counts, 2012–2021", y=.97, fontsize=17)
    for ax, measure, title in zip(axes, ["casualty_collisions", "fatal_collisions"], ["All casualty collisions", "Fatal collisions"]):
        for group, rows in observed.items():
            rows = [r for r in rows if r["year"] >= 2012]
            base = rows[0][measure]
            ax.plot([r["year"] for r in rows], [100 * r[measure] / base for r in rows], color=colors[group], linestyle=styles[group], marker="o", markersize=3, label=GROUPS[group][1])
        ax.axhline(100, color="#555555", linewidth=.7)
        ax.set_title(title)
        ax.set_ylabel("Count index (2012 = 100)")
        decorate(ax, 2012)
    axes[0].legend(frameon=False, loc="lower left", fontsize=9)
    save(fig, "indexed_comparison", "Indices compare count changes, not traffic exposure or collision risk. Heavy unit truck events may overlap tractor events.\nNo recorded tractor is not a car-only group; 2022–2025 national microdata are absent.")


def report(annual: list[dict], changes: list[dict], sensitivity: list[dict], benchmark: list[dict], pooled: list[dict]) -> str:
    index = {(r["group"], r["subset"], r["year"]): r for r in annual}
    tractor = lambda year: index[("road_tractor", "observed", year)]
    def table(headers, rows):
        return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] + ["| " + " | ".join(map(str, row)) + " |" for row in rows])
    dec = next(r for r in changes if r["group"] == "road_tractor" and r["subset"] == "observed" and r["start_year"] == 2012 and r["end_year"] == 2021)
    recent = next(r for r in changes if r["group"] == "road_tractor" and r["subset"] == "observed" and r["start_year"] == 2016 and r["end_year"] == 2021)
    text = ["# Descriptive road-tractor casualty-collision trends", "",
            "## Answer and scope", "",
            f"In this public NCDB release, recorded road-tractor casualty collisions fell from {tractor(2012)['casualty_collisions']:,} in 2012 to {tractor(2021)['casualty_collisions']:,} in 2021 ({dec['pct_change_casualty_collisions']:+.1f}%). Fatal collisions fell from {tractor(2012)['fatal_collisions']} to {tractor(2021)['fatal_collisions']} ({dec['pct_change_fatal_collisions']:+.1f}%), while injury collisions fell {abs(dec['pct_change_injury_collisions']):.1f}%. Because fatal events fell more slowly, the fatal share rose from {tractor(2012)['fatal_share_pct']:.2f}% to {tractor(2021)['fatal_share_pct']:.2f}% ({dec['change_fatal_share_pp']:+.2f} percentage points). Fewer reported casualty collisions and a larger fatal share can coexist. The data do not establish more deaths per collision, increased risk per kilometre, or the reasons for the changes.", "",
            f"The recent available segment, 2016–2021, also declined: {recent['start_casualty_collisions']:,} to {recent['end_casualty_collisions']:,} casualty events ({recent['pct_change_casualty_collisions']:+.1f}%), with fatal share changing from {recent['start_fatal_share_pct']:.2f}% to {recent['end_fatal_share_pct']:.2f}%.", "",
            "The original research target remains **2016–2025 and is unfulfilled**. Event microdata here cover 1999–2021. The complete 2012–2021 window is an explicitly labeled available-data decade that can be checked against Transport Canada's published historical benchmark. Full 1999–2021 annual tables are included for context; choosing that historical window does not extend coverage to 2025.", "",
            "![Annual tractor counts](tractor_counts.png)", "",
            "## Annual tractor results", "",
            table(["Year", "Casualty events", "Fatal", "Injury", "Fatal share", "Strict exclusions"], [[r["year"], f"{r['casualty_collisions']:,}", r["fatal_collisions"], f"{r['injury_collisions']:,}", f"{r['fatal_share_pct']:.2f}%", next(s["excluded_collisions"] for s in sensitivity if s["year"] == r["year"] and s["group"] == "road_tractor")] for r in annual if r["group"] == "road_tractor" and r["subset"] == "observed"]), "",
            "## Period comparisons and the 2020 disruption", "",
            table(["Period", "Casualty change", "Fatal change", "Injury change", "Fatal share change (pp)"], [[f"{r['start_year']}–{r['end_year']}", f"{r['pct_change_casualty_collisions']:+.2f}%", f"{r['pct_change_fatal_collisions']:+.2f}%", f"{r['pct_change_injury_collisions']:+.2f}%", f"{r['change_fatal_share_pp']:+.2f}"] for r in changes if r["group"] == "road_tractor" and r["subset"] == "observed"]), "",
            "The 2012–2019 comparison shows the direction before 2020; the 2019–2020 and 2020–2021 comparisons show the abrupt fall and partial rebound. The 2019–2021 endpoint comparison shows whether the rebound restored the 2019 count. Calendar 2020 is retained and shown explicitly. These descriptions identify timing, not a causal pandemic estimate. A 2021 endpoint remains affected by the post-2019 period, so the 2012–2021 decline should not be described as an undisturbed secular trend.", "",
            f"Observed fatal counts changed from {tractor(2016)['fatal_collisions']} in 2016 to {tractor(2019)['fatal_collisions']} in 2019 ({100*(tractor(2019)['fatal_collisions']/tractor(2016)['fatal_collisions']-1):+.2f}%). Source selection is documented in docs/source_release_update.md; the previously used CSV and its results are preserved as a baseline. The published comparison remains separate from the selected microdata.", "",
            "## Comparison populations", "",
            "![Indexed comparisons](indexed_comparison.png)", "",
            table(["Group", "Period", "Casualty start → end", "Casualty change", "Fatal change", "Fatal share start → end"], [[GROUPS[r["group"]][1], f"{r['start_year']}–{r['end_year']}", f"{r['start_casualty_collisions']:,} → {r['end_casualty_collisions']:,}", f"{r['pct_change_casualty_collisions']:+.2f}%", f"{r['pct_change_fatal_collisions']:+.2f}%", f"{r['start_fatal_share_pct']:.2f}% → {r['end_fatal_share_pct']:.2f}%"] for r in changes if r["subset"] == "observed" and (r["start_year"], r["end_year"]) in [(2012, 2021), (2016, 2021)]]), "",
            "Road tractor means at least one recorded vehicle type 08; heavy unit truck means at least one 07. Those two groups overlap and must not be summed. The no-recorded-tractor group is the complement of recorded 08 involvement, including heavy unit trucks and other vehicles. It is not a car-only comparison and does not establish true absence of tractors when type is unknown. `annual_counts.csv` includes unknown-type counts, overlap counts, and fatality-share denominators. Changes can reflect reporting, vehicle classification, traffic exposure or population composition as well as underlying safety.", "",
            f"The fatal-share increase is not unique to tractors: the no-recorded-tractor share rose from {index[('no_recorded_tractor','observed',2012)]['fatal_share_pct']:.2f}% in 2012 to {index[('no_recorded_tractor','observed',2021)]['fatal_share_pct']:.2f}% in 2021, and the heavy unit truck share rose from {index[('heavy_unit_truck','observed',2012)]['fatal_share_pct']:.2f}% to {index[('heavy_unit_truck','observed',2021)]['fatal_share_pct']:.2f}%. The tractor/no-recorded-tractor share ratio changed from {tractor(2012)['fatal_share_pct']/index[('no_recorded_tractor','observed',2012)]['fatal_share_pct']:.2f} to {tractor(2021)['fatal_share_pct']/index[('no_recorded_tractor','observed',2021)]['fatal_share_pct']:.2f}. These ratios describe severity mix among reported casualty events, not relative driving risk. The known-types-only comparator excludes any event flagged with other/unknown/unavailable vehicle types and is shown in the comparison tables as a sensitivity; it cannot rule out unflagged misclassification.", "",
            "![Fatal collision share](fatal_share.png)", "",
            "## Sensitivity and unresolved source differences", "",
            f"Observed counts retain all events; the strict subset requires `is_analysis_candidate=true`. For tractors this removes {sum(r['excluded_collisions'] for r in sensitivity if r['group']=='road_tractor'):,} of {sum(r['casualty_collisions'] for r in annual if r['group']=='road_tractor' and r['subset']=='observed'):,} events over 1999–2021. These exclusions are an alternative filter, not corrections, and can disproportionately remove complex collisions. Both series appear in the annual and endpoint tables. The observed/strict annual differences, fatal-share changes, and the no-tractor unknown-type share are exported explicitly.", "",
            "The tiny 2020–2021 tractor fatal-share movement is sensitive to those exclusions: observed share changes from 7.4458% to 7.4253% (−0.0205 percentage points), but strict share changes from 7.3724% to 7.4286% (+0.0562 points). No direction is claimed for that small one-year severity-share movement.", "",
            f"[Transport Canada's published Table 1]({BENCHMARK_URL}) remains a separate comparison series. In 2019 selected microdata contain {tractor(2019)['fatal_collisions']:,} fatal and {tractor(2019)['injury_collisions']:,} injury tractor events; the publication reports {next(r['published_fatal'] for r in benchmark if r['year']==2019):,} and {next(r['published_injury'] for r in benchmark if r['year']==2019):,}. The source-version update substantially reduced the earlier discrepancy; residual differences remain unresolved. No synthetic records or count adjustments force agreement.", "",
            table(["Year", "Observed total", "Published total", "Observed fatal share", "Published fatal share", "Difference (events)"], [[r["year"], r["observed_total"], r["published_total"], f"{r['observed_fatal_share_pct']:.2f}%", f"{r['published_fatal_share_pct']:.2f}%", r["total_difference"]] for r in benchmark]), "",
            "`benchmark_period_changes.csv` repeats every endpoint comparison for the separately published series. Results with a 2019 endpoint depend on the source version. The principal 2012–2021 and 2016–2021 endpoint comparisons are unaffected by excluding the interior year 2019; source-specific annual differences are shown. No fitted trend is needed to answer the descriptive question, so there is no model in which 2019 is silently retained or omitted.", "",
            "The following pooled comparisons show sensitivity to omitting 2019, the year with a substantial former source-version discrepancy and a residual benchmark difference. Annual averages divide event totals by included years. Fatal shares use summed fatal counts divided by summed fatal plus injury counts, not an unweighted mean of annual percentages. These block summaries are descriptive and are not adjusted for differing exposures or year composition.", "",
            table(["Block", "Subset", "Years", "Events", "Mean annual events", "Fatal share"], [[r["period"], r["subset"], r["included_years"], f"{r['casualty_collisions']:,}", f"{r['mean_annual_collisions']:.1f}", f"{r['fatal_share_pct']:.2f}%"] for r in pooled if r["group"] == "road_tractor"]), "",
            "## Methods and reproducibility", "",
            "The input is `data/derived/ncdb/collisions.parquet`, one event per `(C_YEAR,C_CASE)`. Severity 1 denotes fatal, 2 injury; casualty count is their sum. Unknown severity would be exported in diagnostics and would stop this analysis rather than entering a severity denominator. Events with multiple tractors count once. No person-record sums or vehicle-involvement totals are used. Input coverage and key uniqueness are asserted. Annual tractor counts and strict counts are separately recomputed and reconciled against the dataset build's `annual_counts.csv` before reporting.", "",
            "Endpoint percent change is `100 × (end/start − 1)`. Fatal share is `100 × fatal/(fatal+injury)`; share differences are percentage points. There are no fitted trend lines, p-values, confidence intervals or claims of statistical significance. These are complete counts of observed events in this release, rather than a random sample; the material uncertainty is completeness, classification, revisions, exposure and benchmark disagreement. Lack of a sampling interval does not establish complete national ascertainment.", "",
            "Run `uv sync --extra analysis`, then `PYTHONPATH=src MPLCONFIGDIR=/tmp/collisions-matplotlib .venv/bin/python -m truck_collisions.analyze_trends` from the repository root. The default output is `reports/trends/`. `summary.json` records input hashes, exact principal results, dataset coverage, software versions and checks. CSVs retain unrounded computational values; report and chart display values are rounded. Figures are reproducible standalone PNG and SVG exports, with exported plotted series in `annual_counts.csv` and `benchmark_comparison.csv`.", "",
            "Source provenance: selected 1999–2013 years from the inherited 1999–2017 file and official annual 2014–2021 releases are mapped in `data/sources.json`; input record hashes are retained in `data/derived/ncdb/source_manifest.json`. See `docs/dataset_contract.md`, `docs/dataset_validation.md`, `docs/ncdb_2019_investigation.md`, and the [official NCDB catalogue](https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a). Historical years before 2012 lack an external tractor-event benchmark in this project. The report is a description of this public release, not a fully reconciled current national series.", "",
            "## What this establishes and what comes next", "",
            "The available release supports lower road-tractor casualty-collision counts over 2012–2021 and a higher fatal collision share at the endpoint. It supports neither a 2016–2025 conclusion nor an explanation of why the shares changed. The pre-2020 comparison and benchmark sensitivity prevent the 2021 endpoint from carrying that interpretation alone.", "",
            "Person identities and casualty scenarios are now validated separately in reports/casualties/findings.md. Before exposure rates, reconcile a compatible tractor distance denominator. Configuration and environmental comparisons remain a subsequent phase. Policy effects, freight activity, vehicle age, pre-impact actions and provincial differences need additional data and suitable comparisons. Public-data availability for 2022–2025 and residual benchmark differences remain explicit; neither aggregate context nor source-version repair supplies missing national event records.", ""]
    return "\n".join(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/derived/ncdb"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/trends"))
    args = parser.parse_args()
    data, output = args.data_dir.resolve(), args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.read_parquet(str(data / "collisions.parquet")).create_view("events")
    diagnostics = query_rows(connection, "SELECT count(*) AS events, count(DISTINCT (C_YEAR,C_CASE)) AS unique_keys, min(C_YEAR) AS first_year, max(C_YEAR) AS last_year, count(DISTINCT C_YEAR) AS year_count, count(*) FILTER (WHERE C_SEV IS NULL OR C_SEV NOT IN ('1','2')) AS unsupported_severity FROM events")[0]
    assert diagnostics["events"] == diagnostics["unique_keys"], diagnostics
    assert (diagnostics["first_year"], diagnostics["last_year"], diagnostics["year_count"]) == (1999, 2021, 23), diagnostics
    assert diagnostics["unsupported_severity"] == 0, diagnostics
    annual = []
    for group, (predicate, _) in GROUPS.items():
        for subset, subset_predicate in [("observed", "TRUE"), ("strict", "is_analysis_candidate")]:
            rows = query_rows(connection, f"""SELECT C_YEAR AS year, '{group}' AS "group", '{subset}' AS subset,
                count(*) AS casualty_collisions, count(*) FILTER (WHERE C_SEV='1') AS fatal_collisions,
                count(*) FILTER (WHERE C_SEV='2') AS injury_collisions,
                count(*) FILTER (WHERE has_unknown_vehicle_type) AS unknown_type_events,
                count(*) FILTER (WHERE is_road_tractor AND is_heavy_unit_truck) AS tractor_heavy_overlap_events
                FROM events WHERE ({predicate}) AND {subset_predicate} GROUP BY C_YEAR ORDER BY C_YEAR""")
            for row in rows:
                assert row["casualty_collisions"] == row["fatal_collisions"] + row["injury_collisions"]
                row["fatal_share_pct"] = 100 * row["fatal_collisions"] / row["casualty_collisions"]
                row["unknown_type_event_share_pct"] = 100 * row["unknown_type_events"] / row["casualty_collisions"]
            annual.extend(rows)
    index = {(r["group"], r["subset"], r["year"]): r for r in annual}
    with (data / "annual_counts.csv").open() as stream:
        for build in csv.DictReader(stream):
            for subset in ["observed", "strict"]:
                row = index[("road_tractor", subset, int(build["year"]))]
                for measure, build_measure in [("casualty_collisions", f"{subset}_tractor_collisions"), ("fatal_collisions", f"{subset}_fatal_tractor_collisions"), ("injury_collisions", f"{subset}_injury_tractor_collisions")]:
                    assert row[measure] == int(build[build_measure]), (row, build)
            assert index[("road_tractor", "observed", int(build["year"]))]["casualty_collisions"] + index[("no_recorded_tractor", "observed", int(build["year"]))]["casualty_collisions"] == int(build["all_casualty_collisions"])
    changes = [{"group": group, "subset": subset, "start_year": start, "end_year": end,
                **change(index[(group, subset, start)], index[(group, subset, end)])}
               for group in GROUPS for subset in ["observed", "strict"] for start, end in PERIODS]
    sensitivity = []
    for group in GROUPS:
        for year in range(1999, 2022):
            observed, strict = index[(group, "observed", year)], index[(group, "strict", year)]
            sensitivity.append({"year": year, "group": group,
                                "observed_collisions": observed["casualty_collisions"], "strict_collisions": strict["casualty_collisions"],
                                "excluded_collisions": observed["casualty_collisions"] - strict["casualty_collisions"],
                                "excluded_fatal_collisions": observed["fatal_collisions"] - strict["fatal_collisions"],
                                "excluded_injury_collisions": observed["injury_collisions"] - strict["injury_collisions"],
                                "observed_fatal_share_pct": observed["fatal_share_pct"], "strict_fatal_share_pct": strict["fatal_share_pct"],
                                "strict_minus_observed_fatal_share_pp": strict["fatal_share_pct"] - observed["fatal_share_pct"]})
    benchmark = []
    published = {}
    with (data / "reconciliation.csv").open() as stream:
        for row in csv.DictReader(stream):
            if not row["published_fatal"]:
                continue
            year, fatal, injury = int(row["year"]), int(row["published_fatal"]), int(row["published_injury"])
            observed = index[("road_tractor", "observed", year)]
            published[year] = {"casualty_collisions": fatal + injury, "fatal_collisions": fatal, "injury_collisions": injury, "fatal_share_pct": 100 * fatal / (fatal + injury)}
            benchmark.append({"year": year, "observed_fatal": observed["fatal_collisions"], "published_fatal": fatal,
                              "observed_injury": observed["injury_collisions"], "published_injury": injury,
                              "observed_total": observed["casualty_collisions"], "published_total": fatal + injury,
                              "total_difference": observed["casualty_collisions"] - fatal - injury,
                              "observed_fatal_share_pct": observed["fatal_share_pct"], "published_fatal_share_pct": published[year]["fatal_share_pct"],
                              "status": row["external_reconciliation"]})
    benchmark_changes = [{"series": "published_transport_canada", "start_year": start, "end_year": end, **change(published[start], published[end])} for start, end in PERIODS]
    pooled = []
    for group in GROUPS:
        for subset in ["observed", "strict"]:
            for label, years in [("2012–2015", list(range(2012, 2016))), ("2016–2021", list(range(2016, 2022))), ("2016–2021 excluding 2019", [2016, 2017, 2018, 2020, 2021]), ("2012–2019", list(range(2012, 2020))), ("2012–2019 excluding 2019", list(range(2012, 2019))), ("2021", [2021])]:
                rows = [index[(group, subset, year)] for year in years]
                total, fatal, injury = [sum(r[measure] for r in rows) for measure in ["casualty_collisions", "fatal_collisions", "injury_collisions"]]
                pooled.append({"group": group, "subset": subset, "period": label, "included_years": ";".join(map(str, years)), "year_count": len(years), "casualty_collisions": total, "fatal_collisions": fatal, "injury_collisions": injury, "mean_annual_collisions": total / len(years), "fatal_share_pct": 100 * fatal / total})
    for filename, rows in [("annual_counts.csv", annual), ("period_changes.csv", changes), ("strict_sensitivity.csv", sensitivity), ("benchmark_comparison.csv", benchmark), ("benchmark_period_changes.csv", benchmark_changes), ("pooled_periods.csv", pooled)]:
        write_csv(output / filename, rows)
    make_figures(output, annual, benchmark)
    (output / "findings.md").write_text(report(annual, changes, sensitivity, benchmark, pooled), encoding="utf-8")
    import matplotlib
    summary = {"created_utc": datetime.now(timezone.utc).isoformat(), "question": "Did recorded road-tractor casualty collision counts and fatal share change?", "target_period": "2016–2025", "target_period_fulfilled": False,
               "available_period": "1999–2021", "available_data_decade": "2012–2021", "unit": "unique casualty-collision event", "vehicle_definition": "recorded V_TYPE=08, road tractor with or without semitrailer",
               "input_sha256": {name: sha256(data / name) for name in ["collisions.parquet", "annual_counts.csv", "reconciliation.csv", "source_manifest.json", "validation.json"]},
               "analysis_code_sha256": sha256(Path(__file__)), "dataset_validation_metadata": json.loads((data / "validation.json").read_text()), "source_manifest": json.loads((data / "source_manifest.json").read_text()), "duckdb_version": duckdb.__version__, "matplotlib_version": matplotlib.__version__, "diagnostics": diagnostics,
               "checks_passed": ["unique event keys", "1999–2021 complete year coverage", "severity is fatal or injury", "fatal plus injury equals casualty totals", "annual observed and strict tractor counts agree with build", "tractor plus no-recorded-tractor equals all build events"],
               "tractor_period_changes": [r for r in changes if r["group"] == "road_tractor"],
               "tractor_observed_total": sum(r["casualty_collisions"] for r in annual if r["group"] == "road_tractor" and r["subset"] == "observed"),
               "tractor_strict_total": sum(r["casualty_collisions"] for r in annual if r["group"] == "road_tractor" and r["subset"] == "strict"),
               "sampling_intervals": "Not computed: descriptive counts of this release; source and classification uncertainties remain", "model_fitted": False,
               "unresolved_limitations": ["No national event microdata for 2022–2025", "Residual source/definition differences are recorded in benchmark_comparison.csv; the old CSV source is preserved as a baseline", "Unknown vehicle types can conceal tractor involvement", "Strict exclusions are sensitivity only", "Person casualties require the separate casualty analysis; no compatible exposure denominator is applied here", "No causal attribution"], "benchmark_url": BENCHMARK_URL}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(output), "diagnostics": diagnostics, "tractor_events": summary["tractor_observed_total"], "tractor_strict_events": summary["tractor_strict_total"]}, indent=2))


if __name__ == "__main__":
    main()
