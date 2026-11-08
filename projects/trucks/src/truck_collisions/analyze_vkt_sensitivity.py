"""Bounded 2015-2021 model-normalized historical VKT sensitivity analysis.

Evaluates observed NCDB road-tractor casualty collision events and distinct
tractor vehicle involvements relative to Transport Canada's Table 10 modeled
tractor-trailer vehicle-kilometres (2015-2021).

IMPORTANT METHODOLOGICAL GATE:
Table 10 provides econometric forecasts for tractor-trailers >15,000 kg with
unresolved vehicle-weight, bobtail/attachment, territorial, and cross-border
travel boundaries relative to public NCDB V_TYPE='08' events. All computed
ratios are strictly MODEL-NORMALIZED HISTORICAL SENSITIVITIES relative to the
specified Table 10 series, NOT unqualified national semi-driving risk rates.

Run from projects/trucks:
  MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src .venv/bin/python -m truck_collisions.analyze_vkt_sensitivity
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import duckdb


OVERLAP_YEARS = tuple(range(2015, 2022))

NUMERATOR_SPECS = (
    (
        "primary_observed_events",
        "event",
        "Primary observed road-tractor casualty collision events (C_SEV in 1,2)",
    ),
    (
        "strict_candidate_events",
        "event",
        "Strict structural/tractor-type candidate events (is_analysis_candidate=true)",
    ),
    (
        "strict_zero_unknown_vtype_events",
        "event",
        "Strict events with zero unknown/other/unavailable vehicle types (is_analysis_candidate AND NOT has_unknown_vehicle_type)",
    ),
    (
        "published_tc_benchmark_events",
        "event",
        "Published Transport Canada Table 1 benchmark events (2019 has +2 injury events vs microdata)",
    ),
    (
        "observed_tractor_vehicle_involvements",
        "vehicle_involvement",
        "Distinct known road-tractor vehicle involvements (V_TYPE=08, V_ID 01-98) in observed events",
    ),
    (
        "strict_tractor_vehicle_involvements",
        "vehicle_involvement",
        "Distinct known road-tractor vehicle involvements (V_TYPE=08, V_ID 01-98) in strict candidate events",
    ),
)

POOLED_PERIODS = (
    ("2015_2017", (2015, 2016, 2017), "Early overlap window (2015–2017)"),
    ("2018_2019_pre_pandemic", (2018, 2019), "Pre-pandemic late window (2018–2019)"),
    ("2018_2018_excl_2019_pre_pandemic", (2018,), "Pre-pandemic late window excluding 2019 (2018 only)"),
    ("2018_2021_full_late", (2018, 2019, 2020, 2021), "Full late overlap window including pandemic (2018–2021)"),
    ("2018_2021_excl_2019", (2018, 2020, 2021), "Late overlap window excluding 2019 (2018, 2020, 2021)"),
    ("2020_2021_pandemic", (2020, 2021), "Pandemic overlap years (2020–2021)"),
    ("2015_2019_pre_pandemic_all", (2015, 2016, 2017, 2018, 2019), "Full pre-pandemic overlap (2015–2019)"),
    ("2015_2019_excl_2019", (2015, 2016, 2017, 2018), "Pre-pandemic overlap excluding 2019 (2015–2018)"),
    ("2015_2021_all_overlap", (2015, 2016, 2017, 2018, 2019, 2020, 2021), "Complete Table 10 overlap (2015–2021)"),
    ("2015_2021_excl_2019", (2015, 2016, 2017, 2018, 2020, 2021), "Complete overlap excluding 2019"),
)

COMPARISONS = (
    ("pooled_2015_2017_vs_2018_2019", "pooled", "2015_2017", "2018_2019_pre_pandemic", "Pre-pandemic pooled: 2015–2017 vs 2018–2019"),
    ("pooled_2015_2017_vs_2018_excl_2019", "pooled", "2015_2017", "2018_2018_excl_2019_pre_pandemic", "Pre-pandemic pooled excluding 2019: 2015–2017 vs 2018"),
    ("pooled_2015_2017_vs_2018_2021", "pooled", "2015_2017", "2018_2021_full_late", "Full-window pooled: 2015–2017 vs 2018–2021"),
    ("pooled_2015_2017_vs_2018_2021_excl_2019", "pooled", "2015_2017", "2018_2021_excl_2019", "Full-window pooled excluding 2019: 2015–2017 vs 2018,2020–2021"),
    ("endpoint_2015_vs_2019_pre_pandemic", "endpoint", "2015", "2019", "Pre-pandemic endpoint trend: 2015 vs 2019"),
    ("endpoint_2015_vs_2018_excl_2019", "endpoint", "2015", "2018", "Pre-pandemic endpoint trend excluding 2019: 2015 vs 2018"),
    ("endpoint_2015_vs_2021_full_overlap", "endpoint", "2015", "2021", "Full overlap endpoint trend: 2015 vs 2021"),
    ("endpoint_2019_vs_2020_pandemic_onset", "endpoint", "2019", "2020", "Pandemic onset single-year change: 2019 vs 2020"),
    ("endpoint_2020_vs_2021_pandemic_rebound", "endpoint", "2020", "2021", "Pandemic second-year change: 2020 vs 2021"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty rows to {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def compute_ratios(fatal_count: int, injury_count: int, total_count: int, vkt_billion: float, base_row: dict | None = None) -> dict:
    if fatal_count + injury_count != total_count:
        raise ValueError(f"Severity additivity violation: {fatal_count} + {injury_count} != {total_count}")
    if vkt_billion <= 0:
        raise ValueError(f"Non-positive VKT denominator: {vkt_billion}")
    total_rate = total_count / vkt_billion
    fatal_rate = fatal_count / vkt_billion
    injury_rate = injury_count / vkt_billion
    fatal_share_pct = 100.0 * fatal_count / total_count if total_count else 0.0
    out = {
        "fatal_events": fatal_count,
        "injury_events": injury_count,
        "total_casualty_events": total_count,
        "fatal_share_pct": fatal_share_pct,
        "events_per_billion_modeled_vkt": total_rate,
        "fatal_events_per_billion_modeled_vkt": fatal_rate,
        "injury_events_per_billion_modeled_vkt": injury_rate,
    }
    if base_row is not None:
        out["count_index_2015_100"] = 100.0 * total_count / base_row["total_casualty_events"]
        out["fatal_count_index_2015_100"] = 100.0 * fatal_count / base_row["fatal_events"]
        out["injury_count_index_2015_100"] = 100.0 * injury_count / base_row["injury_events"]
        out["modeled_vkt_index_2015_100"] = 100.0 * vkt_billion / base_row["modeled_vkt_billion_km"]
        out["events_per_billion_vkt_index_2015_100"] = 100.0 * total_rate / base_row["events_per_billion_modeled_vkt"]
        out["fatal_per_billion_vkt_index_2015_100"] = 100.0 * fatal_rate / base_row["fatal_events_per_billion_modeled_vkt"]
        out["injury_per_billion_vkt_index_2015_100"] = 100.0 * injury_rate / base_row["injury_events_per_billion_modeled_vkt"]
    return out


def load_exposure_candidates(root: Path) -> tuple[dict[int, dict], dict]:
    candidate_path = root / "data/reference/tractor_exposure_candidates.csv"
    metadata_path = root / "data/reference/tractor_exposure_candidates.metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if sha256(candidate_path) != metadata["candidate_csv_sha256"]:
        raise ValueError("Candidate CSV SHA256 does not match tractor_exposure_candidates.metadata.json")
    with candidate_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 7 or [int(r["year"]) for r in rows] != list(OVERLAP_YEARS):
        raise ValueError("Expected exact 2015-2021 candidate exposure coverage")
    by_year = {}
    for row in rows:
        year = int(row["year"])
        vkt_million = Decimal(row["vkt_million_km"])
        fig28_million = Decimal(metadata["figure_28_vkt_million_km_by_year"][str(year)])
        if fig28_million.quantize(Decimal("0.1")) != vkt_million:
            raise ValueError(f"Figure 28 rounding mismatch in year {year}")
        by_year[year] = {
            "series_id": row["series_id"],
            "year": year,
            "vehicle_class": row["vehicle_class"],
            "minimum_weight_kg": int(row["minimum_weight_kg"]),
            "weight_operator": row["weight_operator"],
            "modeled_vkt_million_km": float(vkt_million),
            "modeled_vkt_billion_km": float(vkt_million / Decimal("1000")),
            "figure28_vkt_billion_km": float(fig28_million / Decimal("1000")),
            "estimate_type": row["estimate_type"],
            "eligibility_status": row["eligibility_status"],
        }
    return by_year, metadata


def query_annual_numerators(root: Path) -> dict[tuple[str, int], tuple[int, int, int]]:
    events_path = root / "data/derived/ncdb/collisions.parquet"
    reconcil_path = root / "data/derived/ncdb/reconciliation.csv"
    con = duckdb.connect()
    sql = """
    SELECT
        C_YEAR AS year,
        count(*) FILTER (WHERE C_SEV = '1') AS obs_fatal,
        count(*) FILTER (WHERE C_SEV = '2') AS obs_injury,
        count(*) AS obs_total,
        count(*) FILTER (WHERE is_analysis_candidate AND C_SEV = '1') AS strict_fatal,
        count(*) FILTER (WHERE is_analysis_candidate AND C_SEV = '2') AS strict_injury,
        count(*) FILTER (WHERE is_analysis_candidate) AS strict_total,
        count(*) FILTER (WHERE is_analysis_candidate AND NOT has_unknown_vehicle_type AND C_SEV = '1') AS zero_unk_fatal,
        count(*) FILTER (WHERE is_analysis_candidate AND NOT has_unknown_vehicle_type AND C_SEV = '2') AS zero_unk_injury,
        count(*) FILTER (WHERE is_analysis_candidate AND NOT has_unknown_vehicle_type) AS zero_unk_total,
        sum(road_tractor_vehicle_count) FILTER (WHERE C_SEV = '1') AS inv_obs_fatal,
        sum(road_tractor_vehicle_count) FILTER (WHERE C_SEV = '2') AS inv_obs_injury,
        sum(road_tractor_vehicle_count) AS inv_obs_total,
        sum(road_tractor_vehicle_count) FILTER (WHERE is_analysis_candidate AND C_SEV = '1') AS inv_strict_fatal,
        sum(road_tractor_vehicle_count) FILTER (WHERE is_analysis_candidate AND C_SEV = '2') AS inv_strict_injury,
        sum(road_tractor_vehicle_count) FILTER (WHERE is_analysis_candidate) AS inv_strict_total
    FROM read_parquet(?)
    WHERE is_road_tractor AND C_YEAR BETWEEN 2015 AND 2021
    GROUP BY C_YEAR
    ORDER BY C_YEAR
    """
    rows = con.execute(sql, [str(events_path)]).fetchall()
    con.close()
    if len(rows) != 7:
        raise ValueError(f"Expected 7 annual rows from collisions.parquet, got {len(rows)}")
    out: dict[tuple[str, int], tuple[int, int, int]] = {}
    for (
        year,
        obs_f, obs_i, obs_t,
        str_f, str_i, str_t,
        zu_f, zu_i, zu_t,
        io_f, io_i, io_t,
        is_f, is_i, is_t,
    ) in rows:
        yr = int(year)
        out[("primary_observed_events", yr)] = (int(obs_f), int(obs_i), int(obs_t))
        out[("strict_candidate_events", yr)] = (int(str_f), int(str_i), int(str_t))
        out[("strict_zero_unknown_vtype_events", yr)] = (int(zu_f), int(zu_i), int(zu_t))
        out[("observed_tractor_vehicle_involvements", yr)] = (int(io_f), int(io_i), int(io_t))
        out[("strict_tractor_vehicle_involvements", yr)] = (int(is_f), int(is_i), int(is_t))

    with reconcil_path.open(encoding="utf-8", newline="") as handle:
        for r in csv.DictReader(handle):
            yr = int(r["year"])
            if yr in OVERLAP_YEARS:
                pf = int(r["published_fatal"])
                pi = int(r["published_injury"])
                out[("published_tc_benchmark_events", yr)] = (pf, pi, pf + pi)
    return out


def build_annual_table(exposure_by_year: dict[int, dict], numerators: dict[tuple[str, int], tuple[int, int, int]]) -> list[dict]:
    annual_rows: list[dict] = []
    for num_id, unit_type, description in NUMERATOR_SPECS:
        base_2015: dict | None = None
        for year in OVERLAP_YEARS:
            exp = exposure_by_year[year]
            fatal_c, injury_c, total_c = numerators[(num_id, year)]
            vkt_b = exp["modeled_vkt_billion_km"]
            fig28_vkt_b = exp["figure28_vkt_billion_km"]
            prelim = {
                "total_casualty_events": total_c,
                "fatal_events": fatal_c,
                "injury_events": injury_c,
                "modeled_vkt_billion_km": vkt_b,
                "events_per_billion_modeled_vkt": total_c / vkt_b,
                "fatal_events_per_billion_modeled_vkt": fatal_c / vkt_b,
                "injury_events_per_billion_modeled_vkt": injury_c / vkt_b,
            }
            if year == 2015:
                base_2015 = prelim
            metrics = compute_ratios(fatal_c, injury_c, total_c, vkt_b, base_2015)
            row = {
                "numerator_id": num_id,
                "counting_unit": unit_type,
                "numerator_description": description,
                "year": year,
                "is_2019_benchmark_gap_year": year == 2019,
                "is_pandemic_year": year in (2020, 2021),
                "modeled_vkt_million_km": exp["modeled_vkt_million_km"],
                "modeled_vkt_billion_km": vkt_b,
                "figure28_vkt_billion_km": fig28_vkt_b,
                **metrics,
                "events_per_billion_figure28_vkt": total_c / fig28_vkt_b,
                "table10_minus_figure28_rate_diff": (total_c / vkt_b) - (total_c / fig28_vkt_b),
                "denominator_series_id": exp["series_id"],
                "denominator_eligibility_status": exp["eligibility_status"],
                "interpretation_gate": "model_normalized_historical_sensitivity_only_not_national_driving_risk",
            }
            annual_rows.append(row)
    return annual_rows


def build_summary_table(annual_rows: list[dict]) -> list[dict]:
    by_key = {(r["numerator_id"], r["year"]): r for r in annual_rows}
    pooled_lookup: dict[tuple[str, str], dict] = {}
    summary_rows: list[dict] = []

    for num_id, unit_type, description in NUMERATOR_SPECS:
        base_2015 = by_key[(num_id, 2015)]
        for period_id, years, period_label in POOLED_PERIODS:
            sub = [by_key[(num_id, y)] for y in years]
            fatal_c = sum(r["fatal_events"] for r in sub)
            injury_c = sum(r["injury_events"] for r in sub)
            total_c = sum(r["total_casualty_events"] for r in sub)
            vkt_m = sum(r["modeled_vkt_million_km"] for r in sub)
            vkt_b = sum(r["modeled_vkt_billion_km"] for r in sub)
            metrics = compute_ratios(fatal_c, injury_c, total_c, vkt_b)
            pooled_row = {
                "record_type": "pooled_period",
                "numerator_id": num_id,
                "counting_unit": unit_type,
                "period_or_comparison_id": period_id,
                "label": period_label,
                "years_included": ";".join(map(str, years)),
                "year_count": len(years),
                "excludes_2019": 2019 not in years,
                "excludes_pandemic_2020_2021": all(y < 2020 for y in years),
                "start_or_early_period": period_id,
                "end_or_late_period": "",
                "fatal_events": fatal_c,
                "injury_events": injury_c,
                "total_casualty_events": total_c,
                "mean_annual_events": total_c / len(years),
                "modeled_vkt_million_km": vkt_m,
                "modeled_vkt_billion_km": vkt_b,
                "mean_annual_vkt_billion_km": vkt_b / len(years),
                "fatal_share_pct": metrics["fatal_share_pct"],
                "events_per_billion_modeled_vkt": metrics["events_per_billion_modeled_vkt"],
                "fatal_events_per_billion_modeled_vkt": metrics["fatal_events_per_billion_modeled_vkt"],
                "injury_events_per_billion_modeled_vkt": metrics["injury_events_per_billion_modeled_vkt"],
                "events_per_billion_vkt_index_2015_100": 100.0 * metrics["events_per_billion_modeled_vkt"] / base_2015["events_per_billion_modeled_vkt"],
                "fatal_per_billion_vkt_index_2015_100": 100.0 * metrics["fatal_events_per_billion_modeled_vkt"] / base_2015["fatal_events_per_billion_modeled_vkt"],
                "injury_per_billion_vkt_index_2015_100": 100.0 * metrics["injury_events_per_billion_modeled_vkt"] / base_2015["injury_events_per_billion_modeled_vkt"],
                "start_total_events": total_c,
                "end_total_events": None,
                "pct_change_total_events": None,
                "start_vkt_billion_km": vkt_b,
                "end_vkt_billion_km": None,
                "pct_change_vkt": None,
                "start_events_per_billion_vkt": metrics["events_per_billion_modeled_vkt"],
                "end_events_per_billion_vkt": None,
                "diff_events_per_billion_vkt": None,
                "pct_change_events_per_billion_vkt": None,
                "start_fatal_per_billion_vkt": metrics["fatal_events_per_billion_modeled_vkt"],
                "end_fatal_per_billion_vkt": None,
                "diff_fatal_per_billion_vkt": None,
                "pct_change_fatal_per_billion_vkt": None,
                "start_injury_per_billion_vkt": metrics["injury_events_per_billion_modeled_vkt"],
                "end_injury_per_billion_vkt": None,
                "diff_injury_per_billion_vkt": None,
                "pct_change_injury_per_billion_vkt": None,
                "start_fatal_share_pct": metrics["fatal_share_pct"],
                "end_fatal_share_pct": None,
                "change_fatal_share_pp": None,
                "interpretation_gate": "model_normalized_historical_sensitivity_only_not_national_driving_risk",
            }
            pooled_lookup[(num_id, period_id)] = pooled_row
            summary_rows.append(pooled_row)

        for comp_id, comp_kind, early_key, late_key, comp_label in COMPARISONS:
            if comp_kind == "pooled":
                early = pooled_lookup[(num_id, early_key)]
                late = pooled_lookup[(num_id, late_key)]
                years_str = f"{early['years_included']} vs {late['years_included']}"
                yr_cnt = early["year_count"] + late["year_count"]
                excl_2019 = early["excludes_2019"] and late["excludes_2019"]
                excl_pand = early["excludes_pandemic_2020_2021"] and late["excludes_pandemic_2020_2021"]
            else:
                y0, y1 = int(early_key), int(late_key)
                early = by_key[(num_id, y0)]
                late = by_key[(num_id, y1)]
                years_str = f"{y0} vs {y1}"
                yr_cnt = 2
                excl_2019 = (y0 != 2019 and y1 != 2019)
                excl_pand = (y0 < 2020 and y1 < 2020)

            r0_tot = early["events_per_billion_modeled_vkt"]
            r1_tot = late["events_per_billion_modeled_vkt"]
            r0_fat = early["fatal_events_per_billion_modeled_vkt"]
            r1_fat = late["fatal_events_per_billion_modeled_vkt"]
            r0_inj = early["injury_events_per_billion_modeled_vkt"]
            r1_inj = late["injury_events_per_billion_modeled_vkt"]

            comp_row = {
                "record_type": f"{comp_kind}_comparison",
                "numerator_id": num_id,
                "counting_unit": unit_type,
                "period_or_comparison_id": comp_id,
                "label": comp_label,
                "years_included": years_str,
                "year_count": yr_cnt,
                "excludes_2019": excl_2019,
                "excludes_pandemic_2020_2021": excl_pand,
                "start_or_early_period": early_key,
                "end_or_late_period": late_key,
                "fatal_events": late["fatal_events"] - early["fatal_events"],
                "injury_events": late["injury_events"] - early["injury_events"],
                "total_casualty_events": late["total_casualty_events"] - early["total_casualty_events"],
                "mean_annual_events": None,
                "modeled_vkt_million_km": late["modeled_vkt_million_km"] - early["modeled_vkt_million_km"],
                "modeled_vkt_billion_km": late["modeled_vkt_billion_km"] - early["modeled_vkt_billion_km"],
                "mean_annual_vkt_billion_km": None,
                "fatal_share_pct": late["fatal_share_pct"],
                "events_per_billion_modeled_vkt": r1_tot,
                "fatal_events_per_billion_modeled_vkt": r1_fat,
                "injury_events_per_billion_modeled_vkt": r1_inj,
                "events_per_billion_vkt_index_2015_100": 100.0 * r1_tot / base_2015["events_per_billion_modeled_vkt"],
                "fatal_per_billion_vkt_index_2015_100": 100.0 * r1_fat / base_2015["fatal_events_per_billion_modeled_vkt"],
                "injury_per_billion_vkt_index_2015_100": 100.0 * r1_inj / base_2015["injury_events_per_billion_modeled_vkt"],
                "start_total_events": early["total_casualty_events"],
                "end_total_events": late["total_casualty_events"],
                "pct_change_total_events": 100.0 * (late["total_casualty_events"] / early["total_casualty_events"] - 1.0),
                "start_vkt_billion_km": early["modeled_vkt_billion_km"],
                "end_vkt_billion_km": late["modeled_vkt_billion_km"],
                "pct_change_vkt": 100.0 * (late["modeled_vkt_billion_km"] / early["modeled_vkt_billion_km"] - 1.0),
                "start_events_per_billion_vkt": r0_tot,
                "end_events_per_billion_vkt": r1_tot,
                "diff_events_per_billion_vkt": r1_tot - r0_tot,
                "pct_change_events_per_billion_vkt": 100.0 * (r1_tot / r0_tot - 1.0),
                "start_fatal_per_billion_vkt": r0_fat,
                "end_fatal_per_billion_vkt": r1_fat,
                "diff_fatal_per_billion_vkt": r1_fat - r0_fat,
                "pct_change_fatal_per_billion_vkt": 100.0 * (r1_fat / r0_fat - 1.0),
                "start_injury_per_billion_vkt": r0_inj,
                "end_injury_per_billion_vkt": r1_inj,
                "diff_injury_per_billion_vkt": r1_inj - r0_inj,
                "pct_change_injury_per_billion_vkt": 100.0 * (r1_inj / r0_inj - 1.0),
                "start_fatal_share_pct": early["fatal_share_pct"],
                "end_fatal_share_pct": late["fatal_share_pct"],
                "change_fatal_share_pp": late["fatal_share_pct"] - early["fatal_share_pct"],
                "interpretation_gate": "model_normalized_historical_sensitivity_only_not_national_driving_risk",
            }
            summary_rows.append(comp_row)
    return summary_rows


def render_figure(annual_rows: list[dict], summary_rows: list[dict], fig_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 180,
    })

    by_num = {}
    for r in annual_rows:
        by_num.setdefault(r["numerator_id"], []).append(r)

    primary = by_num["primary_observed_events"]
    strict_zu = by_num["strict_zero_unknown_vtype_events"]
    involvements = by_num["observed_tractor_vehicle_involvements"]
    years = [r["year"] for r in primary]

    fig, axes = plt.subplots(1, 3, figsize=(16.2, 5.6))
    fig.suptitle(
        "Model-normalized road-tractor sensitivity relative to Table 10 modeled VKT (2015–2021)",
        fontsize=14.5,
        y=0.97,
        fontweight="bold",
    )

    # Panel A: Indexed trajectories (2015 = 100) showing numerator vs modeled denominator vs ratio
    ax = axes[0]
    ax.plot(years, [r["modeled_vkt_index_2015_100"] for r in primary], color="#5c6670", linestyle="--", marker="s", markersize=4, linewidth=1.8, label="Table 10 modeled VKT (34.2→45.6B km)")
    ax.plot(years, [r["count_index_2015_100"] for r in primary], color="#1f5b85", linestyle=":", marker="o", markersize=4, linewidth=1.6, label="Observed casualty events (3,075→2,276)")
    ax.plot(years, [r["events_per_billion_vkt_index_2015_100"] for r in primary], color="#1f5b85", linestyle="-", marker="o", markersize=5, linewidth=2.2, label="Casualty events / billion modeled VKT")
    ax.plot(years, [r["fatal_per_billion_vkt_index_2015_100"] for r in primary], color="#b8332a", linestyle="-", marker="^", markersize=5, linewidth=2.0, label="Fatal events / billion modeled VKT")
    ax.axhline(100, color="#888888", linewidth=0.8)
    ax.axvspan(2019.5, 2021.2, color="#f2e8dc", alpha=0.55, label="Pandemic window (2020–2021)")
    ax.set_title("A. Indexed trajectories (2015 = 100)", fontsize=11.5, fontweight="bold")
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Index (2015 = 100)")
    ax.set_xticks(years)
    ax.set_ylim(40, 145)
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8.3, loc="lower left")

    # Panel B: Absolute model-normalized ratios across numerator sensitivities
    ax = axes[1]
    ax.plot(years, [r["events_per_billion_modeled_vkt"] for r in primary], color="#1f5b85", marker="o", linewidth=2.1, label="Primary observed events (E / K̂)")
    ax.plot(years, [r["events_per_billion_modeled_vkt"] for r in strict_zu], color="#2a8c55", linestyle="--", marker="d", markersize=4, linewidth=1.7, label="Strict zero-unknown-V_TYPE events")
    ax.plot(years, [r["events_per_billion_modeled_vkt"] for r in involvements], color="#a86719", linestyle="-.", marker="s", markersize=4, linewidth=1.9, label="Tractor vehicle involvements (I / K̂)")
    ax.axvspan(2019.5, 2021.2, color="#f2e8dc", alpha=0.55)
    ax.set_title("B. Numerator & estimand sensitivities", fontsize=11.5, fontweight="bold")
    ax.set_xlabel("Calendar year")
    ax.set_ylabel("Units per billion Table 10 modeled VKT")
    ax.set_xticks(years)
    ax.set_ylim(0, 110)
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")

    # Panel C: Fatal vs Injury model-normalized rates across pooled windows
    ax = axes[2]
    pool_ids = [
        ("2015_2017", "2015–2017\n(Early)"),
        ("2018_2019_pre_pandemic", "2018–2019\n(Pre-pand.)"),
        ("2018_2018_excl_2019_pre_pandemic", "2018 only\n(Excl. 2019)"),
        ("2018_2021_full_late", "2018–2021\n(Full late)"),
        ("2018_2021_excl_2019", "2018,20–21\n(Excl. 2019)"),
    ]
    pool_map = {
        r["period_or_comparison_id"]: r
        for r in summary_rows
        if r["record_type"] == "pooled_period" and r["numerator_id"] == "primary_observed_events"
    }
    x = list(range(len(pool_ids)))
    fatal_rates = [pool_map[pid]["fatal_events_per_billion_modeled_vkt"] for pid, _ in pool_ids]
    tot_rates = [pool_map[pid]["events_per_billion_modeled_vkt"] for pid, _ in pool_ids]
    bars = ax.bar([i - 0.18 for i in x], tot_rates, width=0.34, color="#1f5b85", label="All casualty events / B VKT")
    ax2 = ax.twinx()
    ax2.spines["top"].set_visible(False)
    bars_f = ax2.bar([i + 0.18 for i in x], fatal_rates, width=0.34, color="#b8332a", alpha=0.88, label="Fatal events / B VKT (right axis)")
    for b, val in zip(bars, tot_rates):
        ax.text(b.get_x() + b.get_width() / 2, val + 1.5, f"{val:.1f}", ha="center", va="bottom", fontsize=8, color="#1f5b85")
    for b, val in zip(bars_f, fatal_rates):
        ax2.text(b.get_x() + b.get_width() / 2, val + 0.12, f"{val:.2f}", ha="center", va="bottom", fontsize=8, color="#b8332a")
    ax.set_xticks(x, [lbl for _, lbl in pool_ids], fontsize=8.5)
    ax.set_ylim(0, 105)
    ax2.set_ylim(0, 7.5)
    ax.set_ylabel("Casualty events per billion modeled VKT", color="#1f5b85")
    ax2.set_ylabel("Fatal events per billion modeled VKT", color="#b8332a")
    ax.set_title("C. Pooled period sensitivity (observed events)", fontsize=11.5, fontweight="bold")
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.7)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8.2, loc="upper right")

    note = (
        "Methodological note: Table 10 VKT is an econometric forecast for tractor-trailers >15,000 kg (34.20B km in 2015 to 45.59B km in 2021, +33.3%), whereas NCDB V_TYPE='08' covers road tractors\n"
        "with or without semitrailers on public roads without a weight filter. Ratios are model-normalized historical sensitivities relative to Table 10, not validated national semi-driving risk rates."
    )
    fig.text(0.02, 0.015, note, fontsize=8.5, color="#333333", va="bottom")
    fig.subplots_adjust(left=0.05, right=0.95, top=0.84, bottom=0.20, wspace=0.28)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, facecolor="white")
    plt.close(fig)


def run_analysis(root: Path) -> dict:
    root = Path(root).resolve()
    exposure_by_year, metadata = load_exposure_candidates(root)
    numerators = query_annual_numerators(root)
    annual_rows = build_annual_table(exposure_by_year, numerators)
    summary_rows = build_summary_table(annual_rows)

    tables_dir = root / "reports/tables"
    figures_dir = root / "reports/figures"
    annual_csv = tables_dir / "vkt_sensitivity_annual.csv"
    summary_csv = tables_dir / "vkt_sensitivity_summary.csv"
    figure_png = figures_dir / "vkt_model_normalized_sensitivity.png"

    write_csv(annual_csv, annual_rows)
    write_csv(summary_csv, summary_rows)
    render_figure(annual_rows, summary_rows, figure_png)

    summary_payload = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis": "bounded_2015_2021_model_normalized_vkt_sensitivity",
        "overlap_years": list(OVERLAP_YEARS),
        "decision_gate": "model_normalized_historical_sensitivity_only_not_approved_as_primary_national_risk_rate",
        "annual_rows": len(annual_rows),
        "summary_rows": len(summary_rows),
        "outputs": {
            "annual_csv": str(annual_csv.relative_to(root)),
            "summary_csv": str(summary_csv.relative_to(root)),
            "figure_png": str(figure_png.relative_to(root)),
        },
        "inputs_sha256": {
            "data/derived/ncdb/collisions.parquet": sha256(root / "data/derived/ncdb/collisions.parquet"),
            "data/derived/ncdb/reconciliation.csv": sha256(root / "data/derived/ncdb/reconciliation.csv"),
            "data/reference/tractor_exposure_candidates.csv": sha256(root / "data/reference/tractor_exposure_candidates.csv"),
            "data/reference/tractor_exposure_candidates.metadata.json": sha256(root / "data/reference/tractor_exposure_candidates.metadata.json"),
        },
        "code_sha256": sha256(Path(__file__)),
    }
    return summary_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = run_analysis(args.root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
