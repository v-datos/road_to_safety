"""Phase 2: Reintroduce Road-User (P_USER) and Vehicle (V_TYPE) Typologies into Collision Severity Models.

Extracts person-level P_USER and vehicle-level V_TYPE indicators from all 23 raw NCDB
annual releases (1999-2021), reconciles 1:1 with the 2,949,846 canonical collisions in
`data/derived/collisions.parquet`, and evaluates nested severity models:
  - M0_conditions_only: 8 environmental/temporal/roadway condition variables
  - M1_plus_p_user: M0 + road-user involvement flags (pedestrian, bicyclist, motorcyclist, passenger)
  - M2_full_typology: M1 + vehicle typology flags (heavy truck, road tractor, bus, light truck/van,
                      multi-vehicle, heavy-freight x VRU interaction)
Evaluates discrimination (ROC-AUC, PR-AUC / Average Precision), proper scoring rules
(Log-Loss, Brier Score, ECE), subgroup performance, and adjusted odds ratios across the
2014-2019 rolling chronological folds and the 2020-2021 out-of-time pandemic stress test.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import warnings

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy. sparse import hstack, csr_matrix
from scipy.special import expit, logit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder

from .explore import sha256

PROJECT_ROOT = Path(__file__).resolve().parents[2]

P_USER_FEATURES = [
    "has_pedestrian",
    "has_bicyclist",
    "has_motorcyclist",
    "has_passenger",
    "has_unknown_user",
]

V_TYPE_FEATURES = [
    "has_light_duty",
    "has_light_truck_van",
    "has_heavy_truck",
    "has_road_tractor",
    "has_bus",
    "has_motorcycle_moped",
    "has_bicycle_vehicle",
    "has_special_offroad",
    "has_unknown_vehicle",
    "multi_vehicle",
    "heavy_freight_x_vru",
]

TYPOLOGY_LABELS = {
    "has_pedestrian": "Pedestrian involved (P_USER=3 / V_TYPE=NN)",
    "has_bicyclist": "Bicyclist person record (P_USER=4)",
    "has_motorcyclist": "Motorcyclist person record (P_USER=5)",
    "has_passenger": "Motor vehicle passenger present (P_USER=2)",
    "has_unknown_user": "Unstated/unknown road user present (P_USER=U)",
    "has_light_duty": "Light-duty vehicle involved (V_TYPE=01)",
    "has_light_truck_van": "Light truck / cargo van <=4536 kg (V_TYPE=05,06)",
    "has_heavy_truck": "Unit heavy truck >4536 kg (V_TYPE=07)",
    "has_road_tractor": "Road tractor / semi-trailer (V_TYPE=08)",
    "has_bus": "Bus (school / transit / intercity; V_TYPE=09,10,11)",
    "has_motorcycle_moped": "Motorcycle / moped vehicle unit (V_TYPE=14)",
    "has_bicycle_vehicle": "Bicycle vehicle unit (V_TYPE=17)",
    "has_special_offroad": "Off-road / farm / construction / streetcar (V_TYPE=16,18-23)",
    "has_unknown_vehicle": "Unknown / other vehicle type (V_TYPE=UU,XX,QQ)",
    "multi_vehicle": "Multi-vehicle collision (>=2 distinct motor/cycle units)",
    "heavy_freight_x_vru": "Heavy truck/tractor x Vulnerable Road User interaction",
}


def _norm_code(val: object) -> str:
    text = "" if val is None else str(val).strip().upper()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return str(int(text)) if text.isdigit() else text


def extract_typology_for_resource(task: tuple[str, dict, str]) -> dict:
    """Worker function: extract collision-level P_USER and V_TYPE flags for one annual NCDB file."""
    root_str, resource, out_dir_str = task
    root = Path(root_str)
    out_dir = Path(out_dir_str)
    source_path = root / resource["local_path"]
    year_expected = str(resource["year"])
    source_id = resource["resource_id"]

    out_parquet = out_dir / f"{year_expected}_typology.parquet"
    if out_parquet.exists():
        con = duckdb.connect()
        n_collisions = int(con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_parquet.as_posix()}')").fetchone()[0])
        con.close()
        if n_collisions > 0:
            return {
                "year": int(year_expected),
                "source_id": source_id,
                "collisions": n_collisions,
                "parquet": str(out_parquet),
            }

    if source_path.suffix.lower() == ".csv":
        is_fr = "-fr" in source_path.name
        encoding = "cp1252" if is_fr else "utf-8-sig"
        col_map = (
            {"C_ANNÉE": "C_YEAR", "C_CAS": "C_CASE", "V_ID": "V_ID", "V_TYPE": "V_TYPE", "P_USAG": "P_USER"}
            if is_fr
            else {"C_YEAR": "C_YEAR", "C_CASE": "C_CASE", "V_ID": "V_ID", "V_TYPE": "V_TYPE", "P_USER": "P_USER"}
        )
        df = pd.read_csv(
            source_path,
            dtype=str,
            keep_default_na=False,
            encoding=encoding,
            usecols=list(col_map.keys()),
        ).rename(columns=col_map)
    else:
        sheet = resource.get("sheet") or 0
        df = pd.read_excel(
            source_path,
            sheet_name=sheet,
            engine="calamine",
            dtype=str,
            keep_default_na=False,
        )
        keep_cols = [c for c in ["C_YEAR", "C_CASE", "V_ID", "V_TYPE", "P_USER"] if c in df.columns]
        df = df[keep_cols].copy()

    for col in ["C_YEAR", "C_CASE", "V_ID", "V_TYPE", "P_USER"]:
        s = df[col].astype(str).str.strip().str.upper()
        s = s.str.replace(r"^(\d+)\.0$", r"\1", regex=True)
        # Strip leading zeros on all-digit strings
        is_dig = s.str.isdigit()
        df[col] = np.where(is_dig, s.str.lstrip("0").replace("", "0"), s)

    # Filter to valid collision keys matching prepare_collisions.py policy
    valid_key = (
        df["C_YEAR"].eq(year_expected)
        & df["C_CASE"].str.isdigit()
        & df["C_CASE"].ne("0")
    )
    df = df.loc[valid_key].copy()

    con = duckdb.connect()
    con.register("raw_rows", df)
    out_parquet = out_dir / f"{year_expected}_typology.parquet"
    query = f"""
    COPY (
        SELECT
            '{source_id}' AS source_id,
            C_YEAR,
            C_CASE,
            CAST(COUNT(*) AS INTEGER) AS person_vehicle_rows,
            CAST(COUNT(DISTINCT CASE
                WHEN V_ID NOT IN ('', '0', '99', 'N', 'NN', 'U', 'UU', 'X', 'XX', 'Q', 'QQ')
                THEN V_ID ELSE NULL END) AS INTEGER) AS distinct_vehicles,
            CAST(MAX(CASE WHEN P_USER = '1' THEN 1 ELSE 0 END) AS TINYINT) AS has_driver,
            CAST(MAX(CASE WHEN P_USER = '2' THEN 1 ELSE 0 END) AS TINYINT) AS has_passenger,
            CAST(MAX(CASE WHEN P_USER = '3' OR V_TYPE IN ('N', 'NN') OR V_ID = '99' THEN 1 ELSE 0 END) AS TINYINT) AS has_pedestrian,
            CAST(MAX(CASE WHEN P_USER = '4' THEN 1 ELSE 0 END) AS TINYINT) AS has_bicyclist,
            CAST(MAX(CASE WHEN P_USER = '5' THEN 1 ELSE 0 END) AS TINYINT) AS has_motorcyclist,
            CAST(MAX(CASE WHEN P_USER IN ('', 'U', 'UU', 'X', 'XX', 'Q', 'QQ', 'N', 'NN') THEN 1 ELSE 0 END) AS TINYINT) AS has_unknown_user,
            CAST(MAX(CASE WHEN V_TYPE = '1' THEN 1 ELSE 0 END) AS TINYINT) AS has_light_duty,
            CAST(MAX(CASE WHEN V_TYPE IN ('5', '6') THEN 1 ELSE 0 END) AS TINYINT) AS has_light_truck_van,
            CAST(MAX(CASE WHEN V_TYPE = '7' THEN 1 ELSE 0 END) AS TINYINT) AS has_heavy_truck,
            CAST(MAX(CASE WHEN V_TYPE = '8' THEN 1 ELSE 0 END) AS TINYINT) AS has_road_tractor,
            CAST(MAX(CASE WHEN V_TYPE IN ('9', '10', '11') THEN 1 ELSE 0 END) AS TINYINT) AS has_bus,
            CAST(MAX(CASE WHEN V_TYPE = '14' THEN 1 ELSE 0 END) AS TINYINT) AS has_motorcycle_moped,
            CAST(MAX(CASE WHEN V_TYPE = '17' THEN 1 ELSE 0 END) AS TINYINT) AS has_bicycle_vehicle,
            CAST(MAX(CASE WHEN V_TYPE IN ('16', '18', '19', '20', '21', '22', '23') THEN 1 ELSE 0 END) AS TINYINT) AS has_special_offroad,
            CAST(MAX(CASE WHEN V_TYPE IN ('', 'U', 'UU', 'X', 'XX', 'Q', 'QQ') THEN 1 ELSE 0 END) AS TINYINT) AS has_unknown_vehicle
        FROM raw_rows
        GROUP BY C_YEAR, C_CASE
        ORDER BY TRY_CAST(C_CASE AS BIGINT)
    ) TO '{out_parquet.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    con.execute(query)
    n_collisions = int(con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_parquet.as_posix()}')").fetchone()[0])
    con.close()
    return {
        "year": int(year_expected),
        "source_id": source_id,
        "collisions": n_collisions,
        "parquet": str(out_parquet),
    }


