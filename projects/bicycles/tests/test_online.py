import csv
from pathlib import Path
import unittest

from bicycle_collisions.online import parse_dom,validate_partitions


class OnlineTests(unittest.TestCase):
    def test_incomplete_period_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_dom([['Year','2023'],[],[]],'fixture')

    def test_missing_or_overlapping_category_counts_are_rejected(self):
        rows=[dict(dataset='fixture',year=2020,measure='injured',category='Total',count=10),
              dict(dataset='fixture',year=2020,measure='injured',category='Known',count=9)]
        with self.assertRaises(ValueError):validate_partitions(rows)

    def test_archived_complete_profiles_reconcile_to_their_own_grain(self):
        path=Path(__file__).resolve().parents[1]/'data/reference/ncdb_online_bicycles_2010_2023.csv'
        with path.open() as stream:
            rows=[{**r,'year':int(r['year']),'count':int(r['count'])} for r in csv.DictReader(stream)]
        totals=validate_partitions(rows)
        self.assertEqual(len(totals),462)
        self.assertEqual(totals['road_user_annual',2020,'fatalities'],54)
        self.assertEqual(totals['annual_bicycle_2010_2023',2020,'fatalities'],50)


if __name__=='__main__':
    unittest.main()
