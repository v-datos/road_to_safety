"""Phase 1: Corridor-Level Pilot Linkage (Spatial + Exposure) & Crash/VKT Modeling.

Links City of Toronto KSI collisions (2006-2023) to Toronto Centreline road segments
and Short-Term Volume Count (SVC) AADT exposure studies to estimate true accident
occurrence rates (Crash / 100M VKT), Poisson/Negative Binomial Safety Performance
Functions (SPFs), and Empirical Bayes (EB) corridor risk rankings. Also profiles
Province of Quebec MTQ highway AADT sections as a provincial exposure comparator.

Run from the project root:
    MPLCONFIGDIR=/tmp/mpl .venv/bin/python -m road_to_safety.corridor_pilot
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.special import gammaln

ROAD_CLASSES = {
    "Major Arterial",
    "Minor Arterial",
    "Collector",
    "Local",
    "Expressway",
    "Expressway Ramp",
    "Major Arterial Ramp",
    "Laneway",
    "Collector Ramp",
    "Minor Arterial Ramp",
    "Other Ramp",
    "Access Road",
    "Busway",
    "Pending",
    "Other",
}

MAIN_ROAD_CLASSES = [
    "Expressway",
    "Major Arterial",
    "Minor Arterial",
    "Collector",
    "Local",
]

LAT0_RAD = np.deg2rad(43.70)
M_PER_DEG_LAT = 111132.92 - 559.82 * np.cos(2.0 * LAT0_RAD) + 1.175 * np.cos(4.0 * LAT0_RAD)
M_PER_DEG_LON = 111412.84 * np.cos(LAT0_RAD) - 93.5 * np.cos(3.0 * LAT0_RAD)
STUDY_YEARS = 18.0  # 2006..2023 inclusive


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def to_xy_meters(lon: np.ndarray | float, lat: np.ndarray | float) -> tuple[np.ndarray, np.ndarray]:
    """Project WGS84 lon/lat to local tangent plane meters centered at Toronto."""
    x = (np.asarray(lon, dtype=float) - (-79.40)) * M_PER_DEG_LON
    y = (np.asarray(lat, dtype=float) - 43.70) * M_PER_DEG_LAT
    return x, y


def normalize_street_name(name: str) -> str:
    """Normalize street names for hybrid spatial + lexical road matching."""
    if not name:
        return ""
    s = str(name).upper().strip()
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    replacements = {
        " AVENUE": " AVE",
        " STREET": " ST",
        " ROAD": " RD",
        " DRIVE": " DR",
        " BOULEVARD": " BLVD",
        " PARKWAY": " PKWY",
        " CRESCENT": " CRES",
        " COURT": " CRT",
        " PLACE": " PL",
        " TERRACE": " TER",
        " TRAIL": " TRL",
        " HIGHWAY": " HWY",
        " EAST": " E",
        " WEST": " W",
        " NORTH": " N",
        " SOUTH": " S",
    }
    for old, new in replacements.items():
        if s.endswith(old):
            s = s[: -len(old)] + new
        s = s.replace(old + " ", new + " ")
    return re.sub(r"\s+", " ", s).strip()


def extract_segment_geometry(roads: pd.DataFrame):
    """Parse GeoJSON polylines, compute exact metric lengths, and build dense KDTree."""
    pts_x, pts_y, pts_seg_idx = [], [], []
    seg_Polylines = []
    seg_lengths_m = np.zeros(len(roads), dtype=float)
    centroid_lon = np.zeros(len(roads), dtype=float)
    centroid_lat = np.zeros(len(roads), dtype=float)

    for idx, geom_str in enumerate(roads["geometry"]):
        g = json.loads(geom_str)
        lines = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"]
        total_len = 0.0
        seg_chunks = []
        all_lons, all_lats = [], []
        for line in lines:
            arr = np.asarray(line, dtype=float)
            all_lons.extend(arr[:, 0])
            all_lats.extend(arr[:, 1])
            xs, ys = to_xy_meters(arr[:, 0], arr[:, 1])
            dx = np.diff(xs)
            dy = np.diff(ys)
            d = np.hypot(dx, dy)
            total_len += float(d.sum())
            seg_chunks.append((xs, ys))
            # Sample vertices, midpoints, and quarter-points for KDTree candidate index
            pts_x.extend(xs)
            pts_y.extend(ys)
            pts_seg_idx.extend([idx] * len(xs))
            for frac in (0.25, 0.50, 0.75):
                qx = xs[:-1] + frac * dx
                qy = ys[:-1] + frac * dy
                pts_x.extend(qx)
                pts_y.extend(qy)
                pts_seg_idx.extend([idx] * len(qx))
        seg_lengths_m[idx] = max(total_len, 1.0)
        seg_Polylines.append(seg_chunks)
        centroid_lon[idx] = float(np.mean(all_lons)) if all_lons else np.nan
        centroid_lat[idx] = float(np.mean(all_lats)) if all_lats else np.nan

    tree = cKDTree(np.column_stack([pts_x, pts_y]))
    return seg_lengths_m, centroid_lon, centroid_lat, seg_Polylines, tree, np.asarray(pts_seg_idx, dtype=int)


def point_to_polyline_dist(px: float, py: float, chunks: list[tuple[np.ndarray, np.ndarray]]) -> float:
    """Compute exact perpendicular distance (meters) from point (px, py) to polyline chunks."""
    best = float("inf")
    for xs, ys in chunks:
        x1, y1 = xs[:-1], ys[:-1]
        x2, y2 = xs[1:], ys[1:]
        dx = x2 - x1
        dy = y2 - y1
        denom = dx * dx + dy * dy
        t = np.where(denom > 1e-12, ((px - x1) * dx + (py - y1) * dy) / np.where(denom > 1e-12, denom, 1.0), 0.0)
        t = np.clip(t, 0.0, 1.0)
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        dist = float(np.min(np.hypot(px - proj_x, py - proj_y)))
        if dist < best:
            best = dist
    return best


def collapse_ksi_events(ksi_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse person-level Toronto KSI records to unique collision events."""
    yes = lambda s: s.astype(str).str.upper().str.strip().isin({"YES", "TRUE", "1"})
    agg = ksi_df.groupby("collision_id", sort=False).agg(
        accdate=("accdate", "first"),
        stname1=("stname1", "first"),
        stname2=("stname2", "first"),
        road_class=("road_class", "first"),
        acclass=("acclass", "first"),
        accloc=("accloc", "first"),
        traffictl=("traffictl", "first"),
        light=("light", "first"),
        rdsfcond=("rdsfcond", "first"),
        longitude=("longitude", "first"),
        latitude=("latitude", "first"),
        neighbourhood=("neighbourhood", "first"),
        person_rows=("_id", "size"),
        has_pedestrian=("pedestrian", lambda s: bool(yes(s).any())),
        has_cyclist=("cyclist", lambda s: bool(yes(s).any())),
        has_motorcyclist=("motorcyclist", lambda s: bool(yes(s).any())),
        has_heavy_truck=("heavy_truck", lambda s: bool(yes(s).any())),
        has_aggressive=("aggressive", lambda s: bool(yes(s).any())),
        has_red_light=("red_light", lambda s: bool(yes(s).any())),
    ).reset_index()
    agg["year"] = pd.to_datetime(agg["accdate"], errors="coerce").dt.year.astype(int)
    agg["is_fatal"] = agg["acclass"].eq("Fatal Injury").astype(int)
    agg["has_vru"] = (agg["has_pedestrian"] | agg["has_cyclist"] | agg["has_motorcyclist"]).astype(int)
    return agg


