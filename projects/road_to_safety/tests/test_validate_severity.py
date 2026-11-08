"""Edge and mutation checks for independent severity reconciliation."""
import unittest

import numpy as np
import pandas as pd

from road_to_safety.validate_severity import (
    FEATURES, assert_values, expected_split, independent_metrics, recall_threshold,
    reconstruct_probability,
)


class SeverityValidationTests(unittest.TestCase):
    def test_year_boundaries_and_outside_population(self):
        self.assertEqual(expected_split([1999,2016,2017,2019,2020,2021]).tolist(),
            ['train','train','validation','validation','test','test'])
        with self.assertRaises(ValueError):
            expected_split([2022])

    def test_probability_domain_mutation(self):
        for invalid in [-.01, 1.01, np.nan, np.inf]:
            with self.assertRaises(ValueError):
                independent_metrics([0,1],[.1,invalid], .5)

    def test_tied_ranking_and_inclusive_confusion(self):
        result = independent_metrics([0,1,0,1],[.2,.2,.8,.8], .8)
        self.assertAlmostEqual(result['roc_auc'], .5)
        self.assertAlmostEqual(result['average_precision'], .5)
        self.assertEqual([result[k] for k in ['tn','fp','fn','tp']], [1,1,1,1])

    def test_threshold_precision_optimization_differs_from_highest_feasible(self):
        # At .8 recall is .8, precision .8; at .7 recall is 1 and precision 5/6.
        y = [1,1,1,1,0,1,0,0]
        p = [.99,.96,.93,.8,.85,.7,.6,.5]
        self.assertEqual(recall_threshold(y,p), .7)
        self.assertEqual(recall_threshold([1,1,0],[.8,.8,.8]), .8)
        self.assertEqual(recall_threshold([1,1,1,1,1,0],[.9,.8,.7,.6,.5,.1]), .6)

    def test_unsupported_features_and_changed_coefficients_detected(self):
        frame = pd.DataFrame({field:['1','2'] for field in FEATURES})
        model = {'features':FEATURES, 'intercept':0.,
            'encoded_features':[{'feature':'C_WTHR','code':'2'}], 'coefficients':[1.]}
        correct = reconstruct_probability(frame, model)
        self.assertAlmostEqual(correct[0], .5)
        self.assertAlmostEqual(correct[1], 1/(1+np.exp(-1)))
        model['coefficients'] = [2.]
        changed = reconstruct_probability(frame,model)
        with self.assertRaises(ValueError):
            assert_values({'score':changed[1]}, {'score':correct[1]})
        model['features'] = FEATURES + ['C_SEV']
        with self.assertRaises(ValueError):
            reconstruct_probability(frame,model)

    def test_zero_prediction_and_one_class_metrics(self):
        result = independent_metrics([0,0],[0,0], .5)
        self.assertTrue(np.isnan(result['roc_auc']))
        self.assertTrue(np.isnan(result['average_precision']))
        self.assertEqual(result['f1'],0)
        self.assertEqual(result['ece'],0)
        self.assertEqual(result['brier_score'],0)


if __name__ == '__main__':
    unittest.main()
