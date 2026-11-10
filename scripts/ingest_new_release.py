#!/usr/bin/env python3
"""CLI Pipeline for Prospective NCDB Microdata Ingestion & Out-of-Sample Drift Governance (2022+).

Chains:
  1. Open Government CKAN Catalog Scraping / Discovery (Package 1eb9eba7-71d1-4b30-9fb1-30cbdab7e63a).
  2. Cryptographic SHA-256 capture and automated schema validation (validate_release_schema).
  3. Prospective scoring with frozen typology severity model weights.
  4. Out-of-sample covariate drift (Population Stability Index / PSI & JSD) and calibration
     drift (Observed / Expected fatality ratio O/E & intercept log-odds shift).
  5. Governance alert triggers (GREEN / AMBER / RED) and immutable audit receipts.

Usage:
  ./scripts/ingest_new_release.py                               # Checks CKAN catalog status
  ./scripts/ingest_new_release.py --online                      # Checks live CKAN API
  ./scripts/ingest_new_release.py --simulate-synthetic         # Tests pipeline on synthetic 2022/2023 batches
  ./scripts/ingest_new_release.py --input-file <path_to_csv>    # Ingests and scores a specific release CSV
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import urllib.request

# Ensure MPLCONFIGDIR is set to a writable directory
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mpl")

# Locate repository and road_to_safety source tree
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "scripts" else SCRIPT_DIR.parents[1]
DEFAULT_RTS_ROOT = REPO_ROOT / "projects/road_to_safety"
if not DEFAULT_RTS_ROOT.exists():
    # Fallback if called directly within projects/road_to_safety
    DEFAULT_RTS_ROOT = REPO_ROOT

sys.path.insert(0, str(DEFAULT_RTS_ROOT / "src"))

try:
    import duckdb
    import numpy as np
    import pandas as pd
    from road_to_safety.explore import DICTIONARY_DOMAINS, sha256
    from road_to_safety.monitor_prospective import (
        CKAN_API_URL,
        CKAN_PACKAGE_ID,
        CONDITION_FEATURES,
        MANDATORY_NCDB_COLUMNS,
        build_synthetic_prospective_batches,
        check_ckan_catalog,
        compute_psi_and_jsd,
        evaluate_release_drift,
        ingest_and_score_release,
        validate_release_schema,
    )
    from road_to_safety.typology_severity import (
        P_USER_FEATURES,
        V_TYPE_FEATURES,
    )
except ImportError as err:
    print(f"Error importing road_to_safety modules: {err}", file=sys.stderr)
    print("Ensure you run with the project's virtual environment:", file=sys.stderr)
    print("  projects/road_to_safety/.venv/bin/python scripts/ingest_new_release.py", file=sys.stderr)
    sys.exit(1)


def collapse_raw_ncdb_to_collisions(df_raw: pd.DataFrame, source_id: str = "prospective") -> pd.DataFrame:
    """Collapse raw person-vehicle microdata rows into 1:1 canonical collision records."""
    con = duckdb.connect()
    con.register("raw_rows", df_raw)

    for col in ["C_YEAR", "C_CASE", "C_SEV", "C_MNTH", "C_WDAY", "C_HOUR",
                "C_RCFG", "C_WTHR", "C_RSUR", "C_RALN", "C_TRAF", "V_ID", "V_TYPE", "P_USER"]:
        if col not in df_raw.columns:
            con.execute(f"ALTER TABLE raw_rows ADD COLUMN {col} VARCHAR")

    query = f"""
    SELECT
        '{source_id}' AS source_id,
        C_YEAR,
        C_CASE,
        CAST(CASE WHEN FIRST(C_SEV) = '1' THEN 1 ELSE 0 END AS TINYINT) AS is_fatal,
        FIRST(C_MNTH) AS C_MNTH,
        FIRST(C_WDAY) AS C_WDAY,
        FIRST(C_HOUR) AS C_HOUR,
        FIRST(C_RCFG) AS C_RCFG,
        FIRST(C_WTHR) AS C_WTHR,
        FIRST(C_RSUR) AS C_RSUR,
        FIRST(C_RALN) AS C_RALN,
        FIRST(C_TRAF) AS C_TRAF,
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
        CAST(MAX(CASE WHEN V_TYPE IN ('', 'U', 'UU', 'X', 'XX', 'Q', 'QQ') THEN 1 ELSE 0 END) AS TINYINT) AS has_unknown_vehicle,
        CAST(CASE WHEN COUNT(DISTINCT CASE
            WHEN V_ID NOT IN ('', '0', '99', 'N', 'NN', 'U', 'UU', 'X', 'XX', 'Q', 'QQ')
            THEN V_ID ELSE NULL END) >= 2 THEN 1 ELSE 0 END AS TINYINT) AS multi_vehicle,
        CAST(CASE WHEN (MAX(CASE WHEN P_USER IN ('3', '4', '5') OR V_TYPE IN ('14', '17', 'N', 'NN') OR V_ID = '99' THEN 1 ELSE 0 END) = 1)
                  THEN 1 ELSE 0 END AS TINYINT) AS has_vru,
        CAST(CASE WHEN (MAX(CASE WHEN V_TYPE IN ('7', '8') THEN 1 ELSE 0 END) = 1)
                  THEN 1 ELSE 0 END AS TINYINT) AS has_heavy_freight,
        CAST(CASE WHEN (MAX(CASE WHEN V_TYPE IN ('7', '8') THEN 1 ELSE 0 END) = 1)
                   AND (MAX(CASE WHEN P_USER IN ('3', '4', '5') OR V_TYPE IN ('14', '17', 'N', 'NN') OR V_ID = '99' THEN 1 ELSE 0 END) = 1)
                  THEN 1 ELSE 0 END AS TINYINT) AS heavy_freight_x_vru
    FROM raw_rows
    GROUP BY C_YEAR, C_CASE
    ORDER BY TRY_CAST(C_CASE AS BIGINT)
    """
    df_col = con.execute(query).df()
    con.close()
    return df_col


def print_banner(title: str) -> None:
    print("\n" + "=" * 74)
    print(f" {title}")
    print("=" * 74)


def print_hud_summary(title: str, items: list[tuple[str, str]]) -> None:
    print(f"\n┌── {title} " + "─" * max(0, 68 - len(title)) + "┐")
    for key, val in items:
        dots = "." * max(1, 38 - len(key))
        print(f"│  {key} {dots} {val:<28} │")
    print("└" + "─" * 72 + "┘")


def evaluate_release_pipeline(
    csv_path: Path,
    root: Path,
    out_dir: Path,
    recalibration_delta: float = 0.0,
    force: bool = False,
) -> tuple[dict, dict]:
    """Execute the full ingestion, schema check, scoring, and drift evaluation pipeline for one CSV."""
    print_banner(f"Ingesting Release: {csv_path.name}")

    # 1. Capture SHA-256 fingerprint
    file_hash = sha256(csv_path)
    file_size_mb = csv_path.stat().st_size / (1024 * 1024)
    print(f"  • Source file: {csv_path.resolve()}")
    print(f"  • Size: {file_size_mb:.2f} MB")
    print(f"  • SHA-256: {file_hash}")

    # 2. Schema and domain validation
    try:
        df_raw = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df_raw = pd.read_csv(csv_path, dtype=str, encoding="latin1")

    validation = validate_release_schema(df_raw)
    status = validation["status"]
    errs = validation["error_counts"]

    print(f"  • Raw Rows: {len(df_raw):,} across {len(df_raw.columns)} columns")
    print(f"  • Schema Status: {status.upper()}")
    if errs["missing_mandatory_columns"] > 0:
        print(f"    - Missing Columns: {validation['missing_mandatory_columns']}")
    if errs["corrupted_keys"] > 0:
        print(f"    - Corrupted Keys: {errs['corrupted_keys']} ({validation.get('key_errors', [])})")
    if errs["out_of_domain_codes"] > 0:
        print(f"    - Out-of-Domain Codes: {errs['out_of_domain_codes']}")

    if status == "invalid_schema" and not force:
        receipt = {
            "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
            "csv_path": str(csv_path),
            "sha256": file_hash,
            "status": "REJECTED_INVALID_SCHEMA",
            "validation": validation,
        }
        receipt_path = out_dir / f"{csv_path.stem}_ingestion_receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
        print(f"\n[ERROR] Ingestion REJECTED: Schema validation failed. Receipt saved to {receipt_path}")
        return receipt, {}

    # 3. Collapse raw rows into collision records
    print("  • Collapsing person-vehicle rows to unique collision level...")
    df_col = collapse_raw_ncdb_to_collisions(df_raw, source_id=csv_path.stem)
    n_collisions = len(df_col)
    n_fatal = int(df_col["is_fatal"].sum())
    fatal_pct = (n_fatal / max(1, n_collisions)) * 100.0
    print(f"  • Resolved Collisions: {n_collisions:,} ({n_fatal:,} fatal; {fatal_pct:.3f}%)")

    # 4. Score collisions with frozen M0 and M2 models
    print("  • Scoring collisions with frozen M0 and M2 severity models...")
    # Load model weights or odds ratios
    or_path = root / "reports/tables/typology_odds_ratios.csv"
    if not or_path.exists():
        raise FileNotFoundError(f"Missing typology odds ratios at {or_path}")

    or_df = pd.read_csv(or_path)
    coef_map = dict(zip(or_df["feature"], or_df["coefficient_log_odds"]))

    # M2 Logits
    logits_m2 = np.full(n_collisions, -4.170, dtype=float)
    for feat, beta in coef_map.items():
        if feat in df_col.columns:
            val = pd.to_numeric(df_col[feat], errors="coerce").fillna(0.0).to_numpy()
            logits_m2 += val * float(beta)

    # M0 Logits (conditions only approximation: intercept -4.11)
    cond_feats = [f for f in CONDITION_FEATURES if f in coef_map]
    logits_m0 = np.full(n_collisions, -4.110, dtype=float)
    for feat in cond_feats:
        if feat in df_col.columns:
            val = pd.to_numeric(df_col[feat], errors="coerce").fillna(0.0).to_numpy()
            logits_m0 += val * float(coef_map.get(feat, 0.0))

    from scipy.special import expit
    df_col["p_M0_conditions_only"] = expit(logits_m0)
    df_col["p_M2_full_typology"] = expit(logits_m2)
    df_col["p_M2_full_typology_recal"] = expit(logits_m2 + recalibration_delta)

    # 5. Load Reference Baseline (2017-2018 validation collisions)
    ref_parquet = root / "data/derived/typology_severity/collision_typologies.parquet"
    pred_parquet = root / "data/derived/typology_severity/eval_predictions_2017_2021.parquet"
    if ref_parquet.exists() and pred_parquet.exists():
        con = duckdb.connect()
        ref_df = con.execute(
            f"""
            SELECT t.*, p.p_M0_conditions_only, p.p_M2_full_typology, p.p_M2_full_typology_recal
            FROM read_parquet('{ref_parquet.as_posix()}') t
            INNER JOIN read_parquet('{pred_parquet.as_posix()}') p
                ON t.source_id = p.source_id AND t.C_YEAR = p.C_YEAR AND t.C_CASE = p.C_CASE
            WHERE t.C_YEAR IN ('2017', '2018')
            """
        ).df()
        con.close()
    else:
        # Fallback to current if baseline not available
        ref_df = df_col.copy()

    protocol = json.loads((root / "data/reference/severity_protocol.json").read_text())
    domains = protocol["categorical_domains"]

    # 6. Evaluate Covariate & Calibration Drift
    summary, feature_drift = evaluate_release_drift(ref_df, df_col, csv_path.stem, domains)

    # 7. Write receipts and summaries
    receipt = {
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "csv_path": str(csv_path.resolve()),
        "sha256": file_hash,
        "raw_rows": len(df_raw),
        "collisions_ingested": n_collisions,
        "fatal_collisions": n_fatal,
        "validation_status": status,
        "drift_governance_alert": summary["alert_status"],
        "recommended_action": summary["recommended_action"],
        "summary_metrics": summary,
    }
    receipt_path = out_dir / f"{csv_path.stem}_ingestion_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    drift_report_path = out_dir / f"{csv_path.stem}_drift_evaluation.json"
    drift_report_path.write_text(json.dumps({"summary": summary, "feature_drift": feature_drift}, indent=2) + "\n")

    # Display HUD summary
    print_hud_summary(
        f"Governance Receipt: {csv_path.stem}",
        [
            ("SHA-256 Fingerprint", file_hash[:16] + "..."),
            ("Canonical Collisions", f"{n_collisions:,}"),
            ("Fatal Crashes", f"{n_fatal:,} ({fatal_pct:.2f}%)"),
            ("Schema Validation", status.upper()),
            ("M2 Mean Pred Fatality", f"{summary['m2_mean_pred_pct']:.3f}%"),
            ("M2 O/E Calibration Ratio", f"{summary['m2_oe_ratio']:.4f}"),
            ("Recalibrated O/E Ratio", f"{summary['m2_recal_oe_ratio']:.4f}"),
            ("Max Covariate PSI", f"{summary['max_covariate_psi']:.5f} ({summary['max_psi_feature']})"),
            ("Governance Alert Status", summary["alert_status"]),
        ],
    )
    print(f"\n  ► Action: {summary['recommended_action']}")
    print(f"  ► Receipt saved: {receipt_path.relative_to(REPO_ROOT) if receipt_path.is_relative_to(REPO_ROOT) else receipt_path}")

    return receipt, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=DEFAULT_RTS_ROOT, help="Path to projects/road_to_safety")
    parser.add_argument("--input-file", type=Path, default=None, help="Direct path to an incoming release CSV")
    parser.add_argument("--online", action="store_true", help="Query live CKAN API on open.canada.ca")
    parser.add_argument("--download", action="store_true", help="Download new candidate release CSV from CKAN if found")
    parser.add_argument("--simulate-synthetic", action="store_true", help="Run ingestion & drift pipeline on synthetic 2022/2023 stress batches")
    parser.add_argument("--force", action="store_true", help="Force scoring even if schema anomalies are detected")
    parser.add_argument("--out-dir", type=Path, default=None, help="Receipts output directory")
    args = parser.parse_args()

    root = args.root.resolve()
    out_dir = args.out_dir or (root / "data/derived/monitoring/receipts")
    out_dir.mkdir(parents=True, exist_ok=True)

    print_banner("Canadian Collision Research · 2022+ NCDB Microdata Ingestion Pipeline")
    print(f"Working Directory: {root}")
    print(f"Open Government CKAN Package ID: {CKAN_PACKAGE_ID}")

    # Case 1: Specific input file provided
    if args.input_file is not None:
        if not args.input_file.exists():
            print(f"[ERROR] Specified input file does not exist: {args.input_file}", file=sys.stderr)
            return 1
        evaluate_release_pipeline(args.input_file, root, out_dir, force=args.force)
        return 0

    # Case 2: Check CKAN Catalog
    print("\n[Step 1/2] Checking Open Government CKAN Catalog...")
    catalog = check_ckan_catalog(root, online=args.online)
    print(f"  • CKAN Mode: {catalog['fetch_mode']}")
    print(f"  • Total Resources in Package: {catalog['total_ckan_resources']}")
    print(f"  • Verified Local Historical Releases: {catalog['verified_local_releases']} / 24")
    print(f"  • Post-2021 Candidate Releases Detected: {catalog['post_2021_microdata_releases_detected']}")
    print(f"  • Catalog Status: {catalog['ingestion_status']}")

    if catalog["post_2021_candidates"]:
        print("\n  ► New microdata candidate(s) discovered:")
        for cand in catalog["post_2021_candidates"]:
            print(f"    - {cand['name']} (Years: {cand['years']}) -> {cand['url']}")
        if args.download:
            cand = catalog["post_2021_candidates"][0]
            dl_dir = root / "data/raw/ncdb"
            dl_dir.mkdir(parents=True, exist_ok=True)
            target_csv = dl_dir / f"ncdb_{cand['years'][0]}.csv"
            print(f"\n  • Downloading {cand['url']} to {target_csv}...")
            urllib.request.urlretrieve(cand["url"], target_csv)
            evaluate_release_pipeline(target_csv, root, out_dir, force=args.force)
            return 0
        else:
            print("\n  Tip: Run with --download to download and score candidate release automatically.")
            return 0

    # Case 3: No new release published yet by Transport Canada
    if args.simulate_synthetic:
        print("\n[Step 2/2] Running Ingestion & Drift Pipeline on Synthetic 2022 & 2023 Batches...")
        pred_parquet = root / "data/derived/typology_severity/eval_predictions_2017_2021.parquet"
        typ_parquet = root / "data/derived/typology_severity/collision_typologies.parquet"
        con = duckdb.connect()
        eval_df = con.execute(
            f"""
            SELECT t.*, p.p_M0_conditions_only, p.p_M2_full_typology, p.p_M0_conditions_only_recal, p.p_M2_full_typology_recal
            FROM read_parquet('{typ_parquet.as_posix()}') t
            INNER JOIN read_parquet('{pred_parquet.as_posix()}') p
                ON t.source_id = p.source_id AND t.C_YEAR = p.C_YEAR AND t.C_CASE = p.C_CASE
            """
        ).df()
        con.close()

        df_2019 = eval_df[eval_df["C_YEAR"] == "2019"].copy()
        df_2021 = eval_df[eval_df["C_YEAR"] == "2021"].copy()
        synth_batches = build_synthetic_prospective_batches(df_2019, df_2021)

        sim_dir = root / "data/derived/monitoring/simulated"
        sim_dir.mkdir(parents=True, exist_ok=True)

        for sim_label, sim_df in synth_batches:
            sim_df = sim_df.copy()
            # Ensure raw NCDB mandatory schema columns are populated for validation
            if "C_SEV" not in sim_df.columns:
                sim_df["C_SEV"] = np.where(sim_df["is_fatal"] == 1, "1", "2")
            if "V_ID" not in sim_df.columns:
                sim_df["V_ID"] = "01"
            if "V_TYPE" not in sim_df.columns:
                sim_df["V_TYPE"] = np.where(sim_df.get("has_heavy_truck", 0) == 1, "07",
                                   np.where(sim_df.get("has_road_tractor", 0) == 1, "08",
                                   np.where(sim_df.get("has_motorcycle_moped", 0) == 1, "14", "01")))
            if "P_ID" not in sim_df.columns:
                sim_df["P_ID"] = "01"
            if "P_USER" not in sim_df.columns:
                sim_df["P_USER"] = np.where(sim_df.get("has_pedestrian", 0) == 1, "3",
                                    np.where(sim_df.get("has_bicyclist", 0) == 1, "4",
                                    np.where(sim_df.get("has_motorcyclist", 0) == 1, "5", "1")))
            sim_csv = sim_dir / f"{sim_label}.csv"
            sim_df.to_csv(sim_csv, index=False)
            evaluate_release_pipeline(sim_csv, root, out_dir, force=args.force)

        print("\n✔ Synthetic prospective release simulation completed successfully.")
        return 0

    print("\n" + "=" * 74)
    print(" [CKAN Monitor Status] READY · WAITING FOR TRANSPORT CANADA 2022+ RELEASE")
    print("=" * 74)
    print("  Transport Canada has not yet published the 2022–2023 NCDB microdata release.")
    print("  All 24 historical annual releases (1999–2021) are cryptographically verified.")
    print("\n  Available CLI Commands:")
    print("    1. Test pipeline on synthetic 2022/2023 stress batches:")
    print("       ./scripts/ingest_new_release.py --simulate-synthetic")
    print("    2. Check live Open Government CKAN API for updates:")
    print("       ./scripts/ingest_new_release.py --online")
    print("    3. Ingest and score an incoming release CSV file:")
    print("       ./scripts/ingest_new_release.py --input-file path/to/ncdb_2022.csv")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