def snap_collisions_to_segments(
    events: pd.DataFrame,
    roads: pd.DataFrame,
    polylines: list,
    tree: cKDTree,
    pts_seg_idx: np.ndarray,
    max_dist_m: float = 50.0,
) -> pd.DataFrame:
    """Snap KSI events to nearest Centreline road segment using hybrid spatial + street name matching."""
    lon = pd.to_numeric(events["longitude"], errors="coerce").to_numpy()
    lat = pd.to_numeric(events["latitude"], errors="coerce").to_numpy()
    valid = np.isfinite(lon) & np.isfinite(lat)
    ex, ey = to_xy_meters(np.where(valid, lon, -79.40), np.where(valid, lat, 43.70))

    road_norm_full = roads["LINEAR_NAME_FULL"].map(normalize_street_name).to_numpy()
    road_norm_base = roads["LINEAR_NAME"].str.upper().str.strip().to_numpy()
    road_cls = roads["FEATURE_CODE_DESC"].to_numpy()
    road_ids = roads["CENTRELINE_ID"].to_numpy()

    st1_norm = events["stname1"].map(normalize_street_name).to_numpy()
    st2_norm = events["stname2"].map(normalize_street_name).to_numpy()
    ev_rclass = events["road_class"].to_numpy()

    dists, idxs = tree.query(np.column_stack([ex, ey]), k=30)

    matched_cid = []
    matched_dist = []
    match_type = []

    for i in range(len(events)):
        if not valid[i]:
            matched_cid.append(None)
            matched_dist.append(np.nan)
            match_type.append("missing_coordinates")
            continue

        cand_seg_indices = []
        seen = set()
        for pt_i in idxs[i]:
            s_idx = int(pts_seg_idx[pt_i])
            if s_idx not in seen:
                seen.add(s_idx)
                cand_seg_indices.append(s_idx)

        s1, s2 = st1_norm[i], st2_norm[i]
        rc = ev_rclass[i]
        px, py = float(ex[i]), float(ey[i])

        best_named_idx, best_named_d = None, float("inf")
        best_any_idx, best_any_d = None, float("inf")

        for s_idx in cand_seg_indices:
            d_perp = point_to_polyline_dist(px, py, polylines[s_idx])
            if d_perp < best_any_d:
                best_any_d = d_perp
                best_any_idx = s_idx

            r_full = road_norm_full[s_idx]
            r_base = road_norm_base[s_idx]
            name_hit = False
            if s1 and (s1 == r_full or (r_base and r_base in s1)):
                name_hit = True
            elif s2 and (s2 == r_full or (r_base and r_base in s2)):
                name_hit = True

            if name_hit and d_perp <= max_dist_m:
                # Slight bonus if road_class also agrees
                effective_d = d_perp - (2.0 if rc and rc == road_cls[s_idx] else 0.0)
                if effective_d < best_named_d:
                    best_named_d = effective_d
                    best_named_idx = s_idx

        if best_named_idx is not None:
            actual_d = point_to_polyline_dist(px, py, polylines[best_named_idx])
            matched_cid.append(road_ids[best_named_idx])
            matched_dist.append(round(actual_d, 3))
            match_type.append("spatial_and_name")
        elif best_any_idx is not None and best_any_d <= max_dist_m:
            matched_cid.append(road_ids[best_any_idx])
            matched_dist.append(round(best_any_d, 3))
            match_type.append("spatial_only")
        else:
            matched_cid.append(None)
            matched_dist.append(round(best_any_d, 3) if np.isfinite(best_any_d) else np.nan)
            match_type.append("outside_50m_buffer")

    out = events.copy()
    out["matched_centreline_id"] = matched_cid
    out["snap_distance_m"] = matched_dist
    out["match_quality"] = match_type
    return out


