"""Build the technical portfolio from reviewed aggregate evidence and saved experiments."""
import argparse
import base64
from html import escape
import json
from pathlib import Path

from matplotlib import pyplot as plt
import nbformat
from nbclient import NotebookClient
import pandas as pd

from run import ROOT, OUTPUT, TABLES, digest

HERE = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
REFERENCE = ROOT / "data/reference"
DELIVERY = REPORTS / "portfolio"
TC = "https://tc.canada.ca/en/road-transportation/statistics-data/canadian-motor-vehicle-traffic-collision-statistics/2024/canadian-motor-vehicle-traffic-collision-statistics-2024"
NCDB = "https://open.canada.ca/data/en/dataset/1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a"
STATCAN = "https://www150.statcan.gc.ca/n1/pub/92-160-g/92-160-g2021002-eng.htm"
NAMES = {"prevalence": "Training prevalence", "logistic": "Logistic regression"}
FIELDS = {"C_RALN": "Road alignment", "C_RCFG": "Road configuration", "C_RSUR": "Road surface",
          "C_TRAF": "Traffic control", "C_WTHR": "Weather", "C_MNTH": "Month", "C_WDAY": "Weekday",
          "C_HOUR": "Hour"}
NOTES = ("Ontario and Alberta figures are preliminary. New Brunswick figures are estimated. "
         "A Manitoba reporting change captured more minor injuries. Newfoundland and Labrador reflects "
         "reports processed by June 1, 2025. Rates in small populations can fluctuate sharply. "
         "Vehicle-kilometre estimates and resident-based rates answer different questions.")


def read_csv(path):
    return pd.read_csv(path)


def rows(data):
    return json.loads(data.to_json(orient="records", double_precision=15))


def collect(draft):
    geography_path = REFERENCE / "geography/jurisdictions_2024.json"
    geography = json.loads(geography_path.read_text())
    rates = read_csv(REFERENCE / "aggregate_jurisdiction_rates_2024.csv").set_index("location")
    assert digest(REFERENCE / "aggregate_jurisdiction_rates_2024.csv") == geography["rates_sha256"]
    assert len(geography["jurisdictions"]) == 13
    assert len({row["pruid"] for row in geography["jurisdictions"]}) == 13
    assert geography["canada"] == rates.loc["Canada"].drop("year").to_dict()
    for jurisdiction in geography["jurisdictions"]:
        assert jurisdiction["rates"] == rates.loc[jurisdiction["location"]].drop("year").to_dict()

    tables = REPORTS / "tables"
    annual = read_csv(REFERENCE / "aggregate_national_annual_2024_vintage.csv")
    assert annual.year.tolist() == list(range(2005, 2025))
    temporal = {}
    for key, codes in (("month", ["code"]), ("weekday_hour", ["weekday_code", "hour_code"])):
        columns = [*codes, "collisions", "fatal_collisions"]
        if key == "month":
            columns += ["label"]
        pooled = read_csv(tables / f"eda_temporal_{key}.csv")[columns]
        yearly = read_csv(tables / f"eda_temporal_{key}_by_year.csv")[["C_YEAR", *columns]]
        assert pooled.collisions.sum() == yearly.collisions.sum() == 2949846
        assert pooled.fatal_collisions.sum() == yearly.fatal_collisions.sum() == 47793
        temporal[key] = {"all": rows(pooled), "by_year": rows(yearly)}
    condition_columns = ["field", "label", "value_class", "collisions", "fatal_collisions",
                         "sparse_n_lt_100_or_fatal_lt_5"]
    conditions = read_csv(tables / "eda_condition_pooled.csv")[condition_columns]
    by_year = read_csv(tables / "eda_condition_by_year.csv")[["year", *condition_columns]]
    assert conditions.groupby("field").collisions.sum().eq(2949846).all()
    assert conditions.groupby("field").fatal_collisions.sum().eq(47793).all()

    evidence = {"annual": rows(annual), "temporal": temporal, "conditions": rows(conditions),
                "conditions_by_year": rows(by_year), "geography": geography, "rate_notes": NOTES,
                "policies": json.loads((REFERENCE / "policy_sources.json").read_text())["recommendations"],
                "model": None}
    if draft:
        return evidence

    receipt = json.loads((OUTPUT / "validation.json").read_text())
    assert receipt["status"] == "passed" and receipt["tree_fits"] == 120
    for relative, expected in receipt["artifact_sha256"].items():
        assert digest(ROOT / relative) == expected, relative
    selection = json.loads((OUTPUT / "selection.json").read_text())
    for family, label in (("rf", "Random Forest"), ("lgbm", "LightGBM")):
        NAMES[selection["development"][family]["configuration"]] = label
    stress = read_csv(TABLES / "stress_metrics.csv")
    development = read_csv(TABLES / "development_metrics.csv")
    importance = read_csv(TABLES / "permutation_importance.csv")
    summary = importance.groupby(["model", "feature"]).delta_log_loss.mean().reset_index()
    evidence["model"] = {"selection": selection, "stress": rows(stress[stress.group.eq("all")]),
                         "development": rows(development), "importance": rows(summary), "names": NAMES,
                         "validation": receipt}
    return evidence


