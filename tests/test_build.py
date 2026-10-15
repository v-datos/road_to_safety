import csv
import tempfile
import unittest
from pathlib import Path

import duckdb

from truck_collisions.build import COLUMNS, FRENCH_HEADERS, build_dataset
from openpyxl import Workbook


def record(case, **changes):
    row = dict(zip(COLUMNS, "2019 1 1 12 2 2 32 1 1 1 1 1 1 1 2015 1 M 40 11 1 2 1 1".split()))
    row["C_CASE"] = case
    row.update(changes)
    return row


class CollisionBuildTests(unittest.TestCase):
    def test_event_grain_codes_ambiguity_and_cross_year_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/reference").mkdir(parents=True)
            (root / "data/reference/tractor_collision_benchmark.csv").write_text(
                "year,fatal_collisions,injury_collisions\n2019,0,6\n2020,0,1\n")
            rows = [
                record("1", V_TYPE="8"),
                record("1", V_TYPE="08", P_ID="2"),
                record("1", V_TYPE="8"),  # Exact duplicate after normalization.
                record("1", V_TYPE="08", V_ID="2"),  # Second tractor, same event.
                record("2", V_TYPE="1"),
                record("2", V_TYPE="1", P_ISEV="2"),  # Conflicting person, stable event.
                record("2", V_TYPE="08", V_ID="2"),  # Tractor is not first vehicle.
                record("3", V_TYPE="08"),
                record("3", V_TYPE="08", C_WTHR="2", P_ID="2"),  # Conflicting event field.
                record("4", V_TYPE="08"),
                record("4", V_TYPE="01"),  # Conflicting tractor classification.
                record("5", V_TYPE="08", V_ID="*", C_VEHS="**", P_ID="UU"),
                record("6", V_TYPE="01", V_ID="99", P_ID="NN"),  # Dummy is not a vehicle.
                record("7", V_TYPE="08", V_ID="123"),  # Must not truncate a long ID.
            ]
            sources = []
            for year, source_rows in [(2019, rows), (2020, [record("1", C_YEAR="2020", V_TYPE="08")])]:
                path = root / f"{year}.csv"
                with path.open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                    writer.writeheader()
                    writer.writerows(source_rows)
                sources.append(dict(id=str(year), path=path.name, first_year=year, last_year=year))
            output = root / "output"
            summary = build_dataset(root, sources, output)
            con = duckdb.connect()
            tractor = con.execute("SELECT C_YEAR,C_CASE,road_tractor_vehicle_count FROM read_parquet(?) ORDER BY 1,2", [str(output / "road_tractor_collisions_strict.parquet")]).fetchall()
            self.assertEqual(tractor, [(2019,"1",2),(2019,"2",1),(2019,"5",0),(2019,"7",0),(2020,"1",1)])
            self.assertTrue(summary["checks"]["collision_key_unique"])
            self.assertEqual(summary["checks"]["excluded_tractor_events"], 2)
            self.assertEqual(summary["checks"]["external_mismatch_years"], [])
            self.assertEqual(con.execute("SELECT count(*) FROM read_parquet(?)", [str(output / "road_tractor_collisions.parquet")]).fetchone()[0],7)
            one = con.execute("SELECT input_record_rows,distinct_record_rows FROM read_parquet(?) WHERE C_YEAR=2019 AND C_CASE='1'", [str(output / "collisions.parquet")]).fetchone()
            self.assertEqual(one, (4,3))
            dummy = con.execute("SELECT known_vehicle_count FROM read_parquet(?) WHERE C_CASE='6'", [str(output / "collisions.parquet")]).fetchone()[0]
            self.assertEqual(dummy, 0)
            person_conflicts = con.execute("SELECT person_attribute_conflict_count FROM read_parquet(?) WHERE C_YEAR=2019 AND C_CASE='2'", [str(output / "collisions.parquet")]).fetchone()[0]
            self.assertEqual(person_conflicts, 1)
            self.assertEqual(summary["status"], "partial_structural_exclusions_review_required")
            con.close()

    def test_overlapping_source_years_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "input.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerow(record("1", V_TYPE="08"))
            sources = [dict(id=str(i),path="input.csv",first_year=2019,last_year=2019) for i in range(2)]
            with self.assertRaisesRegex(ValueError, "Overlapping source years"):
                build_dataset(root, sources, root / "output")

    def test_official_xlsx_and_french_cp1252_schemas(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/reference").mkdir(parents=True)
            (root / "data/reference/tractor_collision_benchmark.csv").write_text(
                "year,fatal_collisions,injury_collisions\n2018,0,1\n2021,0,1\n")
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "in"
            sheet.append(COLUMNS)
            sheet.append(list(record("100", C_YEAR="2018", V_TYPE="8").values()))
            workbook.save(root / "2018.xlsx")
            with (root / "2021-fr.csv").open("w", encoding="cp1252", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(list(FRENCH_HEADERS))
                writer.writerow(list(record("200", C_YEAR="2021", V_TYPE="08").values()))
            sources = [
                dict(id="2018",path="2018.xlsx",sheet="in",first_year=2018,last_year=2018),
                dict(id="2021",path="2021-fr.csv",encoding="cp1252",first_year=2021,last_year=2021),
            ]
            summary = build_dataset(root, sources, root / "output")
            self.assertEqual([r["strict_tractor_collisions"] for r in summary["annual_counts"]], [1,1])
            self.assertEqual(summary["status"], "structurally_valid")

    def test_invalid_key_is_quarantined_and_build_is_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data/reference").mkdir(parents=True)
            (root / "data/reference/tractor_collision_benchmark.csv").write_text(
                "year,fatal_collisions,injury_collisions\n2019,0,1\n")
            with (root / "input.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerows([record("1", V_TYPE="08"), record("UU", V_TYPE="08")])
            summary = build_dataset(root, [dict(id="2019",path="input.csv",first_year=2019,last_year=2019)], root / "output")
            self.assertEqual(summary["checks"]["invalid_key_record_rows"], 1)
            self.assertEqual(summary["annual_counts"][0]["strict_tractor_collisions"], 1)
            self.assertEqual(summary["status"], "partial_structural_exclusions_review_required")


if __name__ == "__main__":
    unittest.main()
