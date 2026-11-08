"""Cross-link national NCDB bicycle collision findings with Toronto Centreline + AADT corridor exposure rates."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys

import duckdb

from .build import EVENT_KEY

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROAD_TO_SAFETY_ROOT = PROJECT_ROOT.parent / "road_to_safety"

MAIN_ROAD_CLASSES = [
    "Major Arterial",
    "Minor Arterial",
    "Collector",
    "Local",
    "Expressway Ramp",
    "Expressway",
]


def _ensure_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")
    try:
        import matplotlib
    except ModuleNotFoundError:
        conda_site = "/Applications/miniconda3/lib/python3.13/site-packages"
        if Path(conda_site).exists() and conda_site not in sys.path:
            sys.path.append(conda_site)
        import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def compute_national_co_involved_lethality(root: Path) -> list[dict]:
    """Compute national 2010-2021 bicycle collision counts, shares, and fatality rates by co-involved vehicle type."""
    db_path = root / "data/derived/build.duckdb"
    con = duckdb.connect(str(db_path), read_only=True)
    total_collisions, total_fatal = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE C_SEV='1') FROM collisions"
    ).fetchone()

    groups = [
        ("Light-duty vehicle", "V_TYPE='01'"),
        ("Cargo or other light truck/van", "V_TYPE IN ('05','06')"),
        ("Heavy unit truck", "V_TYPE='07'"),
        ("Road tractor", "V_TYPE='08'"),
        ("Heavy freight combined (truck or tractor)", "V_TYPE IN ('07','08')"),
        ("Bus", "V_TYPE IN ('09','10','11')"),
        ("Motorcycle or moped", "V_TYPE='14'"),
        ("Other classified non-bicycle vehicle", "V_TYPE IN ('16','18','19','20','21','22','23')"),
        ("Unknown, other or conflicting vehicle type", "V_TYPE IS NULL OR V_TYPE IN ('UU','QQ','XX')"),
    ]

    ldv_fatal_rate = None
    raw_rows = []
    for label, predicate in groups:
        q = f"""
        SELECT
            count(DISTINCT ({EVENT_KEY})) AS collisions,
            count(DISTINCT ({EVENT_KEY})) FILTER (WHERE c.C_SEV='1') AS fatal_collisions,
            count(DISTINCT ({EVENT_KEY})) FILTER (WHERE c.C_SEV='2') AS injury_collisions
        FROM vehicles v
        JOIN collisions c USING (source_id, C_YEAR, C_CASE)
        WHERE {predicate}
        """
        collisions, fatal_collisions, injury_collisions = con.execute(q).fetchone()
        fatal_rate_pct = (100.0 * fatal_collisions / collisions) if collisions else 0.0
        if label == "Light-duty vehicle":
            ldv_fatal_rate = fatal_rate_pct
        raw_rows.append(
            {
                "vehicle_group": label,
                "collisions": int(collisions),
                "fatal_collisions": int(fatal_collisions),
                "injury_collisions": int(injury_collisions),
                "share_of_all_bicycle_collisions_pct": round(100.0 * collisions / total_collisions, 2),
                "share_of_fatal_bicycle_collisions_pct": round(100.0 * fatal_collisions / total_fatal, 2),
                "fatality_rate_pct": round(fatal_rate_pct, 3),
            }
        )
    con.close()

    for r in raw_rows:
        r["lethality_multiplier_vs_light_duty"] = (
            round(r["fatality_rate_pct"] / ldv_fatal_rate, 2) if ldv_fatal_rate else None
        )
    return raw_rows


def compute_toronto_cyclist_exposure(
    parquet_path: Path,
    pilot_class_csv: Path,
) -> tuple[list[dict], list[dict]]:
    """Compute road-class and corridor-level cyclist KSI rates per 100M VKT and per km from Toronto Centreline + AADT."""
    pilot_class_map = {
        r["road_class"]: r for r in _read_csv(pilot_class_csv)
    }

    con = duckdb.connect()
    p_str = parquet_path.as_posix()

    class_query = f"""
    SELECT
        FEATURE_CODE_DESC AS road_class,
        count(*) FILTER (WHERE has_aadt) AS monitored_segments,
        round(sum(length_km) FILTER (WHERE has_aadt), 3) AS monitored_length_km,
        round(avg(aadt) FILTER (WHERE has_aadt), 1) AS mean_aadt,
        round(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 4) AS cumulative_100m_vkt_18y,
        sum(ksi_crashes) FILTER (WHERE has_aadt) AS ksi_crashes,
        sum(fatal_crashes) FILTER (WHERE has_aadt) AS fatal_crashes,
        sum(vru_ksi_crashes) FILTER (WHERE has_aadt) AS vru_ksi_crashes,
        sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt) AS cyclist_ksi_crashes,
        sum(pedestrian_ksi_crashes) FILTER (WHERE has_aadt) AS pedestrian_ksi_crashes,
        sum(heavy_truck_ksi_crashes) FILTER (WHERE has_aadt) AS heavy_truck_ksi_crashes,
        round((sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 3) AS cyclist_ksi_per_100m_vkt,
        round((sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(length_km) FILTER (WHERE has_aadt), 0), 3) AS cyclist_ksi_per_km,
        round((sum(pedestrian_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 3) AS pedestrian_ksi_per_100m_vkt,
        round((sum(vru_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 3) AS vru_ksi_per_100m_vkt,
        round((sum(ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 3) AS ksi_per_100m_vkt,
        round(100.0 * (sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(ksi_crashes) FILTER (WHERE has_aadt), 0), 2) AS cyclist_share_of_ksi_pct,
        round(100.0 * (sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(vru_ksi_crashes) FILTER (WHERE has_aadt), 0), 2) AS cyclist_share_of_vru_ksi_pct,
        sum(cyclist_ksi_crashes) AS network_cyclist_ksi_crashes,
        round(sum(length_km), 3) AS network_length_km,
        round(sum(cyclist_ksi_crashes) / nullif(sum(length_km), 0), 3) AS network_cyclist_ksi_per_km
    FROM read_parquet('{p_str}')
    GROUP BY FEATURE_CODE_DESC
    HAVING count(*) FILTER (WHERE has_aadt) > 0
    ORDER BY cumulative_100m_vkt_18y DESC
    """
    class_cols = [d[0] for d in con.execute(f"DESCRIBE ({class_query})").fetchall()]
    class_rows = [dict(zip(class_cols, r)) for r in con.execute(class_query).fetchall()]

    for row in class_rows:
        rc = row["road_class"]
        if rc in pilot_class_map:
            row["eb_expected_ksi_per_100m_vkt"] = float(pilot_class_map[rc]["eb_expected_ksi_per_100m_vkt"])
        else:
            row["eb_expected_ksi_per_100m_vkt"] = None

    corridor_query = f"""
    WITH base AS (
        SELECT
            LINEAR_NAME_FULL,
            FEATURE_CODE_DESC,
            LINEAR_NAME_FULL || ' (' || FEATURE_CODE_DESC || ')' AS corridor_name,
            count(*) FILTER (WHERE has_aadt) AS monitored_segments,
            round(sum(length_km) FILTER (WHERE has_aadt), 3) AS monitored_length_km,
            round(avg(aadt) FILTER (WHERE has_aadt), 1) AS mean_aadt,
            round(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 4) AS cumulative_100m_vkt,
            sum(ksi_crashes) FILTER (WHERE has_aadt) AS ksi_crashes,
            sum(fatal_crashes) FILTER (WHERE has_aadt) AS fatal_crashes,
            sum(vru_ksi_crashes) FILTER (WHERE has_aadt) AS vru_ksi_crashes,
            sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt) AS cyclist_ksi_crashes,
            sum(pedestrian_ksi_crashes) FILTER (WHERE has_aadt) AS pedestrian_ksi_crashes,
            sum(heavy_truck_ksi_crashes) FILTER (WHERE has_aadt) AS heavy_truck_ksi_crashes,
            round(coalesce((sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 0.0), 3) AS cyclist_ksi_per_100m_vkt,
            round(coalesce((sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(length_km) FILTER (WHERE has_aadt), 0), 0.0), 3) AS cyclist_ksi_per_km,
            round(coalesce(100.0 * (sum(cyclist_ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(ksi_crashes) FILTER (WHERE has_aadt), 0), 0.0), 2) AS cyclist_share_of_ksi_pct,
            round(coalesce((sum(ksi_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 0.0), 3) AS total_ksi_per_100m_vkt,
            round(coalesce((sum(eb_expected_crashes) FILTER (WHERE has_aadt)) / nullif(sum(exposure_100m_vkt) FILTER (WHERE has_aadt), 0), 0.0), 3) AS eb_total_ksi_per_100m_vkt,
            sum(cyclist_ksi_crashes) AS network_cyclist_ksi_crashes,
            round(sum(length_km), 3) AS network_length_km,
            round(sum(cyclist_ksi_crashes) / nullif(sum(length_km), 0), 3) AS network_cyclist_ksi_per_km
        FROM read_parquet('{p_str}')
        WHERE length_km IS NOT NULL AND LINEAR_NAME_FULL != ''
        GROUP BY LINEAR_NAME_FULL, FEATURE_CODE_DESC
    ),
    ranked AS (
        SELECT *,
            CASE WHEN monitored_length_km >= 2.0 AND cumulative_100m_vkt >= 0.5
                 THEN row_number() OVER (
                     PARTITION BY (monitored_length_km >= 2.0 AND cumulative_100m_vkt >= 0.5)
                     ORDER BY cyclist_ksi_crashes DESC, cyclist_ksi_per_100m_vkt DESC
                 )
                 ELSE NULL END AS rank_by_cyclist_ksi,
            CASE WHEN monitored_length_km >= 2.0 AND cumulative_100m_vkt >= 0.5 AND cyclist_ksi_crashes >= 3
                 THEN row_number() OVER (
                     PARTITION BY (monitored_length_km >= 2.0 AND cumulative_100m_vkt >= 0.5 AND cyclist_ksi_crashes >= 3)
                     ORDER BY cyclist_ksi_per_100m_vkt DESC, cyclist_ksi_crashes DESC
                 )
                 ELSE NULL END AS rank_by_cyclist_rate,
            row_number() OVER (ORDER BY network_cyclist_ksi_crashes DESC, network_cyclist_ksi_per_km DESC) AS rank_by_network_cyclist_ksi
        FROM base
    )
    SELECT
        LINEAR_NAME_FULL,
        FEATURE_CODE_DESC,
        corridor_name,
        monitored_segments,
        monitored_length_km,
        mean_aadt,
        cumulative_100m_vkt,
        ksi_crashes,
        fatal_crashes,
        vru_ksi_crashes,
        cyclist_ksi_crashes,
        pedestrian_ksi_crashes,
        heavy_truck_ksi_crashes,
        cyclist_ksi_per_100m_vkt,
        cyclist_ksi_per_km,
        cyclist_share_of_ksi_pct,
        total_ksi_per_100m_vkt,
        eb_total_ksi_per_100m_vkt,
        network_cyclist_ksi_crashes,
        network_length_km,
        network_cyclist_ksi_per_km,
        rank_by_cyclist_ksi,
        rank_by_cyclist_rate,
        rank_by_network_cyclist_ksi
    FROM ranked
    WHERE rank_by_cyclist_ksi <= 15
       OR rank_by_cyclist_rate <= 15
       OR corridor_name IN ('College St (Major Arterial)', 'Harbord St (Minor Arterial)')
    ORDER BY
        CASE WHEN rank_by_cyclist_ksi <= 15 THEN 0
             WHEN rank_by_cyclist_rate <= 15 THEN 1
             ELSE 2 END,
        coalesce(rank_by_cyclist_ksi, 999),
        coalesce(rank_by_cyclist_rate, 999),
        network_cyclist_ksi_crashes DESC
    """
    corr_cols = [d[0] for d in con.execute(f"DESCRIBE ({corridor_query})").fetchall()]
    corridor_rows = [dict(zip(corr_cols, r)) for r in con.execute(corridor_query).fetchall()]
    con.close()

    return class_rows, corridor_rows


def render_synthesis_figure(
    class_rows: list[dict],
    corridor_rows: list[dict],
    co_involved_rows: list[dict],
    bicyclist_perf_rows: list[dict],
    out_path: Path,
) -> None:
    """Render 4-panel synthesis figure combining Toronto corridor exposure and national NCDB typology severity."""
    plt = _ensure_matplotlib()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14.5, 9.6), dpi=160)
    fig.patch.set_facecolor("#fcfcfa")

    # Panel A: Toronto Cyclist KSI per 100M VKT vs per Monitored km by Road Class
    ax_a = axes[0, 0]
    main_cls = [r for r in class_rows if r["road_class"] in MAIN_ROAD_CLASSES]
    main_cls = sorted(main_cls, key=lambda r: float(r["cyclist_ksi_per_100m_vkt"]))
    y_a = list(range(len(main_cls)))
    labels_a = [r["road_class"] for r in main_cls]
    vkt_rates = [float(r["cyclist_ksi_per_100m_vkt"]) for r in main_cls]
    km_rates = [float(r["cyclist_ksi_per_km"]) for r in main_cls]

    ax_a.barh(
        [y - 0.18 for y in y_a],
        vkt_rates,
        height=0.35,
        color="#146f64",
        label="Cyclist KSI / 100M Motor-Vehicle VKT",
    )
    ax_a.barh(
        [y + 0.18 for y in y_a],
        km_rates,
        height=0.35,
        color="#d97f2b",
        label="Cyclist KSI / Monitored km (2006–2023)",
    )
    ax_a.set_yticks(y_a)
    ax_a.set_yticklabels(labels_a, fontsize=9)
    ax_a.set_xlabel("Rate (2006–2023 Cumulative Exposure & Network Length)", fontsize=9)
    ax_a.set_title("A. Toronto Cyclist KSI Exposure Rate vs. Spatial Density by Road Class", fontsize=10.5, fontweight="bold")
    ax_a.grid(axis="x", linestyle="--", alpha=0.4)
    ax_a.legend(loc="lower right", fontsize=8, frameon=True)

    # Panel B: Top Monitored Toronto Corridors by Cyclist KSI per 100M VKT
    ax_b = axes[0, 1]
    top_rate_corridors = [
        r for r in corridor_rows if r["rank_by_cyclist_rate"] is not None and int(r["rank_by_cyclist_rate"]) <= 12
    ]
    top_rate_corridors = sorted(top_rate_corridors, key=lambda r: float(r["cyclist_ksi_per_100m_vkt"]))
    y_b = list(range(len(top_rate_corridors)))
    labels_b = [f"{r['LINEAR_NAME_FULL']} (n={r['cyclist_ksi_crashes']})" for r in top_rate_corridors]
    rates_b = [float(r["cyclist_ksi_per_100m_vkt"]) for r in top_rate_corridors]
    km_b = [float(r["cyclist_ksi_per_km"]) for r in top_rate_corridors]

    ax_b.barh([y - 0.18 for y in y_b], rates_b, height=0.35, color="#153a38", label="Cyclist KSI / 100M VKT")
    ax_b.barh([y + 0.18 for y in y_b], km_b, height=0.35, color="#879e96", label="Cyclist KSI / Monitored km")
    ax_b.set_yticks(y_b)
    ax_b.set_yticklabels(labels_b, fontsize=8.5)
    ax_b.set_xlabel("Cyclist KSI Rate (2006–2023 Monitored Corridors >= 2 km)", fontsize=9)
    ax_b.set_title("B. Top Toronto Corridors by Cyclist KSI per 100M VKT", fontsize=10.5, fontweight="bold")
    ax_b.grid(axis="x", linestyle="--", alpha=0.4)
    ax_b.legend(loc="lower right", fontsize=8, frameon=True)

    # Panel C: National NCDB (2010–2021) Co-Involved Vehicle Fatality Rate vs Share of Fatal Bicycle Collisions
    ax_c = axes[1, 0]
    plot_veh = [
        r for r in co_involved_rows
        if r["vehicle_group"] in {
            "Light-duty vehicle",
            "Cargo or other light truck/van",
            "Bus",
            "Heavy unit truck",
            "Road tractor",
        }
    ]
    plot_veh = sorted(plot_veh, key=lambda r: float(r["fatality_rate_pct"]))
    y_c = list(range(len(plot_veh)))
    labels_c = [
        f"{r['vehicle_group']}\n({r['share_of_all_bicycle_collisions_pct']:.1f}% of collisions)"
        for r in plot_veh
    ]
    fat_rates_c = [float(r["fatality_rate_pct"]) for r in plot_veh]
    colors_c = ["#b14a2e" if r["vehicle_group"] in {"Heavy unit truck", "Road tractor"} else "#4a6fe3" for r in plot_veh]

    bars_c = ax_c.barh(y_c, fat_rates_c, height=0.52, color=colors_c)
    for bar, r in zip(bars_c, plot_veh):
        ax_c.text(
            bar.get_width() + 0.25,
            bar.get_y() + bar.get_height() / 2.0,
            f"{r['fatality_rate_pct']:.2f}% ({r['lethality_multiplier_vs_light_duty']:.1f}x LDV)",
            va="center",
            fontsize=8,
        )
    ax_c.set_yticks(y_c)
    ax_c.set_yticklabels(labels_c, fontsize=8.5)
    ax_c.set_xlim(0, max(fat_rates_c) * 1.32)
    ax_c.set_xlabel("Fatal Collision Rate (% of Co-Involved Bicycle Collisions, 2010–2021)", fontsize=9)
    ax_c.set_title("C. National NCDB Lethality by Co-Involved Vehicle Type", fontsize=10.5, fontweight="bold")
    ax_c.grid(axis="x", linestyle="--", alpha=0.4)

    # Panel D: National M2_full_typology vs M0_baseline Bicyclist Subgroup Performance
    ax_d = axes[1, 1]
    splits = ["Validation\n(2017–2019, n=14,940)", "Test\n(2020–2021, n=8,885)"]
    m0_auc = [float(r["m0_roc_auc"]) for r in bicyclist_perf_rows]
    m2_auc = [float(r["m2_roc_auc"]) for r in bicyclist_perf_rows]
    x_d = [0, 1]

    b1 = ax_d.bar([x - 0.17 for x in x_d], m0_auc, width=0.32, color="#9aa5a2", label="M0 Baseline (Context/Environment Only)")
    b2 = ax_d.bar([x + 0.17 for x in x_d], m2_auc, width=0.32, color="#146f64", label="M2 Full Typology (+Vehicle & VRU Indicators)")
    for bar in list(b1) + list(b2):
        ax_d.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.008,
            f"{bar.get_height():.4f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )
    ax_d.set_xticks(x_d)
    ax_d.set_xticklabels(splits, fontsize=9)
    ax_d.set_ylim(0.50, 0.86)
    ax_d.set_ylabel("Out-of-Time ROC-AUC (Fatal vs. Non-Fatal)", fontsize=9)
    ax_d.set_title("D. National Bicyclist Severity Discrimination Lift (M0 vs. M2)", fontsize=10.5, fontweight="bold")
    ax_d.grid(axis="y", linestyle="--", alpha=0.4)
    ax_d.legend(loc="lower right", fontsize=8, frameon=True)

    fig.suptitle(
        "Canada National Bicycle Collision Typology (2010–2023) & Toronto Arterial Exposure Synthesis (2006–2023)",
        fontsize=12.5,
        fontweight="bold",
        y=0.995,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def run_corridor_exposure_link(
    root: Path | None = None,
    road_to_safety_root: Path | None = None,
) -> dict:
    """Execute the national + Toronto corridor cyclist exposure synthesis and write tables and figure."""
    root = (root or PROJECT_ROOT).resolve()
    rts_root = (road_to_safety_root or ROAD_TO_SAFETY_ROOT).resolve()

    parquet_path = rts_root / "data/derived/corridor_pilot/segment_exposure_crashes.parquet"
    pilot_class_csv = rts_root / "reports/tables/corridor_pilot_by_road_class.csv"
    pilot_top_csv = rts_root / "reports/tables/corridor_pilot_top_corridors.csv"
    typology_or_csv = rts_root / "reports/tables/typology_odds_ratios.csv"
    typology_perf_csv = rts_root / "reports/tables/typology_subgroup_performance.csv"

    class_rows, corridor_rows = compute_toronto_cyclist_exposure(parquet_path, pilot_class_csv)
    co_involved_rows = compute_national_co_involved_lethality(root)

    perf_all = _read_csv(typology_perf_csv)
    bicyclist_perf = [r for r in perf_all if r["subgroup"] == "bicyclist"]
    freight_vru_perf = [r for r in perf_all if r["subgroup"] == "heavy_freight_x_vru"]
    or_rows = _read_csv(typology_or_csv)

    tables_dir = root / "reports/tables"
    figures_dir = root / "reports/figures"
    class_out = tables_dir / "toronto_cyclist_corridor_exposure_by_class.csv"
    corridors_out = tables_dir / "toronto_top_cyclist_ksi_corridors.csv"
    figure_out = figures_dir / "cyclist_corridor_exposure_synthesis.png"

    _write_csv(class_out, class_rows)
    _write_csv(corridors_out, corridor_rows)
    render_synthesis_figure(class_rows, corridor_rows, co_involved_rows, bicyclist_perf, figure_out)

    # Compute headline synthesis metrics
    monitored_cyclist_ksi = sum(int(r["cyclist_ksi_crashes"]) for r in class_rows)
    network_cyclist_ksi = sum(int(r["network_cyclist_ksi_crashes"]) for r in class_rows)
    monitored_vkt_100m = sum(float(r["cumulative_100m_vkt_18y"]) for r in class_rows)
    monitored_km = sum(float(r["monitored_length_km"]) for r in class_rows)

    major_row = next(r for r in class_rows if r["road_class"] == "Major Arterial")
    minor_row = next(r for r in class_rows if r["road_class"] == "Minor Arterial")

    ldv_row = next(r for r in co_involved_rows if r["vehicle_group"] == "Light-duty vehicle")
    ht_row = next(r for r in co_involved_rows if r["vehicle_group"] == "Heavy unit truck")
    rt_row = next(r for r in co_involved_rows if r["vehicle_group"] == "Road tractor")
    hf_row = next(r for r in co_involved_rows if r["vehicle_group"] == "Heavy freight combined (truck or tractor)")

    val_bicyclist = next(r for r in bicyclist_perf if r["split"] == "validation_2017_2019")
    test_bicyclist = next(r for r in bicyclist_perf if r["split"] == "test_2020_2021")

    summary = {
        "toronto_corridor_exposure": {
            "study_period": "2006-2023 (18 years)",
            "monitored_cyclist_ksi_crashes": monitored_cyclist_ksi,
            "network_cyclist_ksi_crashes": network_cyclist_ksi,
            "pooled_cyclist_ksi_per_100m_vkt": round(monitored_cyclist_ksi / monitored_vkt_100m, 3),
            "pooled_cyclist_ksi_per_monitored_km": round(monitored_cyclist_ksi / monitored_km, 3),
            "major_arterial_cyclist_ksi_per_100m_vkt": float(major_row["cyclist_ksi_per_100m_vkt"]),
            "major_arterial_cyclist_ksi_per_km": float(major_row["cyclist_ksi_per_km"]),
            "minor_arterial_cyclist_ksi_per_100m_vkt": float(minor_row["cyclist_ksi_per_100m_vkt"]),
            "minor_arterial_cyclist_ksi_per_km": float(minor_row["cyclist_ksi_per_km"]),
            "arterial_share_of_monitored_cyclist_ksi_pct": round(
                100.0 * (int(major_row["cyclist_ksi_crashes"]) + int(minor_row["cyclist_ksi_crashes"])) / monitored_cyclist_ksi,
                2,
            ),
            "top_corridor_by_count": corridor_rows[0]["corridor_name"],
            "top_corridor_by_rate": next(
                r["corridor_name"] for r in corridor_rows if r["rank_by_cyclist_rate"] == 1
            ),
        },
        "national_ncdb_synthesis": {
            "unique_bicycle_collisions_2010_2021": 68687,
            "fatal_bicycle_collisions_2010_2021": 614,
            "light_duty_co_involvement_share_pct": ldv_row["share_of_all_bicycle_collisions_pct"],
            "light_duty_fatality_rate_pct": ldv_row["fatality_rate_pct"],
            "heavy_truck_fatality_rate_pct": ht_row["fatality_rate_pct"],
            "heavy_truck_lethality_multiplier": ht_row["lethality_multiplier_vs_light_duty"],
            "road_tractor_fatality_rate_pct": rt_row["fatality_rate_pct"],
            "road_tractor_lethality_multiplier": rt_row["lethality_multiplier_vs_light_duty"],
            "heavy_freight_combined_collisions": hf_row["collisions"],
            "heavy_freight_combined_fatal_collisions": hf_row["fatal_collisions"],
            "heavy_freight_share_of_collisions_pct": hf_row["share_of_all_bicycle_collisions_pct"],
            "heavy_freight_share_of_fatal_collisions_pct": hf_row["share_of_fatal_bicycle_collisions_pct"],
            "heavy_freight_combined_fatality_rate_pct": hf_row["fatality_rate_pct"],
            "heavy_freight_lethality_multiplier": hf_row["lethality_multiplier_vs_light_duty"],
        },
        "national_typology_model_bicyclist": {
            "validation_2017_2019_m0_roc_auc": float(val_bicyclist["m0_roc_auc"]),
            "validation_2017_2019_m2_roc_auc": float(val_bicyclist["m2_roc_auc"]),
            "validation_2017_2019_roc_auc_lift": round(
                float(val_bicyclist["m2_roc_auc"]) - float(val_bicyclist["m0_roc_auc"]), 4
            ),
            "test_2020_2021_m0_roc_auc": float(test_bicyclist["m0_roc_auc"]),
            "test_2020_2021_m2_roc_auc": float(test_bicyclist["m2_roc_auc"]),
            "test_2020_2021_roc_auc_lift": round(
                float(test_bicyclist["m2_roc_auc"]) - float(test_bicyclist["m0_roc_auc"]), 4
            ),
            "heavy_freight_x_vru_odds_ratio": float(
                next(r["odds_ratio"] for r in or_rows if r["feature"] == "heavy_freight_x_vru")
            ),
        },
        "outputs": {
            "class_table": str(class_out.relative_to(root)),
            "corridors_table": str(corridors_out.relative_to(root)),
            "synthesis_figure": str(figure_out.relative_to(root)),
            "pilot_top_corridors_ref": str(pilot_top_csv),
            "freight_vru_perf_rows": len(freight_vru_perf),
        },
    }
    return summary


def main() -> None:
    summary = run_corridor_exposure_link()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
