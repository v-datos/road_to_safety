"""Numerical and semantic checks for descriptive condition summaries."""
import math
import unittest

import pandas as pd

from road_to_safety.analyze_conditions import classify, enrich, label, wilson


class ConditionTests(unittest.TestCase):
    def test_wilson_hand_calculation_and_boundaries(self):
        lower, upper = wilson(5, 10)
        self.assertAlmostEqual(lower, 0.236593090512564)
        self.assertAlmostEqual(upper, 0.763406909487436)
        self.assertEqual(wilson(0, 10)[0], 0)
        self.assertAlmostEqual(wilson(10, 10)[1], 1)
        self.assertTrue(math.isnan(wilson(0, 0)[0]))

    def test_unknown_other_and_sparse_denominators(self):
        frame = enrich(pd.DataFrame({'field': ['C_RSUR']*3, 'code': ['1', 'U', 'Q'],
            'collisions': [1000, 200, 101], 'fatal_collisions': [20, 4, 5]}))
        self.assertEqual(list(frame.value_class), ['stated', 'unknown', 'other'])
        self.assertEqual(list(frame.injury_collisions), [980, 196, 96])
        self.assertEqual(list(frame.sparse_n_lt_100_or_fatal_lt_5), [False, True, False])
        self.assertEqual(list(frame.fatal_proportion), [0.02, 0.02, 5/101])
        self.assertEqual(classify('XX'), 'jurisdiction_unavailable')
        self.assertEqual(label('C_RSUR', '6'), 'Sand/gravel/dirt debris')
        self.assertEqual(label('C_TRAF', '13'), 'Stopped school bus, signals flashing')
        self.assertEqual(label('C_TRAF', '14'), 'Stopped school bus, signals not flashing')


if __name__ == '__main__':
    unittest.main()