def aggregate_exposure_studies(svc_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate Toronto short-term traffic volume studies to unique Centreline road segments."""
    df = svc_df.copy()
    df["duration_h"] = pd.to_numeric(df["count_duration"], errors="coerce")
    df["daily_vol"] = pd.to_numeric(df["avg_daily_vol"], errors="coerce")
    df["wkdy_vol"] = pd.to_numeric(df["avg_weekday_daily_vol"], errors="coerce")
    df["wknd_vol"] = pd.to_numeric(df["avg_weekend_daily_vol"], errors="coerce")
    df["speed"] = pd.to_numeric(df["avg_speed"], errors="coerce")
    df["speed_85"] = pd.to_numeric(df["avg_85th_percentile_speed"], errors="coerce")
    df["heavy_pct"] = pd.to_numeric(df["avg_heavy_pct"], errors="coerce")
    df["year"] = pd.to_datetime(df["count_date_start"], errors="coerce").dt.year

    valid = df[df["daily_vol"].gt(0) & df["duration_h"].ge(24)].copy()
    grouped = valid.groupby("centreline_id", sort=False).agg(
        count_studies=("count_id", "size"),
        min_study_year=("year", "min"),
        max_study_year=("year", "max"),
        aadt=("daily_vol", "mean"),
        median_aadt=("daily_vol", "median"),
        weekday_vol=("wkdy_vol", "mean"),
        weekend_vol=("wknd_vol", "mean"),
        avg_speed_kmh=("speed", "mean"),
        avg_85th_speed_kmh=("speed_85", "mean"),
        avg_heavy_pct=("heavy_pct", "mean"),
    ).reset_index()
    return grouped


def fit_poisson_and_nb2_spf(seg_df: pd.DataFrame):
    """Fit Poisson GLM (with log-VKT offset) and Negative Binomial (NB2) SPF + Empirical Bayes."""
    df = seg_df[seg_df["exposure_100m_vkt"].gt(0) & seg_df["aadt"].gt(0)].copy().reset_index(drop=True)
    y = df["ksi_crashes"].to_numpy(dtype=float)
    exposure = df["exposure_100m_vkt"].to_numpy(dtype=float)
    log_exp = np.log(exposure)

    log_aadt_c = np.log(df["aadt"].to_numpy(dtype=float)) - np.mean(np.log(df["aadt"].to_numpy(dtype=float)))
    log_len_c = np.log(df["length_km"].to_numpy(dtype=float)) - np.mean(np.log(df["length_km"].to_numpy(dtype=float)))

    # Road class indicators (reference = Local / Other)
    is_major = df["FEATURE_CODE_DESC"].eq("Major Arterial").to_numpy(dtype=float)
    is_minor = df["FEATURE_CODE_DESC"].eq("Minor Arterial").to_numpy(dtype=float)
    is_collector = df["FEATURE_CODE_DESC"].eq("Collector").to_numpy(dtype=float)
    is_expressway = df["FEATURE_CODE_DESC"].isin(["Expressway", "Expressway Ramp"]).to_numpy(dtype=float)

    X = np.column_stack([
        np.ones(len(df)),
        log_aadt_c,
        log_len_c,
        is_major,
        is_minor,
        is_collector,
        is_expressway,
    ])
    feature_names = [
        "intercept_log_rate_per_100m_vkt",
        "log_aadt_centered",
        "log_length_km_centered",
        "class_major_arterial",
        "class_minor_arterial",
        "class_collector",
        "class_expressway",
    ]

    # 1. Poisson GLM with exact log_exp offset
    def poisson_nll(beta):
        eta = np.clip(log_exp + X @ beta, -20.0, 20.0)
        mu = np.exp(eta)
        return float(np.sum(mu - y * eta + gammaln(y + 1.0)))

    def poisson_grad(beta):
        eta = np.clip(log_exp + X @ beta, -20.0, 20.0)
        mu = np.exp(eta)
        return X.T @ (mu - y)

    init_beta = np.zeros(X.shape[1])
    init_beta[0] = np.log(max(y.sum() / exposure.sum(), 1e-4))
    res_pois = minimize(poisson_nll, init_beta, jac=poisson_grad, method="BFGS")
    beta_pois = res_pois.x
    mu_pois = np.exp(np.clip(log_exp + X @ beta_pois, -20.0, 20.0))

    # Standard errors from Fisher Information Matrix (X^T W X)^{-1}
    W_pois = mu_pois
    cov_pois = np.linalg.pinv(X.T @ (W_pois[:, None] * X))
    se_pois = np.sqrt(np.maximum(np.diag(cov_pois), 1e-12))

    # 2. Negative Binomial (NB2) MLE: Var(Y) = mu + alpha * mu^2
    def nb2_nll(params):
        beta = params[:-1]
        log_alpha = np.clip(params[-1], -8.0, 6.0)
        alpha = np.exp(log_alpha)
        r = 1.0 / alpha
        eta = np.clip(log_exp + X @ beta, -20.0, 20.0)
        mu = np.exp(eta)
        ll = (
            gammaln(y + r)
            - gammaln(r)
            - gammaln(y + 1.0)
            + r * np.log(r / (r + mu))
            + y * np.log(mu / (r + mu))
        )
        return float(-np.sum(ll))

    init_nb = np.append(beta_pois, np.log(1.0))
    res_nb = minimize(nb2_nll, init_nb, method="L-BFGS-B")
    beta_nb = res_nb.x[:-1]
    alpha_nb = float(np.exp(np.clip(res_nb.x[-1], -8.0, 6.0)))
    mu_nb = np.exp(np.clip(log_exp + X @ beta_nb, -20.0, 20.0))

    # NB2 Fisher Information standard errors: w_i = mu_i / (1 + alpha * mu_i)
    W_nb = mu_nb / (1.0 + alpha_nb * mu_nb)
    cov_nb = np.linalg.pinv(X.T @ (W_nb[:, None] * X))
    se_nb = np.sqrt(np.maximum(np.diag(cov_nb), 1e-12))

    # 3. Empirical Bayes (EB) shrinkage estimate
    # Weight on SPF prediction: w_i = 1 / (1 + alpha * mu_i)
    eb_weight = 1.0 / (1.0 + alpha_nb * mu_nb)
    eb_expected_crashes = eb_weight * mu_nb + (1.0 - eb_weight) * y
    eb_rate_per_100m_vkt = eb_expected_crashes / exposure
    psi_excess_crashes = eb_expected_crashes - mu_nb

    df["spf_predicted_crashes_poisson"] = mu_pois
    df["spf_predicted_crashes_nb2"] = mu_nb
    df["eb_weight"] = eb_weight
    df["eb_expected_crashes"] = eb_expected_crashes
    df["observed_rate_per_100m_vkt"] = y / exposure
    df["eb_rate_per_100m_vkt"] = eb_rate_per_100m_vkt
    df["psi_excess_crashes"] = psi_excess_crashes

    coef_rows = []
    for i, name in enumerate(feature_names):
        coef_rows.append({
            "feature": name,
            "poisson_beta": float(beta_pois[i]),
            "poisson_se": float(se_pois[i]),
            "poisson_rate_ratio": float(np.exp(beta_pois[i])),
            "nb2_beta": float(beta_nb[i]),
            "nb2_se": float(se_nb[i]),
            "nb2_rate_ratio": float(np.exp(beta_nb[i])),
        })
    coef_df = pd.DataFrame(coef_rows)

    diagnostics = {
        "n_exposure_segments": int(len(df)),
        "total_observed_ksi_on_exposure_segments": int(y.sum()),
        "total_exposure_100m_vkt": float(exposure.sum()),
        "pooled_ksi_rate_per_100m_vkt": float(y.sum() / exposure.sum()),
        "poisson_log_likelihood": float(-res_pois.fun),
        "nb2_log_likelihood": float(-res_nb.fun),
        "nb2_overdispersion_alpha": alpha_nb,
        "lr_test_stat_nb2_vs_poisson": float(2.0 * (-res_nb.fun - (-res_pois.fun))),
    }
    return df, coef_df, diagnostics


def profile_quebec_mtq_comparator(mtq_path: Path) -> dict:
    """Summarize Quebec MTQ highway section AADT as a provincial comparator."""
    data = json.loads(mtq_path.read_text())
    props = pd.DataFrame([f["properties"] for f in data["features"]])
    val1 = pd.to_numeric(props["val_djma_annee_1"], errors="coerce")
    valid = val1.dropna()
    return {
        "sections": int(len(props)),
        "latest_year_mode": int(pd.to_numeric(props["djma_annee_1"], errors="coerce").mode().iloc[0]),
        "mean_aadt": float(valid.mean()),
        "median_aadt": float(valid.median()),
        "p90_aadt": float(valid.quantile(0.90)),
        "max_aadt": float(valid.max()),
    }


def render_figures(class_df: pd.DataFrame, top_corridors: pd.DataFrame, modeled_df: pd.DataFrame, figures_dir: Path):
    """Render publication-quality figures for Phase 1 Corridor Exposure & SPF/EB analysis."""
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: KSI & Fatal Crash Rates per 100M VKT by Road Class + Top Corridors
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5), dpi=160)
    plot_cls = class_df[class_df["road_class"].isin(MAIN_ROAD_CLASSES)].copy()
    plot_cls = plot_cls.sort_values("ksi_per_100m_vkt", ascending=True)

    ax = axes[0]
    y_pos = np.arange(len(plot_cls))
    ax.barh(y_pos - 0.18, plot_cls["ksi_per_100m_vkt"], height=0.35, color="#146f64", label="KSI Crashes / 100M VKT")
    ax.barh(y_pos + 0.18, plot_cls["fatal_per_100m_vkt"], height=0.35, color="#b14a2e", label="Fatal Crashes / 100M VKT")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_cls["road_class"])
    ax.set_xlabel("Crash Rate per 100 Million VKT (2006–2023)")
    ax.set_title("A. Exposure-Adjusted Crash Rates by Road Class")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right", frameon=True)

    ax2 = axes[1]
    top12 = top_corridors.head(12).iloc[::-1]
    y2 = np.arange(len(top12))
    ax2.barh(y2 - 0.18, top12["observed_ksi_per_100m_vkt"], height=0.35, color="#879e96", label="Observed KSI / 100M VKT")
    ax2.barh(y2 + 0.18, top12["eb_ksi_per_100m_vkt"], height=0.35, color="#153a38", label="EB-Smoothed KSI / 100M VKT")
    ax2.set_yticks(y2)
    ax2.set_yticklabels(top12["corridor_name"], fontsize=8.5)
    ax2.set_xlabel("KSI Crashes per 100 Million VKT")
    ax2.set_title("B. Top High-Risk Major Corridors (Empirical Bayes Ranked)")
    ax2.grid(axis="x", linestyle="--", alpha=0.4)
    ax2.legend(loc="lower right", frameon=True)

    fig.tight_layout()
    fig.savefig(figures_dir / "corridor_pilot_rates_by_class.png", bbox_inches="tight")
    plt.close(fig)

    # Figure 2: Safety Performance Function (AADT vs Crash Rate & EB Shrinkage)
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), dpi=160)
    ax = axes[0]
    for rclass, color in [
        ("Major Arterial", "#146f64"),
        ("Minor Arterial", "#d97f2b"),
        ("Collector", "#4a6fe3"),
        ("Expressway", "#8e2d56"),
    ]:
        sub = modeled_df[modeled_df["FEATURE_CODE_DESC"] == rclass]
        if len(sub) > 0:
            bins = pd.qcut(sub["aadt"], q=min(8, max(2, len(sub) // 100)), duplicates="drop")
            grp = sub.groupby(bins, observed=False).agg(
                mean_aadt=("aadt", "mean"),
                obs_crashes=("ksi_crashes", "sum"),
                pred_crashes=("spf_predicted_crashes_nb2", "sum"),
                total_km=("length_km", "sum"),
            )
            ax.plot(grp["mean_aadt"], grp["pred_crashes"] / grp["total_km"], "-o", color=color, label=f"{rclass} (NB2 SPF)")
            ax.scatter(grp["mean_aadt"], grp["obs_crashes"] / grp["total_km"], color=color, alpha=0.55, marker="x")
    ax.set_xscale("log")
    ax.set_xlabel("Average Annual Daily Traffic (AADT, vehicles/day, log scale)")
    ax.set_ylabel("KSI Crashes per km (2006–2023)")
    ax.set_title("A. Negative Binomial Safety Performance Function (SPF)")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8.5)

    ax2 = axes[1]
    sample = modeled_df[modeled_df["exposure_100m_vkt"] >= 0.02].copy()
    ax2.scatter(
        sample["observed_rate_per_100m_vkt"],
        sample["eb_rate_per_100m_vkt"],
        c=sample["eb_weight"],
        cmap="viridis",
        s=14,
        alpha=0.55,
    )
    max_v = float(np.percentile(sample["observed_rate_per_100m_vkt"], 99))
    ax2.plot([0, max_v], [0, max_v], "r--", lw=1.2, label="1:1 Unsmoothed Line")
    ax2.set_xlim(0, max_v)
    ax2.set_ylim(0, max_v)
    ax2.set_xlabel("Raw Observed KSI Rate (per 100M VKT)")
    ax2.set_ylabel("Empirical Bayes (EB) Smoothed KSI Rate (per 100M VKT)")
    ax2.set_title("B. Empirical Bayes Shrinkage of Noisy Segment Rates")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="upper left")

    fig.tight_layout()
    fig.savefig(figures_dir / "corridor_pilot_spf_eb.png", bbox_inches="tight")
    plt.close(fig)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run(root: Path | None = None) -> dict:
    root = (root or PROJECT_ROOT).resolve()
    raw_geo = root / "data/raw/data_gap_2026_11_04/geography"
    raw_exp = root / "data/raw/data_gap_2026_11_04/exposure"
    out_dir = root / "data/derived/corridor_pilot"
    tables_dir = root / "reports/tables"
    figures_dir = root / "reports/figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    ksi_path = raw_geo / "toronto_ksi_4326.csv"
    tcl_path = raw_geo / "toronto_centreline_4326.csv"
    svc_path = raw_exp / "toronto_svc_summary.csv"
    mtq_path = raw_exp / "mtq_traffic.geojson"

    ksi_raw = pd.read_csv(ksi_path, dtype=str, keep_default_na=False)
    tcl_raw = pd.read_csv(tcl_path, dtype=str, keep_default_na=False)
    svc_raw = pd.read_csv(svc_path, dtype=str, keep_default_na=False)

    roads = tcl_raw[tcl_raw["FEATURE_CODE_DESC"].isin(ROAD_CLASSES)].copy().reset_index(drop=True)
    seg_lengths_m, centroid_lon, centroid_lat, polylines, tree, pts_seg_idx = extract_segment_geometry(roads)
    roads["length_m"] = seg_lengths_m
    roads["length_km"] = seg_lengths_m / 1000.0
    roads["centroid_lon"] = centroid_lon
    roads["centroid_lat"] = centroid_lat

    events = collapse_ksi_events(ksi_raw)
    snapped = snap_collisions_to_segments(events, roads, polylines, tree, pts_seg_idx, max_dist_m=50.0)

    # Aggregate snapped collisions per segment
    matched_events = snapped[snapped["matched_centreline_id"].notna()].copy()
    seg_crashes = matched_events.groupby("matched_centreline_id", sort=False).agg(
        ksi_crashes=("collision_id", "size"),
        fatal_crashes=("is_fatal", "sum"),
        vru_ksi_crashes=("has_vru", "sum"),
        pedestrian_ksi_crashes=("has_pedestrian", "sum"),
        cyclist_ksi_crashes=("has_cyclist", "sum"),
        motorcyclist_ksi_crashes=("has_motorcyclist", "sum"),
        heavy_truck_ksi_crashes=("has_heavy_truck", "sum"),
        median_snap_dist_m=("snap_distance_m", "median"),
    ).reset_index().rename(columns={"matched_centreline_id": "CENTRELINE_ID"})

    exp_segments = aggregate_exposure_studies(svc_raw).rename(columns={"centreline_id": "CENTRELINE_ID"})

    # Merge road inventory + crash counts + AADT exposure
    merged = roads[[
        "CENTRELINE_ID", "LINEAR_NAME_FULL", "FEATURE_CODE_DESC",
        "ONEWAY_DIR_CODE_DESC", "length_m", "length_km", "centroid_lon", "centroid_lat"
    ]].merge(seg_crashes, on="CENTRELINE_ID", how="left").merge(exp_segments, on="CENTRELINE_ID", how="left")

    count_cols = [
        "ksi_crashes", "fatal_crashes", "vru_ksi_crashes",
        "pedestrian_ksi_crashes", "cyclist_ksi_crashes",
        "motorcyclist_ksi_crashes", "heavy_truck_ksi_crashes",
    ]
    for col in count_cols:
        merged[col] = merged[col].fillna(0).astype(int)

    merged["has_aadt"] = merged["aadt"].notna() & merged["aadt"].gt(0)
    merged["annual_vkt"] = np.where(merged["has_aadt"], merged["aadt"] * 365.25 * merged["length_km"], np.nan)
    merged["exposure_100m_vkt"] = np.where(
        merged["has_aadt"],
        (merged["annual_vkt"] * STUDY_YEARS) / 1e8,
        np.nan,
    )

    modeled_df, coef_df, spf_diag = fit_poisson_and_nb2_spf(merged)

    # Join EB predictions back to full segment table
    eb_cols = [
        "CENTRELINE_ID", "spf_predicted_crashes_poisson", "spf_predicted_crashes_nb2",
        "eb_weight", "eb_expected_crashes", "observed_rate_per_100m_vkt",
        "eb_rate_per_100m_vkt", "psi_excess_crashes"
    ]
    full_table = merged.merge(modeled_df[eb_cols], on="CENTRELINE_ID", how="left")
    parquet_out = out_dir / "segment_exposure_crashes.parquet"
    con = duckdb.connect()
    con.register("full_table_view", full_table)
    con.execute(
        f"COPY full_table_view TO '{parquet_out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
    )
    con.close()

    # Summary by Road Class on exposure-measured segments
    exp_only = full_table[full_table["has_aadt"]].copy()
    class_rows = []
    for rclass, grp in exp_only.groupby("FEATURE_CODE_DESC", sort=False):
        vkt_100m = float(grp["exposure_100m_vkt"].sum())
        ksi_n = int(grp["ksi_crashes"].sum())
        fat_n = int(grp["fatal_crashes"].sum())
        vru_n = int(grp["vru_ksi_crashes"].sum())
        eb_n = float(grp["eb_expected_crashes"].sum())
        class_rows.append({
            "road_class": rclass,
            "monitored_segments": int(len(grp)),
            "monitored_length_km": round(float(grp["length_km"].sum()), 3),
            "mean_aadt": round(float(grp["aadt"].mean()), 1),
            "cumulative_100m_vkt_18y": round(vkt_100m, 4),
            "ksi_crashes": ksi_n,
            "fatal_crashes": fat_n,
            "vru_ksi_crashes": vru_n,
            "ksi_per_100m_vkt": round(ksi_n / vkt_100m, 3) if vkt_100m > 0 else np.nan,
            "fatal_per_100m_vkt": round(fat_n / vkt_100m, 3) if vkt_100m > 0 else np.nan,
            "vru_ksi_per_100m_vkt": round(vru_n / vkt_100m, 3) if vkt_100m > 0 else np.nan,
            "eb_expected_ksi_per_100m_vkt": round(eb_n / vkt_100m, 3) if vkt_100m > 0 else np.nan,
        })
    class_df = pd.DataFrame(class_rows).sort_values("cumulative_100m_vkt_18y", ascending=False)
    class_df.to_csv(tables_dir / "corridor_pilot_by_road_class.csv", index=False)

    # Corridor-level aggregation (Major/Minor Arterials & Expressways with >= 2 km monitored length and >= 0.5 100M VKT)
    corridors = exp_only.groupby(["LINEAR_NAME_FULL", "FEATURE_CODE_DESC"], sort=False).agg(
        monitored_segments=("CENTRELINE_ID", "size"),
        monitored_length_km=("length_km", "sum"),
        mean_aadt=("aadt", "mean"),
        cumulative_100m_vkt=("exposure_100m_vkt", "sum"),
        ksi_crashes=("ksi_crashes", "sum"),
        fatal_crashes=("fatal_crashes", "sum"),
        vru_ksi_crashes=("vru_ksi_crashes", "sum"),
        spf_expected_ksi=("spf_predicted_crashes_nb2", "sum"),
        eb_expected_ksi=("eb_expected_crashes", "sum"),
        psi_excess_ksi=("psi_excess_crashes", "sum"),
    ).reset_index()
    corridors = corridors[
        corridors["monitored_length_km"].ge(2.0)
        & corridors["cumulative_100m_vkt"].ge(0.50)
        & corridors["LINEAR_NAME_FULL"].ne("")
    ].copy()
    corridors["corridor_name"] = corridors["LINEAR_NAME_FULL"] + " (" + corridors["FEATURE_CODE_DESC"] + ")"
    corridors["observed_ksi_per_100m_vkt"] = corridors["ksi_crashes"] / corridors["cumulative_100m_vkt"]
    corridors["eb_ksi_per_100m_vkt"] = corridors["eb_expected_ksi"] / corridors["cumulative_100m_vkt"]
    corridors["fatal_per_100m_vkt"] = corridors["fatal_crashes"] / corridors["cumulative_100m_vkt"]
    corridors = corridors.sort_values("eb_ksi_per_100m_vkt", ascending=False).reset_index(drop=True)
    corridors.head(30).to_csv(tables_dir / "corridor_pilot_top_corridors.csv", index=False)

    coef_df.to_csv(tables_dir / "corridor_pilot_model_coefficients.csv", index=False)

    mtq_summary = profile_quebec_mtq_comparator(mtq_path)

    summary_row = {
        "jurisdiction": "City of Toronto (with Quebec MTQ Highway Comparator)",
        "study_period": "2006-2023 (18 years)",
        "total_ksi_collisions": int(len(events)),
        "fatal_ksi_collisions": int(events["is_fatal"].sum()),
        "valid_coord_collisions": int(snapped["match_quality"].ne("missing_coordinates").sum()),
        "snapped_within_50m_collisions": int(snapped["matched_centreline_id"].notna().sum()),
        "snapped_Within_50m_pct": round(float(snapped["matched_centreline_id"].notna().mean() * 100.0), 2),
        "spatial_and_name_verified_collisions": int(snapped["match_quality"].eq("spatial_and_name").sum()),
        "median_snap_distance_m": round(float(snapped["snap_distance_m"].median()), 2),
        "total_road_segments": int(len(roads)),
        "total_road_network_km": round(float(roads["length_km"].sum()), 2),
        "exposure_monitored_segments": int(exp_only["CENTRELINE_ID"].nunique()),
        "exposure_monitored_km": round(float(exp_only["length_km"].sum()), 2),
        "ksi_on_exposure_segments": int(exp_only["ksi_crashes"].sum()),
        "fatal_on_exposure_segments": int(exp_only["fatal_crashes"].sum()),
        "cumulative_100m_vkt_monitored": round(float(exp_only["exposure_100m_vkt"].sum()), 3),
        "pooled_ksi_per_100m_vkt": round(spf_diag["pooled_ksi_rate_per_100m_vkt"], 3),
        "pooled_fatal_per_100m_vkt": round(
            float(exp_only["fatal_crashes"].sum() / exp_only["exposure_100m_vkt"].sum()), 3
        ),
        "nb2_overdispersion_alpha": round(spf_diag["nb2_overdispersion_alpha"], 4),
        "quebec_mtq_sections": mtq_summary["sections"],
        "quebec_mtq_median_aadt": mtq_summary["median_aadt"],
    }
    pd.DataFrame([summary_row]).to_csv(tables_dir / "corridor_pilot_summary.csv", index=False)

    render_figures(class_df, corridors, modeled_df, figures_dir)

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "Phase 1: Corridor-Level Pilot Linkage (Spatial + Exposure)",
        "inputs": {
            "toronto_ksi_4326.csv": sha256(ksi_path),
            "toronto_centreline_4326.csv": sha256(tcl_path),
            "toronto_svc_summary.csv": sha256(svc_path),
            "mtq_traffic.geojson": sha256(mtq_path),
        },
        "summary": summary_row,
        "spf_diagnostics": spf_diag,
        "quebec_mtq_comparator": mtq_summary,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary_row, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    run(args.root)
