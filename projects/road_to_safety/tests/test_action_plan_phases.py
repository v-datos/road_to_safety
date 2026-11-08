"""Unit and integration tests for the 4-phase Operational Decision-Support Action Plan."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

import duckdb
import numpy as np
import pandas as pd

from road_to_safety.corridor_pilot import collapse_ksi_events, point_to_polyline_dist
from road_to_safety.monitor_prospective import (
    compute_psi_and_jsd,
    ingest_and_score_release,
    validate_release_schema,
)
from road_to_safety.operational_triage import threshold_metrics
from road_to_safety.typology_severity import compute_rolling_calibration_step

ROOT = Path(__file__).resolve().parents[1]


class TestPhase1CorridorPilot(unittest.TestCase):
    def test_geometry_point_to_polyline_distance(self):
        chunks = [(np.array([0.0, 100.0]), np.array([0.0, 0.0]))]
        dist = point_to_polyline_dist(50.0, 12.5, chunks)
        self.assertAlmostEqual(dist, 12.5, places=5)

    def test_collapse_ksi_events_parses_boolean_strings(self):
        sample = pd.DataFrame([
            {
                "_id": "1", "collision_id": "2020:1", "accdate": "2020-05-01",
                "stname1": "YONGE ST", "stname2": "BLOOR ST", "road_class": "Major Arterial",
                "acclass": "Fatal Injury", "accloc": "At Intersection", "traffictl": "Traffic Signal",
                "light": "Daylight", "rdsfcond": "Dry", "longitude": "-79.38", "latitude": "43.67",
                "neighbourhood": "Bay", "pedestrian": "true", "cyclist": "false",
                "motorcyclist": "false", "heavy_truck": "true", "aggressive": "false", "red_light": "false",
            },
            {
                "_id": "2", "collision_id": "2020:1", "accdate": "2020-05-01",
                "stname1": "YONGE ST", "stname2": "BLOOR ST", "road_class": "Major Arterial",
                "acclass": "Fatal Injury", "accloc": "At Intersection", "traffictl": "Traffic Signal",
                "light": "Daylight", "rdsfcond": "Dry", "longitude": "-79.38", "latitude": "43.67",
                "neighbourhood": "Bay", "pedestrian": "true", "cyclist": "false",
                "motorcyclist": "false", "heavy_truck": "true", "aggressive": "false", "red_light": "false",
            },
        ])
        events = collapse_ksi_events(sample)
        self.assertEqual(len(events), 1)
        self.assertEqual(int(events.iloc[0]["is_fatal"]), 1)
        self.assertEqual(int(events.iloc[0]["has_vru"]), 1)
        self.assertTrue(bool(events.iloc[0]["has_heavy_truck"]))

    def test_corridor_pilot_artifacts_and_conservation(self):
        manifest_path = ROOT / "data/derived/corridor_pilot/manifest.json"
        parquet_path = ROOT / "data/derived/corridor_pilot/segment_exposure_crashes.parquet"
        self.assertTrue(manifest_path.exists())
        self.assertTrue(parquet_path.exists())

        manifest = json.loads(manifest_path.read_text())
        summary = manifest["summary"]
        self.assertEqual(summary["total_ksi_collisions"], 7673)
        self.assertEqual(summary["fatal_ksi_collisions"], 1073)
        self.assertGreater(summary["snapped_Within_50m_pct"], 99.0)
        self.assertEqual(summary["total_road_segments"], 50083)
        self.assertEqual(summary["exposure_monitored_segments"], 14410)
        self.assertGreater(summary["nb2_overdispersion_alpha"], 0.1)
        self.assertEqual(summary["quebec_mtq_sections"], 7911)

        con = duckdb.connect()
        n_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{parquet_path.as_posix()}')").fetchone()[0]
        con.close()
        self.assertEqual(n_rows, 50083)

        for tbl in [
            "corridor_pilot_summary.csv",
            "corridor_pilot_by_road_class.csv",
            "corridor_pilot_top_corridors.csv",
            "corridor_pilot_model_coefficients.csv",
            "toronto_exposure_study_audit.csv",
            "corridor_ranking_sensitivity.csv",
        ]:
            p = ROOT / "reports/tables" / tbl
            self.assertTrue(p.exists(), f"Missing {tbl}")
            self.assertGreater(len(pd.read_csv(p)), 0)

        # Verify exposure audit values and ranking sensitivity correlation
        audit_p = ROOT / "reports/tables/toronto_exposure_study_audit.csv"
        audit_map = dict(zip(pd.read_csv(audit_p)["metric"], pd.read_csv(audit_p)["value"]))
        self.assertEqual(str(audit_map["study_year_span"]), "1993-2026")
        self.assertEqual(int(audit_map["studies_post_2023"]), 1882)
        self.assertEqual(int(audit_map["segments_with_studies_only_post_2023"]), 615)
        self.assertEqual(int(audit_map["segments_with_single_year_count"]), 6273)
        self.assertEqual(float(audit_map["median_study_duration_hours"]), 72.0)

        sens_p = ROOT / "reports/tables/corridor_ranking_sensitivity.csv"
        sens_df = pd.read_csv(sens_p)
        self.assertGreaterEqual(len(sens_df), 90)
        self.assertGreater(float(sens_df["spearman_rho_eb_primary_vs_window_constrained"].iloc[0]), 0.95)
        self.assertGreater(float(sens_df["spearman_rho_obs_primary_vs_window_constrained"].iloc[0]), 0.95)


class TestPhase2TypologySeverity(unittest.TestCase):
    def test_typology_reconciliation_and_discrimination_lift(self):
        manifest_path = ROOT / "data/derived/typology_severity/manifest.json"
        typ_parquet = ROOT / "data/derived/typology_severity/collision_typologies.parquet"
        pred_parquet = ROOT / "data/derived/typology_severity/eval_predictions_2017_2021.parquet"
        self.assertTrue(manifest_path.exists())
        self.assertTrue(typ_parquet.exists())
        self.assertTrue(pred_parquet.exists())

        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["total_collisions"], 2949846)
        self.assertEqual(manifest["fatal_collisions"], 47793)

        comp = manifest["test_2020_2021_comparison"]
        self.assertGreater(comp["M1_plus_p_user"]["roc_auc"], comp["M0_conditions_only"]["roc_auc"])
        self.assertGreater(comp["M2_full_typology"]["roc_auc"], comp["M1_plus_p_user"]["roc_auc"])
        self.assertGreater(comp["M1_plus_p_user"]["pr_auc"], comp["M0_conditions_only"]["pr_auc"])
        self.assertGreater(comp["M2_full_typology"]["pr_auc"], comp["M1_plus_p_user"]["pr_auc"])
        self.assertLess(comp["M2_full_typology"]["log_loss"], comp["M0_conditions_only"]["log_loss"])

        or_df = pd.read_csv(ROOT / "reports/tables/typology_odds_ratios.csv").set_index("feature")
        for key_driver in ["has_pedestrian", "has_motorcyclist", "has_heavy_truck", "has_road_tractor"]:
            self.assertGreater(float(or_df.loc[key_driver, "odds_ratio"]), 1.5)

    def test_rolling_calibration_cache_validity_and_disjoint_masks(self):
        """Verify calibration logic computes and caches distinct shifts when cal_year differs.

        Asserts that:
          1. Masks for training (year <= train_cutoff) and calibration (year == cal_year)
             are strictly disjoint. Overlap raises ValueError.
          2. When called with identical train_cutoff (e.g. 2017) but differing cal_year
             (e.g. 2018 vs 2019), distinct intercept shifts are stored in cache under
             distinct keys (model_name, train_cutoff, cal_year).
        """
        rng = np.random.default_rng(2026)
        n = 400
        years = np.array([2016] * 100 + [2017] * 100 + [2018] * 100 + [2019] * 100)
        X = rng.normal(0, 1, size=(n, 2))
        y = np.zeros(n, dtype=int)
        y[:200] = (rng.uniform(0, 1, 200) < 0.10).astype(int)
        y[200:300] = (rng.uniform(0, 1, 100) < 0.05).astype(int)
        y[300:400] = (rng.uniform(0, 1, 100) < 0.25).astype(int)

        models: dict = {}
        deltas: dict = {}

        # 1. Disjoint mask verification: call with train_cutoff=2017, cal_year=2018
        clf_1, delta_2018 = compute_rolling_calibration_step(
            model_name="M_test",
            X_mat=X,
            y=y,
            year=years,
            train_cutoff=2017,
            cal_year=2018,
            fitted_models=models,
            fitted_deltas=deltas,
        )
        self.assertIn(("M_test", 2017), models)
        self.assertIn(("M_test", 2017, 2018), deltas)

        # 2. Call with identical train_cutoff (2017) but differing cal_year (2019)
        clf_2, delta_2019 = compute_rolling_calibration_step(
            model_name="M_test",
            X_mat=X,
            y=y,
            year=years,
            train_cutoff=2017,
            cal_year=2019,
            fitted_models=models,
            fitted_deltas=deltas,
        )
        self.assertIs(clf_1, clf_2)
        self.assertIn(("M_test", 2017, 2019), deltas)
        self.assertNotEqual(delta_2018, delta_2019)
        self.assertEqual(len(deltas), 2)

        # 3. Disjoint mask assertion: training (year <= 2018) and calibration (year == 2018) must fail
        with self.assertRaises(ValueError):
            compute_rolling_calibration_step(
                model_name="M_test",
                X_mat=X,
                y=y,
                year=years,
                train_cutoff=2018,
                cal_year=2018,
                fitted_models=models,
                fitted_deltas=deltas,
            )


class TestPhase3OperationalTriage(unittest.TestCase):
    def test_threshold_metrics_unit(self):
        y = np.array([0, 0, 1, 1])
        p = np.array([0.01, 0.05, 0.04, 0.20])
        m = threshold_metrics(y, p, threshold=0.05, cost_ratio=10.0)
        self.assertEqual(m["tp"], 1)
        self.assertEqual(m["fp"], 1)
        self.assertEqual(m["fn"], 1)
        self.assertEqual(m["tn"], 1)
        self.assertAlmostEqual(m["precision_pct"], 50.0)
        self.assertAlmostEqual(m["recall_pct"], 50.0)

    def test_tiered_triage_monotonicity_and_band_conservation(self):
        eval_path = ROOT / "data/derived/operational_triage/triage_evaluation.json"
        self.assertTrue(eval_path.exists())

        tiers_df = pd.read_csv(ROOT / "reports/tables/triage_tiered_operating_points.csv")
        test_tiers = tiers_df[tiers_df["split"] == "test_2020_2021"].set_index("tier_id")

        t1 = test_tiers.loc["Tier_1_Critical_Dispatch"]
        t2 = test_tiers.loc["Tier_2_Priority_Response"]
        t3 = test_tiers.loc["Tier_3_Systemic_Watchlist"]

        self.assertGreater(t1["precision_pct"], t2["precision_pct"])
        self.assertGreater(t2["precision_pct"], t3["precision_pct"])
        self.assertLess(t1["alert_rate_pct"], t2["alert_rate_pct"])
        self.assertLess(t2["alert_rate_pct"], t3["alert_rate_pct"])
        self.assertLess(t1["recall_pct"], t2["recall_pct"])
        self.assertLess(t2["recall_pct"], t3["recall_pct"])

        bands_df = pd.read_csv(ROOT / "reports/tables/triage_mutually_exclusive_bands.csv")
        self.assertEqual(int(bands_df["collisions"].sum()), 163580)
        self.assertEqual(int(bands_df["fatal_collisions"].sum()), 3230)
        rates = list(bands_df["within_band_fatality_rate_pct"])
        self.assertEqual(rates, sorted(rates, reverse=True))


class TestPhase4MonitoringPipeline(unittest.TestCase):
    def test_psi_and_jsd_zero_when_identical(self):
        p = np.array([0.2, 0.5, 0.3])
        psi, jsd = compute_psi_and_jsd(p, p)
        self.assertAlmostEqual(psi, 0.0, places=7)
        self.assertAlmostEqual(jsd, 0.0, places=7)

    def test_prospective_monitor_outputs_and_alerts(self):
        report_path = ROOT / "data/derived/monitoring/prospective_monitor_report.json"
        self.assertTrue(report_path.exists())
        report = json.loads(report_path.read_text())

        cat = report["catalog_status"]
        self.assertEqual(cat["verified_local_releases"], 24)
        self.assertEqual(cat["mismatched_local_releases"], [])

        drift_df = pd.read_csv(ROOT / "reports/tables/monitoring_annual_drift_summary.csv").set_index("release")
        self.assertEqual(drift_df.loc["2017", "alert_status"], "GREEN")
        self.assertEqual(drift_df.loc["2018", "alert_status"], "GREEN")
        self.assertIn(drift_df.loc["2020", "alert_status"], ("AMBER", "RED"))
        self.assertEqual(drift_df.loc["2023_prospective_sentinel_shift_sim", "alert_status"], "RED")

    def test_validate_release_schema_valid_and_corrupted(self):
        """Test validate_release_schema detects valid schema, anomalies, and invalid schemas."""
        valid_data = {
            "C_YEAR": ["2022", "2022"],
            "C_CASE": ["1001", "1002"],
            "C_SEV": ["1", "2"],
            "C_MNTH": ["01", "12"],
            "C_WDAY": ["1", "7"],
            "C_HOUR": ["08", "23"],
            "C_RCFG": ["01", "02"],
            "C_WTHR": ["1", "2"],
            "C_RSUR": ["1", "2"],
            "C_RALN": ["1", "2"],
            "C_TRAF": ["01", "18"],
            "V_ID": ["01", "01"],
            "V_TYPE": ["01", "07"],
            "P_ID": ["01", "01"],
            "P_USER": ["1", "2"],
        }
        df_valid = pd.DataFrame(valid_data)
        report_valid = validate_release_schema(df_valid)
        self.assertEqual(report_valid["status"], "valid")
        self.assertEqual(report_valid["error_counts"]["missing_mandatory_columns"], 0)
        self.assertEqual(report_valid["error_counts"]["null_values"], 0)
        self.assertEqual(report_valid["error_counts"]["corrupted_keys"], 0)
        self.assertEqual(report_valid["error_counts"]["out_of_domain_codes"], 0)

        # Corrupted input 1: Missing mandatory column -> invalid_schema
        df_missing = df_valid.drop(columns=["C_SEV"])
        report_missing = validate_release_schema(df_missing)
        self.assertEqual(report_missing["status"], "invalid_schema")
        self.assertIn("C_SEV", report_missing["missing_mandatory_columns"])

        # Corrupted input 2: Nulls, corrupted keys, out-of-domain codes -> anomalies_detected
        df_corrupt = df_valid.copy()
        df_corrupt.loc[0, "C_CASE"] = "0"  # Invalid case ID
        df_corrupt.loc[0, "C_WTHR"] = "99"  # Out-of-domain weather code
        df_corrupt.loc[1, "C_MNTH"] = None  # Null value
        report_corrupt = validate_release_schema(df_corrupt)
        self.assertEqual(report_corrupt["status"], "anomalies_detected")
        self.assertGreater(report_corrupt["error_counts"]["null_values"], 0)
        self.assertGreater(report_corrupt["error_counts"]["corrupted_keys"], 0)
        self.assertGreater(report_corrupt["error_counts"]["out_of_domain_codes"], 0)


if __name__ == "__main__":
    unittest.main()
