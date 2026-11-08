"""Regression checks for domain-aware availability classification."""
import unittest

from road_to_safety.analyze_stability import classify


class AvailabilityClassificationTests(unittest.TestCase):
    def test_domain_meanings_remain_distinct(self):
        domain = ['1', 'Q', 'U', 'X']
        self.assertEqual(classify('1', False, domain), 'stated')
        self.assertEqual(classify('Q', False, domain), 'other')
        self.assertEqual(classify('U', False, domain), 'unknown')
        self.assertEqual(classify('X', False, domain), 'jurisdiction_unavailable')
        self.assertEqual(classify('N', False, domain), 'out_of_domain')
        self.assertEqual(classify('N', False, domain + ['N']), 'not_applicable')

    def test_conflict_is_not_misclassified_as_null(self):
        self.assertEqual(classify(None, True, ['1']), 'conflict')
        self.assertEqual(classify(None, False, ['1']), 'null')
        self.assertEqual(classify('', False, ['1']), 'blank')

    def test_undocumented_tokens_not_promoted_to_supported_states(self):
        self.assertEqual(classify('UU', False, ['1', 'U']), 'out_of_domain')
        self.assertEqual(classify('Q', False, ['1', 'QQ']), 'out_of_domain')
        self.assertEqual(classify('**', False, ['1']), 'unresolved_star_code')
        self.assertEqual(classify('2', False, ['1']), 'out_of_domain')


if __name__ == '__main__':
    unittest.main()
