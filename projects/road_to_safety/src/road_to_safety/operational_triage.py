"""Phase 3: Operational Threshold Tuning, Cost-Utility Curves & Tiered Triage.

Moves beyond the flat 80% validation recall heuristic by evaluating:
  1. Cost-Utility & Vickers-Elkin Net Benefit curves across FN:FP cost ratios (5:1 to 100:1)
     comparing M0 (Conditions Only) vs M2 (Full Road-User + Vehicle Typology, uncalibrated & recalibrated).
  2. A 3-Tier Operational Triage Architecture (Tier 1 Critical Dispatch, Tier 2 Priority Response,
     Tier 3 Systemic VRU/Corridor Screening) calibrated on 2017-2019 validation data and evaluated
     out-of-time on 2020-2021 test data.
  3. Context-specific operating curves for Non-Intersection Uncontrolled or Freight Scenario vs.
     Urban Intersection & Vulnerable Road User (VRU) Traffic Calming.

Retrospective Scope & Operational Boundary Note:
  Subgroup analyses such as 'non_intersection_uncontrolled_or_freight' represent retrospective
  research evaluation scenarios, NOT an operational dispatch protocol. Predictors like
  post-crash roadway alignment (C_RALN), configuration (C_RCFG), and involved vehicle typologies
  are ascertained post-investigation and are not proven to be available at emergency call intake.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score

from .explore import sha256
from .fit_severity import validation_threshold

PROJECT_ROOT = Path(__file__).resolve().parents[2]

COST_RATIOS = [5, 10, 15, 20, 25, 35, 50, 75, 100]


def threshold_metrics(y: np.ndarray, p: np.ndarray, threshold: float, cost_ratio: float = 25.0) -> dict:
    y = np.asarray(y, dtype=int)
    p = np.asarray(p, dtype=float)
    pred = p >= threshold
    n = len(y)
    pos = int(y.sum())
    tp = int(np.sum((pred == 1) & (y == 1)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    tn = int(np.sum((pred == 0) & (y == 0)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / pos if pos > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    alert_rate = (tp + fp) / n if n > 0 else 0.0
    fp_per_tp = fp / tp if tp > 0 else np.nan
    nne = 1.0 / precision if precision > 0 else np.nan

    # Vickers-Elkin Net Benefit (in true-positive equivalents per collision, scaled per 10,000 collisions)
    # exchange weight w = 1 / cost_ratio = p_t / (1 - p_t)
    w = 1.0 / cost_ratio
    net_benefit_per_10k = ((tp / n) - w * (fp / n)) * 10000.0
    treat_all_nb_per_10k = ((pos / n) - w * ((n - pos) / n)) * 10000.0
    expected_cost_per_1k = ((cost_ratio * fn + 1.0 * fp) / n) * 1000.0
    no_action_cost_per_1k = ((cost_ratio * pos) / n) * 1000.0
    cost_reduction_pct = (
        100.0 * (no_action_cost_per_1k - expected_cost_per_1k) / no_action_cost_per_1k
        if no_action_cost_per_1k > 0
        else 0.0
    )

    return {
        "n": n,
        "fatal": pos,
        "threshold": round(float(threshold), 6),
        "cost_ratio_fn_fp": float(cost_ratio),
        "alert_count": tp + fp,
        "alert_rate_pct": round(alert_rate * 100.0, 3),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision_pct": round(precision * 100.0, 3),
        "recall_pct": round(recall * 100.0, 3),
        "f1_pct": round(f1 * 100.0, 3),
        "fp_per_tp": round(float(fp_per_tp), 2) if np.isfinite(fp_per_tp) else np.nan,
        "nne": round(float(nne), 2) if np.isfinite(nne) else np.nan,
        "net_benefit_per_10k": round(float(net_benefit_per_10k), 3),
        "treat_all_nb_per_10k": round(float(treat_all_nb_per_10k), 3),
        "expected_cost_per_1k": round(float(expected_cost_per_1k), 3),
        "cost_reduction_vs_none_pct": round(float(cost_reduction_pct), 2),
    }


def optimize_validation_threshold_for_cost(y_val: np.ndarray, p_val: np.ndarray, cost_ratio: float) -> float:
    """Find empirical threshold on validation set minimizing C_FN * FN + C_FP * FP."""
    candidates = np.quantile(p_val, np.linspace(0.005, 0.995, 400))
    candidates = np.unique(np.r_[candidates, 1.0 / (1.0 + cost_ratio)])
    pos = int(y_val.sum())
    best_cost = float("inf")
    best_tau = float(1.0 / (1.0 + cost_ratio))
    for tau in candidates:
        pred = p_val >= tau
        tp = int(np.sum((pred == 1) & (y_val == 1)))
        fp = int(np.sum((pred == 1) & (y_val == 0)))
        fn = pos - tp
        cost = cost_ratio * fn + fp
        if cost < best_cost:
            best_cost = cost
            best_tau = float(tau)
    return best_tau


def render_figures(
    cost_df: pd.DataFrame,
    tiers_df: pd.DataFrame,
    context_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    figures_dir: Path,
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    # Figure 1: Cost-Utility / Net Benefit Curve & Precision-Recall Operating Points on Test (2020-2021)
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4), layout="constrained")

    y_test = test_df["is_fatal"].to_numpy(dtype=int)
    p_m0 = test_df["p_M0_conditions_only"].to_numpy(dtype=float)
    p_m2 = test_df["p_M2_full_typology_recal"].to_numpy(dtype=float)

    prec_m0, rec_m0, _ = precision_recall_curve(y_test, p_m0)
    prec_m2, rec_m2, _ = precision_recall_curve(y_test, p_m2)

    axes[0].plot(rec_m0 * 100.0, prec_m0 * 100.0, color="#6b7280", linewidth=2.0, label="M0 Conditions Only")
    axes[0].plot(rec_m2 * 100.0, prec_m2 * 100.0, color="#dc2626", linewidth=2.2, label="M2 Full Typology (Recalibrated)")

    # Overlay legacy 80% recall point vs Tier 1, Tier 2, Tier 3 points on M2
    legacy_row = tiers_df[(tiers_df["split"] == "test_2020_2021") & (tiers_df["tier_id"] == "Legacy_80pct_Recall_M0")].iloc[0]
    axes[0].scatter(
        [legacy_row["recall_pct"]],
        [legacy_row["precision_pct"]],
        color="#111827",
        marker="X",
        s=95,
        zorder=5,
        label=f"Legacy 80% Recall M0 (Prec={legacy_row['precision_pct']:.1f}%, Alert={legacy_row['alert_rate_pct']:.1f}%)",
    )

    tier_Wait_colors = {
        "Tier_1_Critical_Dispatch": ("#7f1d1d", "^", "Tier 1 Critical (10:1)"),
        "Tier_2_Priority_Response": ("#d97706", "s", "Tier 2 Priority (25:1)"),
        "Tier_3_Systemic_Watchlist": ("#2563eb", "o", "Tier 3 Watchlist (50:1)"),
    }
    for tid, (tcol, tmk, tlbl) in tier_Wait_colors.items():
        r = tiers_df[(tiers_df["split"] == "test_2020_2021") & (tiers_df["tier_id"] == tid)].iloc[0]
        axes[0].scatter(
            [r["recall_pct"]],
            [r["precision_pct"]],
            color=tcol,
            marker=tmk,
            s=90,
            zorder=6,
            label=f"{tlbl}: Prec={r['precision_pct']:.1f}%, Rec={r['recall_pct']:.1f}%",
        )

    axes[0].set_xlim(0, 100)
    axes[0].set_ylim(0, 25)
    axes[0].set_xlabel("Fatal Collision Recall (%)")
    axes[0].set_ylabel("Precision / Positive Predictive Value (%)")
    axes[0].set_title("A. Precision-Recall Curve & 3-Tier Operating Points (Test 2020–2021)")
    axes[0].legend(fontsize=8, loc="upper right")
    axes[0].grid(alpha=0.25)

    # Panel B: Vickers-Elkin Net Benefit across Cost Ratios (5:1 to 100:1)
    c_test = cost_df[cost_df["split"] == "test_2020_2021"]
    for m_name, m_lbl, m_col, ls in [
        ("M0_conditions_only", "M0 Conditions Only (Empirical Val Threshold)", "#6b7280", "--"),
        ("M_intake_recal", "M_intake (Call Intake Recalibrated)", "#059669", ":"),
        ("M2_full_typology", "M2 Full Typology (Uncalibrated)", "#2563eb", "-."),
        ("M2_full_typology_recal", "M2 Full Typology (2019 Intercept Recalibrated)", "#dc2626", "-"),
    ]:
        sub = c_test[c_test["model"] == m_name].sort_values("cost_ratio_fn_fp")
        axes[1].plot(
            sub["cost_ratio_fn_fp"],
            sub["net_benefit_per_10k"],
            marker="o",
            linewidth=2.0,
            linestyle=ls,
            color=m_col,
            label=m_lbl,
        )

    axes[1].axhline(0.0, color="#111827", linestyle=":", linewidth=1.0, label="Treat None (Net Benefit = 0)")
    axes[1].set_xlabel("False-Negative to False-Positive Cost Ratio ($C_{FN} : C_{FP}$)")
    axes[1].set_ylabel("Net Benefit per 10,000 Collisions (True-Fatal Equivalents)")
    axes[1].set_title("B. Decision Curve Net Benefit Across Cost Ratios (Test 2020–2021)")
    axes[1].legend(fontsize=8, loc="upper left")
    axes[1].grid(alpha=0.25)

    fig.suptitle(
        "Phase 3: Cost-Utility Decision Curves & 3-Tier Operational Triage Architecture",
        fontsize=12,
        fontweight="bold",
    )
    fig.savefig(figures_dir / "triage_cost_utility_and_pr.png", dpi=180)
    plt.close(fig)

    # Figure 2: Context-Specific Operating Curves (Non-Intersection Uncontrolled/Freight vs Urban VRU Traffic Calming)
    fig, axes = plt.subplots(1, 2, figsize=(13.2, 5.2), layout="constrained")
    ctx_test = context_df[context_df["split"] == "test_2020_2021"].copy()

    for idx, (ctx_code, ctx_title) in enumerate([
        ("non_intersection_uncontrolled_or_freight", "A. Non-Intersection Uncontrolled or Freight Scenario (Research)"),
        ("urban_intersection_vru", "B. Urban Intersection & VRU Traffic Calming Context"),
    ]):
        sub = ctx_test[ctx_test["context"] == ctx_code].sort_values("cost_ratio_fn_fp")
        ax = axes[idx]
        ax.plot(
            sub["alert_rate_pct"],
            sub["recall_pct"],
            marker="o",
            linewidth=2.2,
            color="#dc2626",
            label="Fatal Recall (%)",
        )
        ax.plot(
            sub["alert_rate_pct"],
            sub["precision_pct"],
            marker="s",
            linewidth=2.0,
            color="#2563eb",
            label="Precision / PPV (%)",
        )
        for row in sub.itertuples():
            if int(row.cost_ratio_fn_fp) in (10, 25, 50):
                ax.annotate(
                    f"{int(row.cost_ratio_fn_fp)}:1\n(Prec={row.precision_pct:.1f}%, Rec={row.recall_pct:.1f}%)",
                    (row.alert_rate_pct, row.recall_pct),
                    xytext=(6, -14),
                    textcoords="offset points",
                    fontsize=7.8,
                )
        ax.set_xlabel("Share of Context Collisions Flagged / Dispatched (%)")
        ax.set_ylabel("Metric (%)")
        ax.set_title(ctx_title)
        ax.legend(fontsize=8.5, loc="center right")
        ax.grid(alpha=0.25)

    fig.suptitle(
        "Phase 3: Context-Specific Operational Triage Curves (Test 2020–2021, M2 Full Typology)",
        fontsize=12,
        fontweight="bold",
    )
    fig.savefig(figures_dir / "triage_context_operating_curves.png", dpi=180)
    plt.close(fig)


def run(root: Path | None = None) -> dict:
    root = (root or PROJECT_ROOT).resolve()
    pred_parquet = root / "data/derived/typology_severity/eval_predictions_2017_2021.parquet"
    if not pred_parquet.exists():
        raise FileNotFoundError(f"Missing Phase 2 predictions at {pred_parquet}; run typology_severity first.")

    out_dir = root / "data/derived/operational_triage"
    tables_dir = root / "reports/tables"
    figures_dir = root / "reports/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    df = con.execute(f"SELECT * FROM read_parquet('{pred_parquet.as_posix()}')").df()
    con.close()

    val_df = df[df["split"] == "validation"].copy().reset_index(drop=True)
    test_df = df[df["split"] == "test"].copy().reset_index(drop=True)

    y_val = val_df["is_fatal"].to_numpy(dtype=int)
    y_test = test_df["is_fatal"].to_numpy(dtype=int)

    # 1. Evaluate Cost-Utility Curves across cost ratios on Validation (2017-2019) & Test (2020-2021)
    cost_rows = []
    for model_col, model_name in [
        ("p_M0_conditions_only", "M0_conditions_only"),
        ("p_M_intake", "M_intake"),
        ("p_M_intake_recal", "M_intake_recal"),
        ("p_M2_full_typology", "M2_full_typology"),
        ("p_M2_full_typology_recal", "M2_full_typology_recal"),
    ]:
        p_val = val_df[model_col].to_numpy(dtype=float)
        p_test = test_df[model_col].to_numpy(dtype=float)
        for r in COST_RATIOS:
            tau_opt = optimize_validation_threshold_for_cost(y_val, p_val, cost_ratio=float(r))
            tau_bayes = 1.0 / (1.0 + float(r))
            cost_rows.append({
                "split": "validation_2017_2019",
                "model": model_name,
                "threshold_policy": "empirical_val_cost_min",
                "theoretical_bayes_threshold": round(tau_bayes, 6),
                **threshold_metrics(y_val, p_val, tau_opt, cost_ratio=float(r)),
            })
            cost_rows.append({
                "split": "test_2020_2021",
                "model": model_name,
                "threshold_policy": "empirical_val_cost_min",
                "theoretical_bayes_threshold": round(tau_bayes, 6),
                **threshold_metrics(y_test, p_test, tau_opt, cost_ratio=float(r)),
            })

    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(tables_dir / "triage_cost_utility_curves.csv", index=False)

    # 2. Define 3-Tier Operational Triage Architecture vs Legacy Flat 80% Recall Heuristic
    tau_legacy_m0 = validation_threshold(y_val, val_df["p_M0_conditions_only"].to_numpy(dtype=float), target=0.80)
    tau_legacy_m2 = validation_threshold(y_val, val_df["p_M2_full_typology_recal"].to_numpy(dtype=float), target=0.80)

    p_val_m2 = val_df["p_M2_full_typology_recal"].to_numpy(dtype=float)
    p_test_m2 = test_df["p_M2_full_typology_recal"].to_numpy(dtype=float)

    tau_tier1 = optimize_validation_threshold_for_cost(y_val, p_val_m2, cost_ratio=10.0)
    tau_tier2 = optimize_validation_threshold_for_cost(y_val, p_val_m2, cost_ratio=25.0)
    tau_tier3 = optimize_validation_threshold_for_cost(y_val, p_val_m2, cost_ratio=50.0)

    tier_specs = [
        (
            "Legacy_80pct_Recall_M0",
            "Legacy Flat 80% Recall (M0 Conditions Only)",
            "M0_conditions_only",
            "p_M0_conditions_only",
            tau_legacy_m0,
            50.0,
            "Unchanged baseline heuristic from initial severity protocol",
        ),
        (
            "Legacy_80pct_Recall_M2",
            "Flat 80% Recall with M2 Full Typology",
            "M2_full_typology_recal",
            "p_M2_full_typology_recal",
            tau_legacy_m2,
            50.0,
            "Same 80% recall constraint but using road-user + vehicle typologies",
        ),
        (
            "Tier_1_Critical_Dispatch",
            "Tier 1: Critical Trauma / Air-Ground Dispatch (10:1 Cost Ratio)",
            "M2_full_typology_recal",
            "p_M2_full_typology_recal",
            tau_tier1,
            10.0,
            "Immediate trauma center pre-alert & air/ALS dispatch for highest lethality collisions",
        ),
        (
            "Tier_2_Priority_Response",
            "Tier 2: Priority Field Response & Traffic Control (25:1 Cost Ratio)",
            "M2_full_typology_recal",
            "p_M2_full_typology_recal",
            tau_tier2,
            25.0,
            "Priority police/EMS dispatch & speed enforcement targeting high-severity corridors",
        ),
        (
            "Tier_3_Systemic_Watchlist",
            "Tier 3: Systemic Engineering & VRU Corridor Watchlist (50:1 Cost Ratio)",
            "M2_full_typology_recal",
            "p_M2_full_typology_recal",
            tau_tier3,
            50.0,
            "Network screening for traffic calming, protected signal phases & road safety audits",
        ),
    ]

    tier_rows = []
    for tid, tlabel, mname, col, tau, cr, use_case in tier_specs:
        for split_name, s_df, y_arr in [
            ("validation_2017_2019", val_df, y_val),
            ("test_2020_2021", test_df, y_test),
        ]:
            m = threshold_metrics(y_arr, s_df[col].to_numpy(dtype=float), tau, cost_ratio=cr)
            tier_rows.append({
                "split": split_name,
                "tier_id": tid,
                "tier_label": tlabel,
                "model": mname,
                "operational_use_case": use_case,
                **m,
            })

    # Also compute mutually exclusive band distribution on Test 2020-2021 for M2
    band_labels = np.select(
        [
            p_test_m2 >= tau_tier1,
            (p_test_m2 >= tau_tier2) & (p_test_m2 < tau_tier1),
            (p_test_m2 >= tau_tier3) & (p_test_m2 < tau_tier2),
        ],
        [
            "Band_1_Critical_gte_T1",
            "Band_2_Priority_T2_to_T1",
            "Band_3_Watchlist_T3_to_T2",
        ],
        default="Band_4_Routine_lt_T3",
    )
    band_rows = []
    for b_code in [
        "Band_1_Critical_gte_T1",
        "Band_2_Priority_T2_to_T1",
        "Band_3_Watchlist_T3_to_T2",
        "Band_4_Routine_lt_T3",
    ]:
        bm = band_labels == b_code
        bn = int(bm.sum())
        bfat = int(y_test[bm].sum())
        band_rows.append({
            "band": b_code,
            "collisions": bn,
            "share_of_all_collisions_pct": round(100.0 * bn / len(y_test), 3),
            "fatal_collisions": bfat,
            "share_of_all_fatals_pct": round(100.0 * bfat / int(y_test.sum()), 3),
            "within_band_fatality_rate_pct": round(100.0 * bfat / bn, 3) if bn > 0 else 0.0,
            "relative_risk_vs_routine": 0.0,
        })
    routine_rate = band_rows[-1]["within_band_fatality_rate_pct"]
    for r in band_rows:
        r["relative_risk_vs_routine"] = round(
            r["within_band_fatality_rate_pct"] / routine_rate, 2
        ) if routine_rate > 0 else np.nan
    band_df = pd.DataFrame(band_rows)
    band_df.to_csv(tables_dir / "triage_mutually_exclusive_bands.csv", index=False)

    tiers_df = pd.DataFrame(tier_rows)
    tiers_df.to_csv(tables_dir / "triage_tiered_operating_points.csv", index=False)

    # 2b. Emergency Call Intake Model (M_intake) vs. Post-Investigation Model (M_post / M2_full_typology)
    p_val_intake = val_df["p_M_intake_recal"].to_numpy(dtype=float)
    p_test_intake = test_df["p_M_intake_recal"].to_numpy(dtype=float)

    tau_intake_tier1 = optimize_validation_threshold_for_cost(y_val, p_val_intake, cost_ratio=10.0)
    tau_intake_tier2 = optimize_validation_threshold_for_cost(y_val, p_val_intake, cost_ratio=25.0)
    tau_intake_tier3 = optimize_validation_threshold_for_cost(y_val, p_val_intake, cost_ratio=50.0)

    # Routine baseline rate definition (collisions below Tier 3 threshold)
    def calc_routine_rate(y_arr: np.ndarray, p_arr: np.ndarray, tau: float) -> float:
        mask = p_arr < tau
        return float(y_arr[mask].mean()) if np.any(mask) else float(y_arr.mean())

    rout_val_m2 = calc_routine_rate(y_val, p_val_m2, tau_tier3)
    rout_test_m2 = calc_routine_rate(y_test, p_test_m2, tau_tier3)

    rout_val_intake_fixed = calc_routine_rate(y_val, p_val_intake, tau_tier3)
    rout_test_intake_fixed = calc_routine_rate(y_test, p_test_intake, tau_tier3)

    rout_val_intake_tuned = calc_routine_rate(y_val, p_val_intake, tau_intake_tier3)
    rout_test_intake_tuned = calc_routine_rate(y_test, p_test_intake, tau_intake_tier3)

    intake_vs_post_rows = []
    tiers_info = [
        ("Tier_1_Critical_Dispatch", "Tier 1: Critical Triage (10:1)", 10.0, tau_tier1, tau_intake_tier1),
        ("Tier_2_Priority_Response", "Tier 2: Priority Response (25:1)", 25.0, tau_tier2, tau_intake_tier2),
        ("Tier_3_Systemic_Watchlist", "Tier 3: Systemic Watchlist (50:1)", 50.0, tau_tier3, tau_intake_tier3),
    ]

    for split_name, y_arr, p_m2_arr, p_in_arr, r_m2, r_if, r_it in [
        ("validation_2017_2019", y_val, p_val_m2, p_val_intake, rout_val_m2, rout_val_intake_fixed, rout_val_intake_tuned),
        ("test_2020_2021", y_test, p_test_m2, p_test_intake, rout_test_m2, rout_test_intake_fixed, rout_test_intake_tuned),
    ]:
        for tid, tlbl, cr, tau_post, tau_in_tuned in tiers_info:
            m_post = threshold_metrics(y_arr, p_m2_arr, tau_post, cost_ratio=cr)
            m_in_fixed = threshold_metrics(y_arr, p_in_arr, tau_post, cost_ratio=cr)
            m_in_tuned = threshold_metrics(y_arr, p_in_arr, tau_in_tuned, cost_ratio=cr)

            rr_post = round((m_post["precision_pct"] / 100.0) / r_m2, 2) if r_m2 > 0 else np.nan
            rr_in_fixed = round((m_in_fixed["precision_pct"] / 100.0) / r_if, 2) if r_if > 0 else np.nan
            rr_in_tuned = round((m_in_tuned["precision_pct"] / 100.0) / r_it, 2) if r_it > 0 else np.nan

            intake_vs_post_rows.append({
                "split": split_name,
                "tier_id": tid,
                "tier_label": tlbl,
                "cost_ratio_fn_fp": cr,
                "model": "M_post_recal",
                "threshold_policy": "m_post_validation_cost_optimal",
                "threshold": m_post["threshold"],
                "alert_count": m_post["alert_count"],
                "alert_rate_pct": m_post["alert_rate_pct"],
                "tp": m_post["tp"],
                "fp": m_post["fp"],
                "fn": m_post["fn"],
                "tn": m_post["tn"],
                "precision_pct": m_post["precision_pct"],
                "recall_pct": m_post["recall_pct"],
                "f1_pct": m_post["f1_pct"],
                "fp_per_tp": m_post["fp_per_tp"],
                "relative_risk_vs_routine": rr_post,
                "net_benefit_per_10k": m_post["net_benefit_per_10k"],
                "delta_precision_vs_post_pp": 0.0,
                "delta_recall_vs_post_pp": 0.0,
                "delta_alert_rate_vs_post_pp": 0.0,
                "alert_volume_ratio_vs_post": 1.0,
            })
            intake_vs_post_rows.append({
                "split": split_name,
                "tier_id": tid,
                "tier_label": tlbl,
                "cost_ratio_fn_fp": cr,
                "model": "M_intake_recal",
                "threshold_policy": "evaluated_at_m_post_cutoff",
                "threshold": m_in_fixed["threshold"],
                "alert_count": m_in_fixed["alert_count"],
                "alert_rate_pct": m_in_fixed["alert_rate_pct"],
                "tp": m_in_fixed["tp"],
                "fp": m_in_fixed["fp"],
                "fn": m_in_fixed["fn"],
                "tn": m_in_fixed["tn"],
                "precision_pct": m_in_fixed["precision_pct"],
                "recall_pct": m_in_fixed["recall_pct"],
                "f1_pct": m_in_fixed["f1_pct"],
                "fp_per_tp": m_in_fixed["fp_per_tp"],
                "relative_risk_vs_routine": rr_in_fixed,
                "net_benefit_per_10k": m_in_fixed["net_benefit_per_10k"],
                "delta_precision_vs_post_pp": round(m_in_fixed["precision_pct"] - m_post["precision_pct"], 3),
                "delta_recall_vs_post_pp": round(m_in_fixed["recall_pct"] - m_post["recall_pct"], 3),
                "delta_alert_rate_vs_post_pp": round(m_in_fixed["alert_rate_pct"] - m_post["alert_rate_pct"], 3),
                "alert_volume_ratio_vs_post": round(m_in_fixed["alert_count"] / m_post["alert_count"], 3) if m_post["alert_count"] > 0 else np.nan,
            })
            intake_vs_post_rows.append({
                "split": split_name,
                "tier_id": tid,
                "tier_label": tlbl,
                "cost_ratio_fn_fp": cr,
                "model": "M_intake_recal",
                "threshold_policy": "m_intake_separately_tuned_validation_cost_optimal",
                "threshold": m_in_tuned["threshold"],
                "alert_count": m_in_tuned["alert_count"],
                "alert_rate_pct": m_in_tuned["alert_rate_pct"],
                "tp": m_in_tuned["tp"],
                "fp": m_in_tuned["fp"],
                "fn": m_in_tuned["fn"],
                "tn": m_in_tuned["tn"],
                "precision_pct": m_in_tuned["precision_pct"],
                "recall_pct": m_in_tuned["recall_pct"],
                "f1_pct": m_in_tuned["f1_pct"],
                "fp_per_tp": m_in_tuned["fp_per_tp"],
                "relative_risk_vs_routine": rr_in_tuned,
                "net_benefit_per_10k": m_in_tuned["net_benefit_per_10k"],
                "delta_precision_vs_post_pp": round(m_in_tuned["precision_pct"] - m_post["precision_pct"], 3),
                "delta_recall_vs_post_pp": round(m_in_tuned["recall_pct"] - m_post["recall_pct"], 3),
                "delta_alert_rate_vs_post_pp": round(m_in_tuned["alert_rate_pct"] - m_post["alert_rate_pct"], 3),
                "alert_volume_ratio_vs_post": round(m_in_tuned["alert_count"] / m_post["alert_count"], 3) if m_post["alert_count"] > 0 else np.nan,
            })

    intake_vs_post_df = pd.DataFrame(intake_vs_post_rows)
    intake_vs_post_df.to_csv(tables_dir / "triage_intake_vs_post_comparison.csv", index=False)

    # 3. Context-Specific Operating Curves:
    #    Context A: Non-Intersection Uncontrolled or Freight Scenario (Retrospective Research Scenario)
    #    Context B: Urban Intersection & Vulnerable Road User (VRU) Traffic Calming
    # Note: Subgroup A is constructed from non-intersection (C_RCFG='1'), uncontrolled (C_TRAF='18'),
    # roadway alignment (C_RALN), and freight typologies. This is a retrospective research scenario,
    # NOT an operational dispatch protocol; these features are not proven to be available at emergency intake.
    def get_context_masks(d: pd.DataFrame) -> dict[str, np.ndarray]:
        non_intersection_freight_uncontrolled = (
            d["C_RCFG"].eq("1")
            & (
                d["C_TRAF"].eq("18")
                | d["C_RALN"].isin(["2", "3", "4", "5", "6"])
                | d["has_heavy_freight"].eq(1)
            )
        ).to_numpy()
        urban_vru = (
            d["C_RCFG"].isin(["2", "3"])
            | d["has_vru"].eq(1)
        ).to_numpy()
        return {
            "non_intersection_uncontrolled_or_freight": non_intersection_freight_uncontrolled,
            "urban_intersection_vru": urban_vru,
        }

    val_ctx = get_context_masks(val_df)
    test_ctx = get_context_masks(test_df)

    context_rows = []
    for ctx_code in ["non_intersection_uncontrolled_or_freight", "urban_intersection_vru"]:
        vm = val_ctx[ctx_code]
        tm = test_ctx[ctx_code]
        for r in [5, 10, 15, 20, 25, 35, 50, 75]:
            tau_ctx = optimize_validation_threshold_for_cost(
                y_val[vm], p_val_m2[vm], cost_ratio=float(r)
            )
            context_rows.append({
                "split": "validation_2017_2019",
                "context": ctx_code,
                **threshold_metrics(y_val[vm], p_val_m2[vm], tau_ctx, cost_ratio=float(r)),
            })
            context_rows.append({
                "split": "test_2020_2021",
                "context": ctx_code,
                **threshold_metrics(y_test[tm], p_test_m2[tm], tau_ctx, cost_ratio=float(r)),
            })
    context_df = pd.DataFrame(context_rows)
    context_df.to_csv(tables_dir / "triage_context_specific_curves.csv", index=False)

    render_figures(cost_df, tiers_df, context_df, val_df, test_df, figures_dir)

    roc_post = float(roc_auc_score(y_test, p_test_m2))
    pr_post = float(average_precision_score(y_test, p_test_m2))
    roc_intake = float(roc_auc_score(y_test, p_test_intake))
    pr_intake = float(average_precision_score(y_test, p_test_intake))

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 3: Operational Threshold Tuning & Tiered Triage",
        "test_2020_2021_tiered_summary": tiers_df[tiers_df["split"] == "test_2020_2021"].to_dict(orient="records"),
        "mutually_exclusive_bands_test_2020_2021": band_rows,
        "intake_vs_post_comparison": {
            "test_2020_2021_discrimination": {
                "m_post": {"roc_auc": round(roc_post, 4), "pr_auc": round(pr_post, 4)},
                "m_intake": {"roc_auc": round(roc_intake, 4), "pr_auc": round(pr_intake, 4)},
                "drop_roc_auc": round(roc_post - roc_intake, 4),
                "drop_pr_auc_pp": round((pr_post - pr_intake) * 100.0, 2),
                "relative_pr_auc_loss_pct": round(100.0 * (pr_post - pr_intake) / pr_post, 2),
            },
            "tiers_comparison": intake_vs_post_df[intake_vs_post_df["split"] == "test_2020_2021"].to_dict(orient="records"),
        },
    }
    (out_dir / "triage_evaluation.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(band_rows, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    run(args.root)
