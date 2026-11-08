"""Protect event denominators and prevent complete-case or time interpretation drift."""
from collections import Counter
import json
from pathlib import Path
import unittest

from truck_collisions.analyze_conditions import category, distribute, domain, hour_band, partitions, percentage

BOOK = json.loads((Path(__file__).resolve().parents[1] /
                   'data/reference/collision_codebook.json').read_text())['fields']


class ConditionComparisonTests(unittest.TestCase):
    def test_unknown_and_other_stay_in_all_event_denominator(self):
        spec = BOOK['C_WTHR']
        counts = Counter({category('1', spec): 6, category('3', spec): 2,
                          category('Q', spec): 1, category('U', spec): 1})
        rows = {r['code']: r for r in distribute(counts, domain(spec))}
        self.assertEqual(rows['1']['events'], 10)
        self.assertEqual(rows['1']['share_pct'], 60)
        self.assertEqual(rows['1']['named_events'], 8)
        self.assertEqual(rows['1']['named_share_pct'], 75)
        self.assertEqual(rows['Q']['status'], 'other')
        self.assertIsNone(rows['Q']['named_share_pct'])
        self.assertIsNone(rows['U']['named_share_pct'])
        self.assertEqual(rows['7']['code_events'], 0)
        self.assertEqual(rows['7']['share_pct'], 0)
        self.assertEqual(sum(r['code_events'] for r in rows.values()), 10)

    def test_no_observations_does_not_imply_zero_fatal_share(self):
        self.assertIsNone(percentage(0, 0))
        self.assertEqual(percentage(0, 5), 0)
        self.assertEqual(percentage(2, 10), 20)
        rows = distribute(Counter(), domain(BOOK['C_RSUR']))
        self.assertTrue(all(r['share_pct'] is None for r in rows))

    def test_midnight_and_unknown_clock_values_are_not_lighting(self):
        self.assertEqual(hour_band('00'), '00–05')
        self.assertEqual(hour_band('05'), '00–05')
        self.assertEqual(hour_band('06'), '06–11')
        self.assertEqual(hour_band('17'), '12–17')
        self.assertEqual(hour_band('23'), '18–23')
        self.assertEqual(hour_band('UU'), 'UU')
        self.assertIsNone(hour_band(None))
        self.assertEqual(hour_band('24'), '24')

    def test_defined_other_and_residual_unknown_remain_distinct(self):
        spec = BOOK['C_CONF']
        self.assertEqual(category('06', spec)[1], 'defined')
        self.assertEqual(category('QQ', spec)[1], 'other')
        self.assertEqual(category('UU', spec)[1], 'unknown')
        self.assertEqual(category(None, spec, True)[1], 'conflict_null')
        self.assertEqual(category(None, spec)[1], 'null_or_blank')

    def test_strict_is_a_subset_for_each_cohort_not_a_new_comparator(self):
        self.assertEqual(list(partitions(False, False, '2')),
            [('no_recorded_tractor', 'observed', 'all'),
             ('no_recorded_tractor', 'observed', 'injury')])
        selected = list(partitions(True, True, '1'))
        self.assertEqual(len(selected), 4)
        self.assertIn(('tractor', 'strict', 'fatal'), selected)
        self.assertNotIn(('no_recorded_tractor', 'observed', 'all'), selected)


if __name__ == '__main__':
    unittest.main()
