"""Protect distinctions that affect missingness and usable denominators."""
import json
from pathlib import Path
import unittest

from truck_collisions.audit_conditions import classify, variation

BOOK = json.loads((Path(__file__).resolve().parents[1] /
                   'data/reference/collision_codebook.json').read_text())['fields']


class ConditionQualityTests(unittest.TestCase):
    def test_midnight_is_observed_but_zero_month_and_vehicle_count_are_invalid(self):
        self.assertEqual(classify('00', BOOK['C_HOUR']), 'defined')
        self.assertEqual(classify('00', BOOK['C_MNTH']), 'unexpected')
        self.assertEqual(classify('00', BOOK['C_VEHS']), 'unexpected')

    def test_other_and_defined_other_configuration_are_not_unknown(self):
        self.assertEqual(classify('Q', BOOK['C_RSUR']), 'other')
        self.assertEqual(classify('06', BOOK['C_CONF']), 'defined')
        self.assertEqual(classify('UU', BOOK['C_CONF']), 'unknown')
        self.assertEqual(classify('XX', BOOK['C_CONF']), 'not_provided')

    def test_code_width_and_nonstandard_values_are_not_silently_coerced(self):
        self.assertEqual(classify('XX', BOOK['C_RSUR']), 'unexpected')
        self.assertEqual(classify('NN', BOOK['C_CONF']), 'unexpected')
        self.assertEqual(classify('**', BOOK['C_VEHS']), 'unexpected')
        self.assertEqual(classify('99', BOOK['C_VEHS']), 'top_coded')

    def test_conflict_null_and_absent_value_remain_distinct(self):
        self.assertEqual(classify(None, BOOK['C_VEHS'], conflict=True), 'conflict_null')
        self.assertEqual(classify(None, BOOK['C_VEHS']), 'null_or_blank')

    def test_distribution_shift_uses_proportions_and_retains_unknowns(self):
        before = {('1', 'defined'): 9, ('U', 'unknown'): 1}
        scaled = {('1', 'defined'): 90, ('U', 'unknown'): 10}
        changed = {('1', 'defined'): 5, ('U', 'unknown'): 5}
        self.assertEqual(variation(before, scaled), 0)
        self.assertAlmostEqual(variation(before, changed), .4)


if __name__ == '__main__':
    unittest.main()
