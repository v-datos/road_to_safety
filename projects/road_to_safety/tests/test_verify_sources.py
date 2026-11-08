import csv
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from road_to_safety.verify_sources import compare_benchmarks, verify


class SourceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write_json(self, relative, payload):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))

    def write_csv(self, relative, rows):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_changed_catalog_is_rejected(self):
        self.write_json("data/sources.json", {"catalog_id": "ncdb", "resources": []})
        self.write_json("data/reference/aggregate_sources.json", {"sources": [], "extracts": []})
        self.write_json("data/raw/source_metadata/ncdb_catalog.provenance.json", {
            "url": "https://example.org/catalog", "sha256": hashlib.sha256(b"original").hexdigest(),
        })
        (self.root / "data/raw/source_metadata/ncdb_catalog.json").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            verify(self.root)

    def benchmark_fixture(self, audited_years):
        self.write_json("data/sources.json", {"resources": [
            {"year": year, "local_path": f"{year}.csv"} for year in (2020, 2021)
        ]})
        self.write_csv("reports/tables/record_annual_quality.csv", [
            {"year": year, "source_path": f"{year}.csv", "selected": True,
             "fatal_collisions": 10, "injury_collisions": 100} for year in audited_years
        ])
        self.write_csv("data/reference/aggregate_national_annual_2024_vintage.csv", [
            {"year": 2020, "fatal_collisions": 12, "injury_collisions": 100}
        ])

    def test_partial_audit_is_rejected(self):
        self.benchmark_fixture([2020])
        with self.assertRaisesRegex(ValueError, "must finish"):
            compare_benchmarks(self.root)

    def test_comparison_preserves_source_disagreement(self):
        self.benchmark_fixture([2020, 2021])
        rows = compare_benchmarks(self.root)
        self.assertEqual(rows[0]["record_count"], 10)
        self.assertEqual(rows[0]["published_2024_vintage_count"], 12)
        self.assertEqual(rows[0]["difference"], -2)
        self.assertEqual(rows[0]["status"], "unresolved_difference")
        self.assertEqual(rows[1]["status"], "equal")


if __name__ == "__main__":
    unittest.main()