def embedded_image(name, alt):
    data = base64.b64encode((FIGURES / name).read_bytes()).decode()
    return f'<img alt="{escape(alt)}" src="data:image/png;base64,{data}">'


def html_table(headers, records, caption=""):
    head = "".join(f'<th scope="col">{escape(str(item))}</th>' for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(str(item))}</td>" for item in record) + "</tr>"
                   for record in records)
    return f'<div class="table-scroll"><table><caption>{escape(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def model_panel(evidence):
    model = evidence["model"]
    if model is None:
        return '<p class="note">Technical preview. The expanded tree comparison is running. This report will include its results after validation.</p>'
    record = []
    for row in model["stress"]:
        record.append([model["names"][row["model"]], row["period"], f'{row["log_loss"]:.6f}',
                       f'{row["brier_score"]:.6f}', f'{row["average_precision"]:.2%}',
                       f'{row["roc_auc"]:.3f}', f'{row["mean_prediction"]:.2%}',
                       f'{row["precision"]:.2%}', f'{row["recall"]:.2%}', f'{row["f1"]:.3f}',
                       f'{row["flagged_fraction"]:.2%}'])
    selected = model["selection"]["development"]
    lines = []
    for family in ("rf", "lgbm"):
        row = selected[family]
        result = "met" if row["passes_development_gate"] else "fell short of"
        lines.append(f'<p><strong>{model["names"][row["configuration"]]}.</strong> Configuration '
                     f'{row["configuration"]} {result} the development improvement rule. '
                     f'Its log loss improved in {row["annual_log_loss_wins"]} of six years versus logistic regression.</p>')
    table = html_table(["Model", "Period", "Log loss", "Brier", "Avg. precision", "ROC-AUC",
                        "Mean prediction", "Precision", "Recall", "F1", "Flagged"], record,
                       "Retrospective evaluation. Pooled observed fatal share 1.97%.")
    contribution = html_table(
        ["Model", "Feature", "Mean increase in log loss"],
        [[model["names"][row["model"]], FIELDS[row["feature"]], f'{row["delta_log_loss"]:+.6f}']
         for row in sorted(model["importance"], key=lambda row: (row["model"], -row["delta_log_loss"]))],
        "Five seeded permutations per field and development year, averaged across 2014–2019")
    return ("".join(lines) + table + embedded_image("tree_comparison_reliability.png",
             "Model reliability on the reused 2020 and 2021 period")
            + '<details><summary>Predictive contribution of each field</summary>'
            + '<p>Permuting a field breaks its relationship with the outcome and other predictors. '
            'Changes in log loss show reliance within this model and evaluation period. Correlated fields can share contribution.</p>'
            + contribution + '</details>')