def build_or_load_typology_parquet(root: Path, workers: int = 4, rebuild: bool = False) -> Path:
    """Build or verify `data/derived/typology_severity/collision_typologies.parquet`."""
    out_dir = root / "data/derived/typology_severity"
    out_dir.mkdir(parents=True, exist_ok=True)
    target_parquet = out_dir / "collision_typologies.parquet"
    meta_path = out_dir / "extraction_manifest.json"

    catalog = json.loads((root / "data/sources.json").read_text())
    selected = [r for r in catalog["resources"] if r.get("selected") and r.get("year") is not None]
    selected.sort(key=lambda r: int(r["year"]))

    if target_parquet.exists() and meta_path.exists() and not rebuild:
        meta = json.loads(meta_path.read_text())
        if meta.get("total_collisions") == 2949846:
            return target_parquet

    tmp_dir = out_dir / "_tmp_years"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(extract_typology_for_resource, (str(root), r, str(tmp_dir)))
            for r in selected
        ]
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            print(f"Extracted typology year {res['year']}: {res['collisions']:,} collisions", flush=True)

    results.sort(key=lambda r: r["year"])
    con = duckdb.connect()
    glob_pattern = (tmp_dir / "*_typology.parquet").as_posix()
    base_parquet = (root / "data/derived/collisions.parquet").as_posix()

    # Join 1:1 with canonical collisions.parquet and derive interaction flags
    con.execute(
        f"""
        COPY (
            SELECT
                c.source_id,
                c.C_YEAR,
                c.C_CASE,
                c.is_fatal,
                c.C_MNTH,
                c.C_WDAY,
                c.C_HOUR,
                c.C_RCFG,
                c.C_WTHR,
                c.C_RSUR,
                c.C_RALN,
                c.C_TRAF,
                t.person_vehicle_rows,
                t.distinct_vehicles,
                t.has_driver,
                t.has_passenger,
                t.has_pedestrian,
                t.has_bicyclist,
                t.has_motorcyclist,
                t.has_unknown_user,
                t.has_light_duty,
                t.has_light_truck_van,
                t.has_heavy_truck,
                t.has_road_tractor,
                t.has_bus,
                t.has_motorcycle_moped,
                t.has_bicycle_vehicle,
                t.has_special_offroad,
                t.has_unknown_vehicle,
                CAST(CASE WHEN t.distinct_vehicles >= 2 THEN 1 ELSE 0 END AS TINYINT) AS multi_vehicle,
                CAST(CASE WHEN (t.has_pedestrian = 1 OR t.has_bicyclist = 1 OR t.has_motorcyclist = 1
                                OR t.has_bicycle_vehicle = 1 OR t.has_motorcycle_moped = 1)
                          THEN 1 ELSE 0 END AS TINYINT) AS has_vru,
                CAST(CASE WHEN (t.has_heavy_truck = 1 OR t.has_road_tractor = 1)
                          THEN 1 ELSE 0 END AS TINYINT) AS has_heavy_freight,
                CAST(CASE WHEN (t.has_heavy_truck = 1 OR t.has_road_tractor = 1)
                           AND (t.has_pedestrian = 1 OR t.has_bicyclist = 1 OR t.has_motorcyclist = 1
                                OR t.has_bicycle_vehicle = 1 OR t.has_motorcycle_moped = 1)
                          THEN 1 ELSE 0 END AS TINYINT) AS heavy_freight_x_vru
            FROM read_parquet('{base_parquet}') c
            INNER JOIN read_parquet('{glob_pattern}') t
                ON c.source_id = t.source_id
               AND c.C_YEAR = t.C_YEAR
               AND c.C_CASE = t.C_CASE
            ORDER BY CAST(c.C_YEAR AS INTEGER), c.source_id, TRY_CAST(c.C_CASE AS BIGINT)
        ) TO '{target_parquet.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """
    )
    total_n, fatal_n = con.execute(
        f"SELECT COUNT(*), SUM(CAST(is_fatal AS BIGINT)) FROM read_parquet('{target_parquet.as_posix()}')"
    ).fetchone()
    con.close()

    for p in tmp_dir.glob("*.parquet"):
        p.unlink()
    tmp_dir.rmdir()

    if int(total_n) != 2949846 or int(fatal_n) != 47793:
        raise ValueError(f"Reconciliation failure: got {total_n} collisions and {fatal_n} fatals")

    meta = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_collisions": int(total_n),
        "fatal_collisions": int(fatal_n),
        "years": results,
        "parquet_sha256": sha256(target_parquet),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return target_parquet


