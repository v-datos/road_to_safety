import unittest
from truck_collisions.decompose_configuration import components


class DecompositionTests(unittest.TestCase):
    def total(self, rows, field):
        return sum(r[field] or 0 for r in rows)

    def test_pure_mix(self):
        rows = components({'a': (80, 8), 'b': (20, 10)}, {'a': (20, 2), 'b': (80, 40)})
        self.assertAlmostEqual(self.total(rows, 'mix_pp'), 24)
        self.assertAlmostEqual(self.total(rows, 'within_pp'), 0)

    def test_pure_within(self):
        rows = components({'a': (80, 8), 'b': (20, 10)}, {'a': (80, 16), 'b': (20, 12)})
        self.assertAlmostEqual(self.total(rows, 'mix_pp'), 0)
        self.assertAlmostEqual(self.total(rows, 'within_pp'), 10)

    def test_reconciliation_and_reversal(self):
        a, b = {'a': (80, 8), 'b': (20, 10)}, {'a': (30, 6), 'b': (40, 25)}
        forward, reverse = components(a, b), components(b, a)
        self.assertAlmostEqual(self.total(forward, 'net_pp'), 100*(31/70-18/100))
        self.assertAlmostEqual(self.total(forward, 'net_pp'), self.total(forward, 'mix_pp')+self.total(forward, 'within_pp'))
        for field in ('mix_pp', 'within_pp', 'net_pp'):
            self.assertAlmostEqual(self.total(forward, field), -self.total(reverse, field))

    def test_absence_does_not_invent_rates(self):
        rows = components({'a': (10, 1), 'z': (0, 0)}, {'b': (20, 4), 'z': (0, 0)})
        self.assertEqual(self.total(rows, 'unallocated_pp'), 10)
        z = next(r for r in rows if r['code']=='z')
        self.assertIsNone(z['fatal_share_a'])
        self.assertEqual(z['mix_pp'], 0)
        a = next(r for r in rows if r['code']=='a')
        self.assertIsNone(a['within_pp'])
        self.assertIsNone(a['fatal_share_b'])

    def test_invalid_counts_and_empty_period(self):
        with self.assertRaises(ValueError):
            components({'a': (1, 2)}, {'a': (1, 0)})
        with self.assertRaises(ValueError):
            components({}, {'a': (1, 0)})