def make_figures(evidence):
    annual = pd.DataFrame(evidence["annual"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained")
    axes[0].plot(annual.year, annual.fatalities, color="#15776b", linewidth=2.4)
    axes[1].plot(annual.year, annual.total_injuries, color="#15776b", linewidth=2.4)
    for ax, title in zip(axes, ["People killed", "People injured"]):
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xticks([2005, 2010, 2015, 2020, 2024])
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=.22)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("National road casualties · Transport Canada 2024 publication", fontweight="bold")
    fig.savefig(FIGURES / "portfolio_national_trend.png", dpi=170, facecolor="white")
    plt.close(fig)
    if evidence["model"] is None:
        return
    calibration = read_csv(TABLES / "stress_calibration.csv")
    calibration = calibration[calibration.period.eq("pooled") & calibration.n.gt(0)]
    fig, ax = plt.subplots(figsize=(8.1, 4.8), layout="constrained")
    peak = max(calibration.mean_prediction.max(), calibration.observed.max(), .05)
    ax.plot([0, peak], [0, peak], color="#778084", linestyle="--", label="Perfect agreement")
    for name, group in calibration.groupby("model"):
        supported = group[group.n.ge(100) & group.fatal.ge(5)]
        sparse = group.drop(supported.index)
        line, = ax.plot(supported.mean_prediction, supported.observed, marker="o", linewidth=1.4,
                        label=NAMES[name])
        ax.scatter(sparse.mean_prediction, sparse.observed, color=line.get_color(), marker="x", alpha=.6)
    ax.set(xlabel="Mean predicted fatal share", ylabel="Observed fatal share",
           title="Probability reliability in 2020–2021 · crosses indicate sparse bins")
    ax.legend(frameon=False)
    fig.savefig(FIGURES / "tree_comparison_reliability.png", dpi=170, facecolor="white")
    plt.close(fig)


STYLE = """
:root{color:#172f32;background:#f9f8f2;font-family:system-ui,sans-serif;line-height:1.55;--ink:#172f32;--accent:#146f64;--muted:#526663}
*{box-sizing:border-box}body{margin:0}a{color:#0a625a;text-underline-offset:.2em}main{max-width:1120px;margin:auto;padding:0 clamp(18px,5vw,65px) 60px}
header{background:#153a38;color:#f9f8f2;padding:clamp(35px,8vw,105px) max(6vw,calc((100vw - 990px)/2));border-bottom:5px solid #79bcad}
header a{color:#e3f7f0}h1,h2{font-family:Georgia,serif;font-weight:normal;line-height:1.06}
h1{font-size:clamp(3.1rem,8vw,7rem);margin:14px 0;letter-spacing:-.055em}h2{font-size:clamp(2rem,4vw,3.35rem);letter-spacing:-.045em;margin:0 0 16px}
h3{font-size:1.2rem;margin:24px 0 8px}p{max-width:76ch;margin:10px 0 16px}header p{font-size:1.15rem;max-width:62ch}
.kicker{font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;font-weight:750}
nav{display:flex;flex-wrap:wrap;gap:16px;padding:18px 0;border-bottom:1px solid #bdcbc5}
section{padding:clamp(28px,5vw,64px) 0;border-bottom:1px solid #bdcbc5;scroll-margin-top:12px}
section .kicker{color:var(--accent)}img{display:block;max-width:100%;height:auto;margin:20px auto}
figure{margin:0}figcaption,.note{color:var(--muted);font-size:.91rem;max-width:88ch}.note{border-left:3px solid #79bcad;padding-left:14px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:.89rem}
th,td{text-align:left;border-bottom:1px solid #d5dfd9;padding:9px 11px;vertical-align:top}
thead{background:#e7eee8}caption{text-align:left;color:var(--muted);padding:9px 0}
.table-scroll{overflow-x:auto;margin:16px 0}details{margin:16px 0}summary{cursor:pointer;font-weight:650;color:var(--accent)}
:focus-visible{outline:3px solid #b16a2e;outline-offset:4px}select,input{font:inherit}select{background:white;color:var(--ink);border:1px solid #879e96;padding:6px 8px;border-radius:4px}
"""


def page(title, subtitle, content, style="", script="", hero=""):
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{escape(title)}</title>'
            f'<style>{STYLE}{style}</style><body><header>{hero}<div class="kicker">Canada · Traffic accident analysis</div>'
            f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></header><main>{content}</main>{script}</body></html>')


def evidence_download(path, label):
    encoded = base64.b64encode(path.read_bytes()).decode()
    return (f'<a download="{escape(path.name)}" href="data:text/csv;base64,{encoded}">'
            f'{escape(label)}</a>')


def technical(evidence):
    findings = evidence["annual"][-1]
    rates = evidence["geography"]
    policy = "".join(
        f'<h3>{index:02} · {escape(rec["title"])}</h3><p>{escape(rec["observation"])} '
        f'{escape(rec["evidence"])}</p><p>{escape(rec["action"])} {escape(rec["evaluation"])} '
        f'<a href="{rec["url"]}">{escape(rec["source_label"])}</a></p>'
        for index, rec in enumerate(evidence["policies"], 1))
    rate_rows = [[r["location"], r["rates"]["fatalities_per_100k_population"],
                  r["rates"]["injuries_per_100k_population"]] for r in rates["jurisdictions"]]
    rate_rows.append(["Canada", rates["canada"]["fatalities_per_100k_population"],
                      rates["canada"]["injuries_per_100k_population"]])
    downloads = [
        evidence_download(REFERENCE / "aggregate_national_annual_2024_vintage.csv", "National publication series CSV"),
        evidence_download(REFERENCE / "aggregate_jurisdiction_rates_2024.csv", "Jurisdiction rates CSV"),
        evidence_download(REPORTS / "tables/eda_temporal_weekday_hour.csv", "Weekday and hour CSV"),
    ]
    if evidence["model"]:
        downloads += [
            evidence_download(TABLES / "development_grid.csv", "Development comparison CSV"),
            evidence_download(TABLES / "stress_metrics.csv", "Retrospective model metrics CSV"),
        ]
    model_title = "A retrospective comparison of collision severity"
    return page("Road to Safety", "Technical portfolio · Canadian collision patterns, severity and geographic context",
        f"""
<nav aria-label="Report sections"><a href="#timing">Timing</a><a href="#conditions">Conditions</a>
<a href="#geography">Geography</a><a href="#models">Models</a><a href="#policy">Policy</a><a href="#methods">Methods</a></nav>
<section><div class="kicker">Executive summary</div><h2>Collision burden and fatal share peak at different times</h2>
<p>The archived cohort contains 2,949,846 fatal and nonfatal injury collisions from 1999–2021. The fatal share is 1.62%.
Friday accounts for the most reported collisions with a known weekday. Sunday has the highest fatal share.
Transport Canada separately reports {findings['fatalities']:,} people killed and {findings['total_injuries']:,} injured in 2024.</p>
<p>The geographic comparison shows the 2024 national fatality rate of 4.9 per 100,000 residents alongside published jurisdiction rates.
Different reporting practices and small populations matter when interpreting the comparison.</p></section>
<section id="timing"><div class="kicker">01 · Timing</div><h2>Late afternoon accounts for the largest volume</h2>
<p>The 16:00 hour had the most recorded collisions. The fatal share was highest at 02:00 among known hours.
The weekday and hour matrix counts both fatal and nonfatal injury collisions. Cells describe recorded events and their outcomes.</p>
{embedded_image('temporal_weekday_hour.png','Weekday and hour heatmaps of collision counts and fatal shares')}
<p class="note">Records with an unknown weekday or hour are retained in the evidence tables. The heatmap covers 2,918,220 collisions with both fields stated.</p>
{embedded_image('portfolio_national_trend.png','Transport Canada annual fatalities and injuries from 2005 to 2024')}
<p>Published annual casualty totals count people. Their data vintage and counting scope differ from the archived collision cohort.</p></section>
<section id="conditions"><div class="kicker">02 · Road conditions</div><h2>Alignment is associated with fatal severity</h2>
<p>Curves with gradients have a fatal share of 3.45% among 131,584 reported collisions. The share is 1.33% among
2,063,954 on straight and level roads. Road design, speed, exposure and case mix can affect the comparison.</p>
{embedded_image('conditions_c_raln.png','Reported fatal share and collision counts by road alignment')}
<details><summary>All recorded condition categories</summary>
{html_table(['Field','Category','Reported collisions','Fatal collisions','Fatal share','Category status'],
[[FIELDS[r['field']],r['label'],f"{r['collisions']:,}",f"{r['fatal_collisions']:,}",f"{r['fatal_collisions']/r['collisions']:.2%}",r['value_class']]
 for r in evidence['conditions'] if r['collisions']], '1999–2021 selected fatal and injury collision releases')}
</details></section>
<section id="geography"><div class="kicker">03 · Geography</div><h2>Published casualty rates vary by jurisdiction</h2>
{embedded_image('geography_map_2024.png','Choropleth of 2024 road fatalities per 100,000 residents across Canada')}
{embedded_image('geography_comparison_2024.png','Companion chart with all thirteen jurisdiction rates and the Canadian benchmark')}
<p class="note">{escape(NOTES)} Boundaries are 2021 Statistics Canada cartographic geography.</p>
<details><summary>View jurisdiction rates</summary>{html_table(['Jurisdiction','Fatalities per 100,000 residents','Injuries per 100,000 residents'], rate_rows)}</details></section>
<section id="models"><div class="kicker">04 · Modeling</div><h2>{model_title}</h2>
<p>These models estimate the conditional fatal share for recorded collisions with injury or death. Development compares the same
eight categorical features and six annual evaluations. The 2020–2021 outcomes were previously examined.
The original sigmoid calibration correction worsened probability scores in both years.</p>
{model_panel(evidence)}
<p class="note">The inputs are recorded in post-crash reports. A prospective decision system would need verified input availability and independent temporal evaluation.</p></section>
<section id="policy"><div class="kicker">05 · Policy</div><h2>Evaluate local interventions against measured exposure</h2>{policy}</section>
<section id="methods"><div class="kicker">06 · Evidence</div><h2>Coverage and reproducibility</h2>
<p>Event keys are unique within their selected source and year. The cohort excludes property-damage-only crashes.
The released records lack geographic identifiers, full dates and travel exposure. Severity comparisons are descriptive.
Jurisdiction rates come from the 2024 publication. The Statistics Canada geometry is simplified for display.</p>
<p>The project repository contains the methods, notebooks and validated run artifacts. Use the evidence downloads to inspect the exact values displayed here.</p>
<p>{' · '.join(downloads)}</p>
<p><a href="{NCDB}">NCDB public records and dictionary</a> · <a href="{TC}">Transport Canada collision statistics</a> ·
<a href="{STATCAN}">Statistics Canada boundary guide</a></p></section>""")


def execute_notebooks():
    notebook_dir = ROOT / "notebooks"
    summary = [
        nbformat.v4.new_markdown_cell("# Road to Safety\n\nTechnical synthesis of reviewed national, geographic and model evidence."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport pandas as pd\nfrom IPython.display import Image, display\n"
            "root = Path.cwd()\nref = root / 'data/reference'\ntables = root / 'reports/tables'\n"
            "annual = pd.read_csv(tables / 'eda_temporal_annual.csv')\n"
            "assert (annual.collisions.sum(), annual.fatal_collisions.sum()) == (2949846, 47793)\n"
            "display(annual[['C_YEAR', 'collisions', 'fatal_collisions']])"),
        nbformat.v4.new_code_cell(
            "national = pd.read_csv(ref / 'aggregate_national_annual_2024_vintage.csv')\n"
            "rates = pd.read_csv(ref / 'aggregate_jurisdiction_rates_2024.csv')\n"
            "assert len(rates) == 14 and national.year.tolist() == list(range(2005, 2025))\n"
            "display(national.tail(), rates[['location', 'fatalities_per_100k_population']])\n"
            "for name in ['temporal_weekday_hour.png', 'geography_map_2024.png', 'geography_comparison_2024.png']:\n"
            "    display(Image(filename=str(root / 'reports/figures' / name)))"),
        nbformat.v4.new_code_cell(
            "stress = pd.read_csv(tables / 'tree_comparison_v1/stress_metrics.csv')\n"
            "display(stress.loc[stress.group.eq('all'), ['model', 'period', 'n', 'fatal', 'log_loss', 'brier_score', 'precision', 'recall']])"),
    ]
    comparison = [
        nbformat.v4.new_markdown_cell("# Tree comparison v1\n\nSix chronological development evaluations and a reused 2020–2021 stress period."),
        nbformat.v4.new_code_cell(
            "from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import Image, display\n"
            "root = Path.cwd()\nrun = root / 'data/derived/tree_comparison_v1'\ntables = root / 'reports/tables/tree_comparison_v1'\n"
            "receipt = json.loads((run / 'validation.json').read_text())\n"
            "assert receipt['status'] == 'passed' and receipt['tree_fits'] == 120\n"
            "selection = json.loads((run / 'selection.json').read_text())\nselection"),
        nbformat.v4.new_code_cell(
            "grid = pd.read_csv(tables / 'development_grid.csv')\nassert len(grid) == 132\n"
            "display(grid.groupby('configuration')[['log_loss', 'brier_score']].mean().sort_values('log_loss'))\n"
            "stress = pd.read_csv(tables / 'stress_metrics.csv')\ndisplay(stress[stress.group.eq('all')])"),
        nbformat.v4.new_code_cell(
            "importance = pd.read_csv(tables / 'permutation_importance.csv')\n"
            "display(importance.groupby(['model','feature']).delta_log_loss.mean().unstack())\n"
            "display(Image(filename=str(root / 'reports/figures/tree_comparison_reliability.png')))"),
    ]
    for name, cells in [("07_tree_comparison_v1.ipynb", comparison), ("08_portfolio_synthesis.ipynb", summary)]:
        notebook = nbformat.v4.new_notebook(cells=cells)
        NotebookClient(notebook, timeout=120, kernel_name="python3",
                       resources={"metadata": {"path": str(ROOT)}}).execute()
        nbformat.validate(notebook)
        nbformat.write(notebook, notebook_dir / name)


def write_model_card(evidence):
    model = evidence["model"]
    selection = model["selection"]["development"]
    lines = [
        "# Tree comparison v1 model card",
        "",
        "The target is fatal versus nonfatal injury among the selected 1999–2021 NCDB casualty collisions.",
        "Use these scores to study retrospective severity patterns. Prospective use would require time-verified predictors, "
        "a new evaluation period and a decision-specific cost and calibration study.",
        "",
        "## Design and selection",
        "",
        "The four methods use matching chronological populations. Six development folds evaluate 2014–2019. "
        "Each fit uses only prior years. The probability inputs are eight dictionary-coded timing and road-condition fields.",
        "The 2019 models were fitted through 2018. Thresholds use 2019 and maximize precision subject to 80% recall.",
        "The reused 2020–2021 period was scored after freezing the selection and thresholds.",
        "",
        "| Family | Configuration | Annual log loss wins vs logistic | Development gate |",
        "| --- | --- | ---: | --- |",
    ]
    for result in selection.values():
        key = result["configuration"]
        lines.append(f'| {model["names"][key]} | {key} | {result["annual_log_loss_wins"]} | '
                     f'{"Met" if result["passes_development_gate"] else "Fell short"} |')
    lines += ["", "## Reused stress period", "",
              "| Model | Log loss | Brier | Average precision | Fatal recall | Precision | Flagged |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in model["stress"]:
        if row["period"] == "pooled":
            lines.append(f'| {model["names"][row["model"]]} | {row["log_loss"]:.6f} | '
                         f'{row["brier_score"]:.6f} | {row["average_precision"]:.2%} | '
                         f'{row["recall"]:.2%} | {row["precision"]:.2%} | {row["flagged_fraction"]:.2%} |')
    lines += ["", "## Scope and reproducibility", "",
              "The records lack geographic identifiers and travel exposure. The outcome covers recorded casualty collisions. "
              "The inputs were recorded after crashes. Sparse groups and previously examined years limit generalization.",
              "Permutation importance measures changes in predictive loss within the fitted models. "
              "Correlation and input availability affect interpretation.",
              "",
              "See the [experiment instructions](../experiments/tree_comparison_v1/README.md) and "
              "[reviewed technical report](../reports/portfolio/technical-report.html).", ""]
    (ROOT / "models/tree_comparison_v1_card.md").write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    evidence = collect(args.draft)
    DELIVERY.mkdir(exist_ok=True)
    make_figures(evidence)
    target = DELIVERY / ("technical-preview.html" if args.draft else "technical-report.html")
    target.write_text(technical(evidence))
    if not args.draft:
        execute_notebooks()
        write_model_card(evidence)
    print(target)


if __name__ == "__main__":
    main()