def compute_ece(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    ece = 0.0
    n = len(y)
    for b in range(n_bins):
        mask = bins == b
        cnt = int(mask.sum())
        if cnt > 0:
            ece += (cnt / n) * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(ece)


def score_predictions(y: np.ndarray, p: np.ndarray) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    obs = float(y.mean())
    pred = float(p.mean())
    return {
        "n": int(len(y)),
        "fatal": int(y.sum()),
        "observed_prevalence": obs,
        "mean_predicted_prob": pred,
        "oe_ratio": obs / pred if pred > 0 else np.nan,
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else np.nan,
        "pr_auc": float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else np.nan,
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y, p)),
        "ece": compute_ece(y, p),
    }


def fit_intercept_shift(logits: np.ndarray, y: np.ndarray) -> float:
    """Find additive intercept delta on log-odds so mean(expit(logits + delta)) == mean(y)."""
    target_mean = float(np.mean(y))
    lo, hi = -5.0, 5.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if float(np.mean(expit(logits + mid))) < target_mean:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def render_figures(
    summary_df: pd.DataFrame,
    fold_df: pd.DataFrame,
    or_df: pd.DataFrame,
    subgroup_df: pd.DataFrame,
    figures_dir: Path,
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    # Figure 1: Rolling chronological folds (2014-2019) + 2020-2021 Out-of-time discrimination & log-loss
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), layout="constrained")
    colors = {
        "M0_conditions_only": "#6b7280",
        "M1_plus_p_user": "#2563eb",
        "M2_full_typology": "#dc2626",
    }
    labels = {
        "M0_conditions_only": "M0: Conditions Only (8 vars)",
        "M1_plus_p_user": "M1: + Road-User Typology (P_USER)",
        "M2_full_typology": "M2: + Vehicle & VRU Typology (P_USER + V_TYPE)",
    }

    annual = fold_df[fold_df["calibration_mode"] == "uncalibrated"].sort_values("eval_year")
    for model_name, grp in annual.groupby("model", sort=False):
        axes[0].plot(
            grp["eval_year"],
            grp["roc_auc"],
            marker="o",
            linewidth=2.0,
            color=colors[model_name],
            label=labels[model_name],
        )
        axes[1].plot(
            grp["eval_year"],
            grp["pr_auc"] * 100.0,
            marker="s",
            linewidth=2.0,
            color=colors[model_name],
            label=labels[model_name],
        )

    for ax in axes:
        ax.axvline(2019.5, color="#374151", linestyle="--", linewidth=1.1, label="Pandemic test split (2020+)")
        ax.set_xticks(sorted(annual["eval_year"].unique()))
        ax.set_xlabel("Evaluation Year (Expanding Training Window 1999..t-1)")
        ax.grid(alpha=0.25)

    axes[0].set_ylabel("ROC-AUC")
    axes[0].set_title("A. Discrimination Gain Across Rolling & Test Years (ROC-AUC)")
    axes[0].legend(fontsize=8.5, loc="lower left")

    axes[1].set_ylabel("PR-AUC / Average Precision (%)")
    axes[1].set_title("B. Precision-Recall AUC Gain (PR-AUC %)")
    axes[1].legend(fontsize=8.5, loc="upper left")

    fig.suptitle(
        "Phase 2: Incorporating Road-User (P_USER) and Vehicle (V_TYPE) Typologies (1999–2021 NCDB)",
        fontsize=12,
        fontweight="bold",
    )
    fig.savefig(figures_dir / "typology_model_comparison.png", dpi=180)
    plt.close(fig)

    # Figure 2: Adjusted Odds Ratios for Road-User & Vehicle Typology Factors + Subgroup Lift
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8), layout="constrained")
    typ_or = or_df[or_df["feature_group"].isin(["P_USER", "V_TYPE"])].sort_values("odds_ratio", ascending=True)
    y_pos = np.arange(len(typ_or))
    bar_colors = np.where(typ_or["odds_ratio"] >= 1.0, "#dc2626", "#2563eb")
    axes[0].barh(y_pos, typ_or["odds_ratio"], color=bar_colors, alpha=0.88)
    axes[0].axvline(1.0, color="#111827", linestyle="--", linewidth=1.1)
    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(typ_or["label"], fontsize=8.5)
    axes[0].set_xlabel("Adjusted Fatal Collision Odds Ratio (M2 Full Typology, Train 1999–2019)")
    axes[0].set_title("A. Adjusted Fatality Drivers (Controlling for 8 Env/Road Conditions)")
    for idx, row in enumerate(typ_or.itertuples()):
        axes[0].text(
            row.odds_ratio + 0.05,
            idx,
            f"{row.odds_ratio:.2f}x",
            va="center",
            fontsize=8,
        )
    axes[0].set_xlim(0, max(typ_or["odds_ratio"]) * 1.18)

    sub_test = subgroup_df[subgroup_df["split"] == "test_2020_2021"].copy()
    sub_test = sub_test.sort_values("observed_fatality_rate_pct", ascending=True)
    y2 = np.arange(len(sub_test))
    h = 0.26
    axes[1].barh(y2 + h, sub_test["observed_fatality_rate_pct"], height=h, color="#111827", label="Observed Fatal %")
    axes[1].barh(y2, sub_test["m0_mean_pred_pct"], height=h, color="#9ca3af", label="M0 Conditions Only Pred %")
    axes[1].barh(y2 - h, sub_test["m2_mean_pred_pct"], height=h, color="#dc2626", label="M2 Full Typology Pred %")
    axes[1].set_yticks(y2)
    axes[1].set_yticklabels(sub_test["subgroup_label"], fontsize=8.5)
    axes[1].set_xlabel("Fatal Collision Rate (%) on 2020–2021 Out-of-Time Test Set")
    axes[1].set_title("B. Subgroup Calibration Recovery: M0 vs M2 (Test 2020–2021)")
    axes[1].legend(fontsize=8.5, loc="lower right")

    fig.suptitle(
        "Phase 2: Pedestrian, Cyclist, Motorcyclist & Heavy-Truck Fatality Drivers",
        fontsize=12,
        fontweight="bold",
    )
    fig.savefig(figures_dir / "typology_odds_and_subgroups.png", dpi=180)
    plt.close(fig)


