"""Unit and integration tests for the 4-phase Operational Decision-Support Action Plan."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

import duckdb
import numpy as np
import pandas as pd

from road_to_safety.corridor_pilot import collapse_ksi_events, point_to_polyline_dist
from road_to_safety.monitor_prospective import compute_psi_and_jsd
from road_to_safety.operational_triage import threshold_metrics

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
        ]:
            p = ROOT / "reports/tables" / tbl
            self.assertTrue(p.exists(), f"Missing {tbl}")
            self.assertGreater(len(pd.read_csv(p)), 0)


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


if __name__ == "__main__":
    unittest.main()
