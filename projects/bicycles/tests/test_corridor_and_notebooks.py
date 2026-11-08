import csv
import json
from pathlib import Path
import unittest

from bicycle_collisions.corridor_exposure_link import (
    compute_national_co_involved_lethality,
    run_corridor_exposure_link,
)

ROOT = Path(__file__).resolve().parents[1]


class CorridorAndNotebooksTests(unittest.TestCase):
    def test_corridor_exposure_tables_and_figure_exist_and_reconcile(self):
        summary = run_corridor_exposure_link(ROOT)
        class_csv = ROOT / "reports/tables/toronto_cyclist_corridor_exposure_by_class.csv"
        corridors_csv = ROOT / "reports/tables/toronto_top_cyclist_ksi_corridors.csv"
        fig_png = ROOT / "reports/figures/cyclist_corridor_exposure_synthesis.png"

        self.assertTrue(class_csv.exists())
        self.assertTrue(corridors_csv.exists())
        self.assertTrue(fig_png.exists())
        self.assertGreater(fig_png.stat().st_size, 50_000)
        self.assertEqual(fig_png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

        with class_csv.open() as stream:
            class_rows = list(csv.DictReader(stream))
        by_class = {r["road_class"]: r for r in class_rows}
        for required_class in ["Major Arterial", "Minor Arterial", "Collector", "Local", "Expressway"]:
            self.assertIn(required_class, by_class)

        self.assertAlmostEqual(float(by_class["Major Arterial"]["cyclist_ksi_per_100m_vkt"]), 0.519, places=3)
        self.assertAlmostEqual(float(by_class["Major Arterial"]["cyclist_ksi_per_km"]), 0.674, places=3)
        self.assertAlmostEqual(float(by_class["Minor Arterial"]["cyclist_ksi_per_100m_vkt"]), 0.751, places=3)
        self.assertAlmostEqual(float(by_class["Minor Arterial"]["cyclist_ksi_per_km"]), 0.485, places=3)
        self.assertEqual(sum(int(r["cyclist_ksi_crashes"]) for r in class_rows), 543)
        self.assertEqual(sum(int(r["network_cyclist_ksi_crashes"]) for r in class_rows), 935)

        with corridors_csv.open() as stream:
            corridor_rows = list(csv.DictReader(stream))
        top15_by_count = [
            r for r in corridor_rows if r["rank_by_cyclist_ksi"] and int(r["rank_by_cyclist_ksi"]) <= 15
        ]
        top15_by_rate = [
            r for r in corridor_rows if r["rank_by_cyclist_rate"] and int(r["rank_by_cyclist_rate"]) <= 15
        ]
        self.assertEqual(len(top15_by_count), 15)
        self.assertEqual(len(top15_by_rate), 15)

        names = {r["LINEAR_NAME_FULL"] for r in corridor_rows}
        for expected_street in [
            "Bloor St W",
            "Spadina Ave",
            "Danforth Ave",
            "Yonge St",
            "St Clair Ave W",
            "Davenport Rd",
            "College St",
            "Harbord St",
        ]:
            self.assertIn(expected_street, names)

        self.assertEqual(summary["national_ncdb_synthesis"]["unique_bicycle_collisions_2010_2021"], 68687)
        self.assertAlmostEqual(
            summary["national_ncdb_synthesis"]["light_duty_co_involvement_share_pct"], 89.82, places=2
        )
        self.assertAlmostEqual(
            summary["national_typology_model_bicyclist"]["test_2020_2021_m0_roc_auc"], 0.6810, places=4
        )
        self.assertAlmostEqual(
            summary["national_typology_model_bicyclist"]["test_2020_2021_m2_roc_auc"], 0.7576, places=4
        )

    def test_national_co_involved_lethality_multipliers(self):
        rows = compute_national_co_involved_lethality(ROOT)
        by_group = {r["vehicle_group"]: r for r in rows}
        self.assertEqual(by_group["Light-duty vehicle"]["collisions"], 61698)
        self.assertAlmostEqual(by_group["Light-duty vehicle"]["fatality_rate_pct"], 0.708, places=3)
        self.assertEqual(by_group["Heavy unit truck"]["collisions"], 1102)
        self.assertEqual(by_group["Heavy unit truck"]["fatal_collisions"], 84)
        self.assertGreater(by_group["Heavy unit truck"]["lethality_multiplier_vs_light_duty"], 10.0)
        self.assertEqual(by_group["Road tractor"]["collisions"], 307)
        self.assertEqual(by_group["Road tractor"]["fatal_collisions"], 41)
        self.assertGreater(by_group["Road tractor"]["lethality_multiplier_vs_light_duty"], 18.0)

    def test_three_companion_notebooks_exist_and_have_executed_outputs(self):
        expected_notebooks = [
            "01_bicycle_dataset_and_online_validation.ipynb",
            "02_bicyclist_casualty_and_condition_trends.ipynb",
            "03_corridor_exposure_and_vru_synthesis.ipynb",
        ]
        for nb_name in expected_notebooks:
            nb_path = ROOT / "notebooks" / nb_name
            self.assertTrue(nb_path.exists(), f"Missing notebook: {nb_name}")
            nb = json.loads(nb_path.read_text())
            self.assertEqual(nb.get("nbformat"), 4)
            code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
            self.assertGreaterEqual(len(code_cells), 3)
            for idx, cell in enumerate(code_cells, 1):
                self.assertIsNotNone(cell.get("execution_count"), f"{nb_name} code cell {idx} unexecuted")
                outputs = cell.get("outputs", [])
                self.assertGreater(len(outputs), 0, f"{nb_name} code cell {idx} has no outputs")
                text = "".join("".join(o.get("text", [])) for o in outputs)
                self.assertGreater(len(text.strip()), 20, f"{nb_name} code cell {idx} output too short")


if __name__ == "__main__":
    unittest.main()
