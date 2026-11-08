"""Protocol-relevant failure and numerical boundary cases; no fitting."""
import unittest
import numpy as np
import pandas as pd
from road_to_safety.score_calibration_stress_v1 import score_json, probability_metrics, reliability, assess_transfer


class StressTests(unittest.TestCase):
    def test_score_preserves_unknown_column_and_rejects_unsupported(self):
        model = {'features': ['f'], 'categories': {'f': ['1','U']}, 'intercept': -2.,
                 'encoded_features': [{'feature':'f','code':'U'}], 'coefficients': [.5]}
        np.testing.assert_array_equal(score_json(model, pd.DataFrame({'f':['U','1']})), [-1.5,-2.])
        with self.assertRaises(ValueError):
            score_json(model, pd.DataFrame({'f':['unsupported']}))

    def test_empty_oneclass_and_extreme_probabilities(self):
        empty = probability_metrics([], [])
        self.assertEqual(empty['n'], 0)
        self.assertIsNone(empty['log_loss'])
        oneclass = probability_metrics([1], [0])
        self.assertIsNone(oneclass['roc_auc'])
        self.assertIsNone(oneclass['average_precision'])
        self.assertTrue(np.isfinite(oneclass['log_loss']))
        with self.assertRaises(ValueError):
            probability_metrics([0,1], [0,np.nan])

    def test_bins_include_endpoints_and_retain_empty(self):
        rows = reliability(np.array([0,1,1]), np.array([0,.5,1]), [0,.25,.5,.75,1])
        self.assertEqual([r['n'] for r in rows], [1,0,1,1])
        self.assertIsNone(rows[1]['mean_prediction'])
        self.assertEqual(sum(r['fatal'] for r in rows), 2)

    def test_transfer_requires_both_years_but_not_aggregate_gap(self):
        records = []
        for year in ('2020','2021'):
            records.extend([{'population':year,'group':'all','method':'unchanged','log_loss':.1,'brier_score':.02,'prediction_minus_observed':0},
                            {'population':year,'group':'all','method':'sigmoid','log_loss':.09,'brier_score':.019,'prediction_minus_observed':.01}])
        frame = pd.DataFrame(records)
        self.assertEqual(assess_transfer(frame)['assessment'], 'favorable_descriptive_transfer')
        frame.loc[(frame.population == '2021') & (frame.method == 'sigmoid'), 'brier_score'] = .021
        self.assertEqual(assess_transfer(frame)['assessment'], 'transfer_not_demonstrated')


if __name__ == '__main__':
    unittest.main()
