from __future__ import annotations

import csv
import math
from pathlib import Path
import unittest

import duckdb
import numpy as np

from truck_collisions.analyze_vehicle_age import (
    AGE_COHORTS_ORDERED,
    age_to_cohort,
    classify_v_year_state,
    fit_weighted_logistic_irls,
    run_analysis as run_vehicle_age_analysis,
    wilson_ci_pct,
)
from truck_collisions.analyze_vkt_sensitivity import (
    NUMERATOR_SPECS,
    compute_ratios,
    run_analysis as run_vkt_sensitivity_analysis,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class VktSensitivityTests(unittest.TestCase):
    def test_compute_ratios_arithmetic_and_index(self) -> None:
        base_prelim = {
            "total_casualty_events": 3075,
            "fatal_events": 194,
            "injury_events": 2881,
            "modeled_vkt_billion_km": 34.2035,
            "events_per_billion_modeled_vkt": 3075 / 34.2035,
            "fatal_events_per_billion_modeled_vkt": 194 / 34.2035,
            "injury_events_per_billion_modeled_vkt": 2881 / 34.2035,
        }
        base = compute_ratios(194, 2881, 3075, 34.2035, base_prelim)
        self.assertEqual(base["total_casualty_events"], 3075)
        self.assertAlmostEqual(base["events_per_billion_modeled_vkt"], 3075 / 34.2035, places=9)
        self.assertAlmostEqual(base["fatal_events_per_billion_modeled_vkt"], 194 / 34.2035, places=9)
        self.assertAlmostEqual(base["injury_events_per_billion_modeled_vkt"], 2881 / 34.2035, places=9)
        self.assertAlmostEqual(base["fatal_share_pct"], 100.0 * 194 / 3075, places=9)
        self.assertAlmostEqual(base["events_per_billion_vkt_index_2015_100"], 100.0, places=9)

        indexed = compute_ratios(169, 2107, 2276, 45.5938, base_prelim)
        self.assertAlmostEqual(
            indexed["events_per_billion_vkt_index_2015_100"],
            100.0 * (2276 / 45.5938) / (3075 / 34.2035),
            places=9,
        )
        self.assertAlmostEqual(
            indexed["fatal_per_billion_vkt_index_2015_100"],
            100.0 * (169 / 45.5938) / (194 / 34.2035),
            places=9,
        )

    @unittest.skipUnless(
        (PROJECT_ROOT / "data/derived/ncdb/collisions.parquet").exists()
        and (PROJECT_ROOT / "data/reference/tractor_exposure_candidates.csv").exists(),
        "Derived collision dataset and exposure candidate CSV required",
    )
    def test_vkt_sensitivity_outputs_and_reconciliation(self) -> None:
        summary = run_vkt_sensitivity_analysis(PROJECT_ROOT)
        self.assertEqual(
            summary["decision_gate"],
            "model_normalized_historical_sensitivity_only_not_approved_as_primary_national_risk_rate",
        )
        self.assertEqual(summary["annual_rows"], 42)
        self.assertEqual(summary["summary_rows"], 114)

        annual_path = PROJECT_ROOT / "reports/tables/vkt_sensitivity_annual.csv"
        summary_path = PROJECT_ROOT / "reports/tables/vkt_sensitivity_summary.csv"
        figure_path = PROJECT_ROOT / "reports/figures/vkt_model_normalized_sensitivity.png"
        doc_path = PROJECT_ROOT / "docs/model_normalized_vkt_sensitivity.md"

        for p in (annual_path, summary_path, figure_path, doc_path):
            self.assertTrue(p.exists(), f"Missing expected artifact: {p}")
        self.assertGreater(figure_path.stat().st_size, 50_000)

        with annual_path.open(encoding="utf-8") as f_ann:
            annual_rows = list(csv.DictReader(f_ann))
        with summary_path.open(encoding="utf-8") as f_sum:
            summary_rows = list(csv.DictReader(f_sum))
        self.assertEqual(len(annual_rows), 42)
        self.assertEqual(len(summary_rows), 114)

        spec_names = {s[0] for s in NUMERATOR_SPECS}
        self.assertEqual({r["numerator_id"] for r in annual_rows}, spec_names)

        by_spec_year = {(r["numerator_id"], int(r["year"])): r for r in annual_rows}
        for spec in spec_names:
            r2015 = by_spec_year[(spec, 2015)]
            self.assertAlmostEqual(float(r2015["events_per_billion_vkt_index_2015_100"]), 100.0, places=4)
            self.assertAlmostEqual(float(r2015["fatal_per_billion_vkt_index_2015_100"]), 100.0, places=4)
            self.assertAlmostEqual(float(r2015["injury_per_billion_vkt_index_2015_100"]), 100.0, places=4)

            for y in range(2015, 2022):
                r = by_spec_year[(spec, y)]
                f_ev = int(r["fatal_events"])
                i_ev = int(r["injury_events"])
                t_ev = int(r["total_casualty_events"])
                vkt_b = float(r["modeled_vkt_billion_km"])
                self.assertEqual(f_ev + i_ev, t_ev)
                self.assertTrue(math.isclose(float(r["events_per_billion_modeled_vkt"]), t_ev / vkt_b, abs_tol=1e-6))
                self.assertTrue(math.isclose(float(r["fatal_events_per_billion_modeled_vkt"]), f_ev / vkt_b, abs_tol=1e-6))
                self.assertTrue(math.isclose(float(r["injury_events_per_billion_modeled_vkt"]), i_ev / vkt_b, abs_tol=1e-6))

        pooled_rows = {
            (r["numerator_id"], r["period_or_comparison_id"]): r
            for r in summary_rows
            if r["record_type"] == "pooled_period"
        }
        for spec in spec_names:
            r_15_17 = pooled_rows[(spec, "2015_2017")]
            f_sum = sum(int(by_spec_year[(spec, y)]["fatal_events"]) for y in (2015, 2016, 2017))
            i_sum = sum(int(by_spec_year[(spec, y)]["injury_events"]) for y in (2015, 2016, 2017))
            vkt_sum = sum(float(by_spec_year[(spec, y)]["modeled_vkt_billion_km"]) for y in (2015, 2016, 2017))
            self.assertEqual(int(r_15_17["fatal_events"]), f_sum)
            self.assertEqual(int(r_15_17["injury_events"]), i_sum)
            self.assertEqual(int(r_15_17["total_casualty_events"]), f_sum + i_sum)
            self.assertAlmostEqual(float(r_15_17["modeled_vkt_billion_km"]), vkt_sum, places=6)


class VehicleAgeTests(unittest.TestCase):
    def test_v_year_classification_and_age_buckets(self) -> None:
        self.assertEqual(
            classify_v_year_state("2018", 2020, 1, 1),
            ("valid_model_year_1950_to_cyear_plus_1", 2, "0_to_2_years"),
        )
        self.assertEqual(
            classify_v_year_state("2021", 2020, 1, 1),
            ("valid_model_year_1950_to_cyear_plus_1", -1, "0_next_model_year"),
        )
        self.assertEqual(
            classify_v_year_state("2022", 2020, 1, 1),
            ("implausible_future_gt_cyear_plus_1", None, "implausible_model_year"),
        )
        self.assertEqual(
            classify_v_year_state("1940", 2020, 1, 1),
            ("implausible_historical_lt_1950", None, "implausible_model_year"),
        )
        self.assertEqual(
            classify_v_year_state("UUUU", 2020, 1, 1),
            ("unknown_UUUU", None, "unknown_model_year"),
        )
        self.assertEqual(
            classify_v_year_state("NNNN", 2020, 1, 1),
            ("not_applicable_or_unavailable", None, "unknown_model_year"),
        )
        self.assertEqual(
            classify_v_year_state("2018", 2020, 2, 2),
            ("conflict_within_vtype08", None, "unknown_model_year"),
        )
        self.assertEqual(
            classify_v_year_state("2018", 2020, 1, 2),
            ("valid_model_year_with_cross_vtype_vid_conflict", 2, "0_to_2_years"),
        )

        self.assertEqual(age_to_cohort(-1), "0_next_model_year")
        self.assertEqual(age_to_cohort(0), "0_to_2_years")
        self.assertEqual(age_to_cohort(2), "0_to_2_years")
        self.assertEqual(age_to_cohort(3), "3_to_5_years")
        self.assertEqual(age_to_cohort(6), "6_to_10_years")
        self.assertEqual(age_to_cohort(11), "11_to_15_years")
        self.assertEqual(age_to_cohort(16), "16_plus_years")
        self.assertEqual(age_to_cohort(None, False), "unknown_model_year")
        self.assertEqual(age_to_cohort(None, True), "implausible_model_year")

    def test_wilson_ci_and_weighted_logistic_irls(self) -> None:
        lo, hi = wilson_ci_pct(72, 1000)
        self.assertIsNotNone(lo)
        self.assertIsNotNone(hi)
        self.assertLess(lo, 7.2)
        self.assertGreater(hi, 7.2)
        self.assertEqual(wilson_ci_pct(0, 0), (None, None))

        # Two-group exact log-odds check: group 0 (ref) p0 = 0.10, group 1 p1 = 0.20 -> OR = (0.2/0.8)/(0.1/0.9) = 2.25
        X = np.array(
            [
                [1.0, 0.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [1.0, 1.0],
            ],
            dtype=float,
        )
        y = np.array([1.0, 0.0, 1.0, 0.0], dtype=float)
        w = np.array([100.0, 900.0, 200.0, 800.0], dtype=float)
        beta, se = fit_weighted_logistic_irls(X, y, w)
        self.assertAlmostEqual(math.exp(beta[1]), 2.25, places=6)
        expected_se = math.sqrt(1 / 100 + 1 / 900 + 1 / 200 + 1 / 800)
        self.assertAlmostEqual(se[1], expected_se, places=5)

    @unittest.skipUnless(
        (PROJECT_ROOT / "data/derived/casualties/record_alternatives.parquet").exists()
        and (PROJECT_ROOT / "data/derived/ncdb/road_tractor_collisions.parquet").exists(),
        "Derived casualty and road-tractor collision Parquet tables required",
    )
    def test_vehicle_age_outputs_and_reconciliation(self) -> None:
        summary = run_vehicle_age_analysis(PROJECT_ROOT)
        self.assertEqual(summary["total_tractor_vehicles_1999_2021"], 86154)
        self.assertEqual(summary["total_tractor_events_1999_2021"], 80540)
        self.assertEqual(summary["total_tractor_events_2012_2021"], 29496)

        audit_path = PROJECT_ROOT / "reports/tables/vehicle_age_audit.csv"
        cohort_path = PROJECT_ROOT / "reports/tables/vehicle_age_severity_cohorts.csv"
        multi_path = PROJECT_ROOT / "reports/tables/vehicle_age_multi_tractor_sensitivity.csv"
        figure_path = PROJECT_ROOT / "reports/figures/vehicle_age_conditional_severity.png"
        doc_path = PROJECT_ROOT / "docs/vehicle_age_severity.md"

        for p in (audit_path, cohort_path, multi_path, figure_path, doc_path):
            self.assertTrue(p.exists(), f"Missing expected artifact: {p}")
        self.assertGreater(figure_path.stat().st_size, 50_000)

        with audit_path.open(encoding="utf-8") as f_aud:
            audit_rows = list(csv.DictReader(f_aud))
        with cohort_path.open(encoding="utf-8") as f_coh:
            cohort_rows = list(csv.DictReader(f_coh))
        with multi_path.open(encoding="utf-8") as f_mul:
            multi_rows = list(csv.DictReader(f_mul))

        self.assertEqual(len(audit_rows), 28)
        self.assertEqual(len(cohort_rows), 32)
        self.assertEqual(len(multi_rows), 64)

        con = duckdb.connect()
        total_events_1999_2021, total_events_2012_2021 = con.execute(
            """
            SELECT
                count(*),
                count(*) FILTER (WHERE CAST(C_YEAR AS INTEGER) BETWEEN 2012 AND 2021)
            FROM read_parquet(?)
            """,
            [str(PROJECT_ROOT / "data/derived/ncdb/road_tractor_collisions.parquet")],
        ).fetchone()
        con.close()

        self.assertEqual(int(total_events_1999_2021), 80540)
        self.assertEqual(int(total_events_2012_2021), 29496)

        ordered_cohort_ids = [c[0] for c in AGE_COHORTS_ORDERED]
        for period, expected_events, expected_vehicles in (
            ("1999_2021", 80540, 86154),
            ("2012_2021", 29496, 32022),
        ):
            v_audit = [r for r in audit_rows if r["period"] == period and r["grain"] == "tractor_vehicle"]
            e_audit = [r for r in audit_rows if r["period"] == period and r["grain"] == "collision_event"]
            self.assertEqual(sum(int(r["total_count"]) for r in v_audit), expected_vehicles)
            self.assertEqual(sum(int(r["total_count"]) for r in e_audit), expected_events)

            obs_cohorts = [r for r in cohort_rows if r["period"] == period and r["subset"] == "observed"]
            self.assertEqual([r["age_cohort"] for r in obs_cohorts], ordered_cohort_ids)
            self.assertEqual(sum(int(r["total_casualty_events"]) for r in obs_cohorts), expected_events)
            self.assertAlmostEqual(sum(float(r["cohort_share_of_events_pct"]) for r in obs_cohorts), 100.0, places=4)

            for r in obs_cohorts:
                f_ev = int(r["fatal_events"])
                i_ev = int(r["injury_events"])
                t_ev = int(r["total_casualty_events"])
                self.assertEqual(f_ev + i_ev, t_ev)
                if t_ev > 0:
                    share = float(r["conditional_fatal_share_pct"])
                    lo = float(r["wilson_95_ci_low_pct"])
                    hi = float(r["wilson_95_ci_high_pct"])
                    self.assertLessEqual(lo, share + 1e-6)
                    self.assertGreaterEqual(hi, share - 1e-6)

            for rule, expected_rule_total in (
                ("oldest_tractor", expected_events),
                ("newest_tractor", expected_events),
                ("vehicle_grain_all_tractors", expected_vehicles),
            ):
                rule_rows = [r for r in multi_rows if r["period"] == period and r["assignment_rule"] == rule]
                self.assertEqual(sum(int(r["total_casualty_events"]) for r in rule_rows), expected_rule_total)


if __name__ == "__main__":
    unittest.main()