def run(root: Path | None = None, workers: int = 4, rebuild: bool = False) -> dict:
    root = (root or PROJECT_ROOT).resolve()
    out_dir = root / "data/derived/typology_severity"
    tables_dir = root / "reports/tables"
    figures_dir = root / "reports/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    typology_parquet = build_or_load_typology_parquet(root, workers=workers, rebuild=rebuild)

    protocol = json.loads((root / "data/reference/severity_protocol.json").read_text())
    cond_features = protocol["features"]
    domains = protocol["categorical_domains"]
    references = protocol["reference_levels"]

    con = duckdb.connect()
    df = con.execute(f"SELECT * FROM read_parquet('{typology_parquet.as_posix()}')").df()
    con.close()

    year = df["C_YEAR"].astype(int).to_numpy()
    y = df["is_fatal"].astype(int).to_numpy()

    encoder = OneHotEncoder(
        categories=[domains[f] for f in cond_features],
        drop=[references[f] for f in cond_features],
        handle_unknown="error",
        sparse_output=True,
        dtype=np.float64,
    )
    X_cond = encoder.fit_transform(df[cond_features])
    X_p_user = csr_matrix(df[P_USER_FEATURES].to_numpy(dtype=np.float64))
    X_v_type = csr_matrix(df[V_TYPE_FEATURES].to_numpy(dtype=np.float64))

    model_matrices = {
        "M0_conditions_only": X_cond,
        "M1_plus_p_user": hstack([X_cond, X_p_user], format="csr"),
        "M2_full_typology": hstack([X_cond, X_p_user, X_v_type], format="csr"),
    }

    # Evaluate across rolling development folds (2014-2019) + 2020 and 2021 test years
    fold_rows = []
    eval_years = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]

    # Store predictions for 2017-2021 (validation 2017-2019 + test 2020-2021) for Phase 3 operational triage
    # Specifically: fit on 1999-2016 to score 2017-2019 validation & 2020-2021 test (matching frozen split),
    # AND fit on 1999-2018 (cal 2019) / 1999-2019 to score 2020-2021.
    summary_rows = []

    # 1. Rolling year-by-year evaluation (train <= min(t-1, 2019) so 2020 & 2021 use pre-pandemic <=2019 model)
    rolling_csv = tables_dir / "typology_rolling_folds.csv"
    if rolling_csv.exists() and not rebuild:
        fold_df = pd.read_csv(rolling_csv)
    else:
        fitted_pre_pandemic_models = {}
        fitted_pre_pandemic_cal_delta = {}

        for t in eval_years:
            train_cutoff = min(t - 1, 2018) if t >= 2019 else (t - 2)
            cal_year = min(t - 1, 2019)
            train_mask = year <= train_cutoff
            cal_mask = year == cal_year
            eval_mask = year == t

            for model_name, X_mat in model_matrices.items():
                cache_key = (model_name, train_cutoff)
                if cache_key not in fitted_pre_pandemic_models:
                    clf = LogisticRegression(
                        C=1.0,
                        penalty="l2",
                        solver="lbfgs",
                        max_iter=300,
                        tol=1e-4,
                        random_state=2026,
                    )
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", ConvergenceWarning)
                        clf.fit(X_mat[train_mask], y[train_mask])
                    fitted_pre_pandemic_models[cache_key] = clf
                    cal_logits = clf.decision_function(X_mat[cal_mask])
                    fitted_pre_pandemic_cal_delta[cache_key] = fit_intercept_shift(cal_logits, y[cal_mask])

                clf = fitted_pre_pandemic_models[cache_key]
                delta = fitted_pre_pandemic_cal_delta[cache_key]
                eval_logits = clf.decision_function(X_mat[eval_mask])
                p_uncal = expit(eval_logits)
                p_recal = expit(eval_logits + delta)

                m_uncal = score_predictions(y[eval_mask], p_uncal)
                m_recal = score_predictions(y[eval_mask], p_recal)
                fold_rows.append({
                    "eval_year": t,
                    "train_years": f"1999-{train_cutoff}",
                    "cal_year": cal_year,
                    "model": model_name,
                    "calibration_mode": "uncalibrated",
                    "intercept_shift": 0.0,
                    **m_uncal,
                })
                fold_rows.append({
                    "eval_year": t,
                    "train_years": f"1999-{train_cutoff}",
                    "cal_year": cal_year,
                    "model": model_name,
                    "calibration_mode": "prior_year_intercept",
                    "intercept_shift": round(delta, 5),
                    **m_recal,
                })

        fold_df = pd.DataFrame(fold_rows)
        fold_df.to_csv(rolling_csv, index=False)

    # 2. Canonical Split Benchmark: Train 1999-2016, Validation 2017-2019, Test 2020-2021
    # Plus Full Pre-Pandemic Fit (1999-2019) scored on 2020-2021
    train_16 = year <= 2016
    val_17_19 = (year >= 2017) & (year <= 2019)
    test_20_21 = (year >= 2020) & (year <= 2021)
    eval_17_21 = year >= 2017

    eval_pred_df = df.loc[
        eval_17_21,
        [
            "source_id", "C_YEAR", "C_CASE", "is_fatal",
            "C_RCFG", "C_WTHR", "C_RSUR", "C_RALN", "C_TRAF", "C_HOUR",
            *P_USER_FEATURES, *V_TYPE_FEATURES,
            "has_vru", "has_heavy_freight",
        ],
    ].copy()
    # Deduplicate any repeated column names while preserving order
    eval_pred_df = eval_pred_df.loc[:, ~eval_pred_df.columns.duplicated()].copy()
    eval_pred_df["split"] = np.where(eval_pred_df["C_YEAR"].astype(int) <= 2019, "validation", "test")

    for model_name, X_mat in model_matrices.items():
        clf_16 = LogisticRegression(
            C=1.0, penalty="l2", solver="lbfgs", max_iter=300, tol=1e-4, random_state=2026
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            clf_16.fit(X_mat[train_16], y[train_16])

        logits_eval = clf_16.decision_function(X_mat[eval_17_21])
        p_eval = expit(logits_eval)
        # Fit intercept recalibration on validation (2017-2019) and more recent 2019 year
        val_sub_mask = (year[eval_17_21] == 2019)
        delta_2019 = fit_intercept_shift(logits_eval[val_sub_mask], y[eval_17_21][val_sub_mask])
        p_eval_recal = expit(logits_eval + delta_2019)

        eval_pred_df[f"p_{model_name}"] = p_eval
        eval_pred_df[f"p_{model_name}_recal"] = p_eval_recal

        for split_name, mask in [
            ("train_1999_2016", train_16),
            ("validation_2017_2019", val_17_19),
            ("test_2020_2021_uncal", test_20_21),
        ]:
            p_split = expit(clf_16.decision_function(X_mat[mask]))
            summary_rows.append({
                "split": split_name,
                "model": model_name,
                **score_predictions(y[mask], p_split),
            })

        # Also record test_2020_2021 with 2019 intercept recalibration
        p_test_recal = expit(clf_16.decision_function(X_mat[test_20_21]) + delta_2019)
        summary_rows.append({
            "split": "test_2020_2021_recal_2019",
            "model": model_name,
            **score_predictions(y[test_20_21], p_test_recal),
        })

    # Save 2017-2021 evaluation predictions for Phase 3 operational triage
    pred_parquet = out_dir / "eval_predictions_2017_2021.parquet"
    con = duckdb.connect()
    con.register("eval_preds", eval_pred_df)
    con.execute(f"COPY eval_preds TO '{pred_parquet.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    con.close()

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(tables_dir / "typology_model_summary.csv", index=False)

    # 3. Extract Full Pre-Pandemic (1999-2019) M2 Model Coefficients & Adjusted Odds Ratios
    train_19 = year <= 2019
    clf_m2_full = LogisticRegression(
        C=1.0, penalty="l2", solver="lbfgs", max_iter=300, tol=1e-4, random_state=2026
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        clf_m2_full.fit(model_matrices["M2_full_typology"][train_19], y[train_19])

    coefs = clf_m2_full.coef_[0]
    n_cond_cols = X_cond.shape[1]
    typ_features = P_USER_FEATURES + V_TYPE_FEATURES
    or_rows = []
    for idx, feat in enumerate(typ_features):
        beta = float(coefs[n_cond_cols + idx])
        grp = "P_USER" if feat in P_USER_FEATURES else "V_TYPE"
        pos_mask = df[feat].to_numpy() == 1
        or_rows.append({
            "feature": feat,
            "feature_group": grp,
            "label": TYPOLOGY_LABELS[feat],
            "collisions_all_years": int(pos_mask.sum()),
            "fatal_collisions_all_years": int(y[pos_mask].sum()),
            "unadjusted_fatality_rate_pct": round(float(y[pos_mask].mean() * 100.0), 4),
            "coefficient_log_odds": round(beta, 5),
            "odds_ratio": round(float(np.exp(beta)), 4),
        })
    or_df = pd.DataFrame(or_rows).sort_values("odds_ratio", ascending=False)
    or_df.to_csv(tables_dir / "typology_odds_ratios.csv", index=False)

    # 4. Subgroup Performance Table (Validation 2017-2019 & Test 2020-2021)
    subgroup_defs = [
        ("all_collisions", "All Collisions", lambda d: np.ones(len(d), dtype=bool)),
        ("pedestrian", "Pedestrian Involved", lambda d: d["has_pedestrian"].eq(1).to_numpy()),
        ("bicyclist", "Bicyclist Involved", lambda d: (d["has_bicyclist"].eq(1) | d["has_bicycle_vehicle"].eq(1)).to_numpy()),
        ("motorcyclist", "Motorcyclist Involved", lambda d: (d["has_motorcyclist"].eq(1) | d["has_motorcycle_moped"].eq(1)).to_numpy()),
        ("any_vru", "Any Vulnerable Road User (VRU)", lambda d: d["has_vru"].eq(1).to_numpy()),
        ("heavy_truck", "Unit Heavy Truck (>4536 kg)", lambda d: d["has_heavy_truck"].eq(1).to_numpy()),
        ("road_tractor", "Road Tractor / Semi-Trailer", lambda d: d["has_road_tractor"].eq(1).to_numpy()),
        ("heavy_freight_x_vru", "Heavy Freight x VRU Collision", lambda d: d["heavy_freight_x_vru"].eq(1).to_numpy()),
        ("motor_vehicle_only_light", "Motor-Vehicle Only (No VRU, No Heavy Freight)", lambda d: (d["has_vru"].eq(0) & d["has_heavy_freight"].eq(0)).to_numpy()),
    ]

    subgroup_rows = []
    for split_key, split_label in [("validation", "validation_2017_2019"), ("test", "test_2020_2021")]:
        sub_df = eval_pred_df[eval_pred_df["split"] == split_key]
        for sg_code, sg_label, mask_fn in subgroup_defs:
            m = mask_fn(sub_df)
            if not np.any(m):
                continue
            y_sg = sub_df["is_fatal"].to_numpy(dtype=int)[m]
            p_m0 = sub_df["p_M0_conditions_only"].to_numpy(dtype=float)[m]
            p_m1 = sub_df["p_M1_plus_p_user"].to_numpy(dtype=float)[m]
            p_m2 = sub_df["p_M2_full_typology"].to_numpy(dtype=float)[m]
            subgroup_rows.append({
                "split": split_label,
                "subgroup": sg_code,
                "subgroup_label": sg_label,
                "n": int(len(y_sg)),
                "fatal": int(y_sg.sum()),
                "observed_fatality_rate_pct": round(float(y_sg.mean() * 100.0), 3),
                "m0_mean_pred_pct": round(float(p_m0.mean() * 100.0), 3),
                "m1_mean_pred_pct": round(float(p_m1.mean() * 100.0), 3),
                "m2_mean_pred_pct": round(float(p_m2.mean() * 100.0), 3),
                "m0_roc_auc": round(float(roc_auc_score(y_sg, p_m0)), 4) if len(np.unique(y_sg)) == 2 else np.nan,
                "m2_roc_auc": round(float(roc_auc_score(y_sg, p_m2)), 4) if len(np.unique(y_sg)) == 2 else np.nan,
                "m0_pr_auc": round(float(average_precision_score(y_sg, p_m0)), 4) if len(np.unique(y_sg)) == 2 else np.nan,
                "m2_pr_auc": round(float(average_precision_score(y_sg, p_m2)), 4) if len(np.unique(y_sg)) == 2 else np.nan,
                "m0_log_loss": round(float(log_loss(y_sg, p_m0, labels=[0, 1])), 5),
                "m2_log_loss": round(float(log_loss(y_sg, p_m2, labels=[0, 1])), 5),
            })
    subgroup_df = pd.DataFrame(subgroup_rows)
    subgroup_df.to_csv(tables_dir / "typology_subgroup_performance.csv", index=False)

    render_figures(summary_df, fold_df, or_df, subgroup_df, figures_dir)

    test_m0 = summary_df[(summary_df["split"] == "test_2020_2021_uncal") & (summary_df["model"] == "M0_conditions_only")].iloc[0]
    test_m1 = summary_df[(summary_df["split"] == "test_2020_2021_uncal") & (summary_df["model"] == "M1_plus_p_user")].iloc[0]
    test_m2 = summary_df[(summary_df["split"] == "test_2020_2021_uncal") & (summary_df["model"] == "M2_full_typology")].iloc[0]

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 2: Incorporate Road-User (P_USER) & Vehicle (V_TYPE) Typologies",
        "total_collisions": int(len(df)),
        "fatal_collisions": int(y.sum()),
        "test_2020_2021_comparison": {
            "M0_conditions_only": {
                "roc_auc": round(float(test_m0["roc_auc"]), 4),
                "pr_auc": round(float(test_m0["pr_auc"]), 4),
                "log_loss": round(float(test_m0["log_loss"]), 5),
                "brier_score": round(float(test_m0["brier_score"]), 5),
            },
            "M1_plus_p_user": {
                "roc_auc": round(float(test_m1["roc_auc"]), 4),
                "pr_auc": round(float(test_m1["pr_auc"]), 4),
                "log_loss": round(float(test_m1["log_loss"]), 5),
                "brier_score": round(float(test_m1["brier_score"]), 5),
            },
            "M2_full_typology": {
                "roc_auc": round(float(test_m2["roc_auc"]), 4),
                "pr_auc": round(float(test_m2["pr_auc"]), 4),
                "log_loss": round(float(test_m2["log_loss"]), 5),
                "brier_score": round(float(test_m2["brier_score"]), 5),
            },
        },
        "top_adjusted_odds_ratios": or_df.head(8).to_dict(orient="records"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["test_2020_2021_comparison"], indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    run(args.root, workers=args.workers, rebuild=args.rebuild)
