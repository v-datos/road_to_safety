"""Mutations that target temporal leakage and score/calibration corruption."""
import unittest
import numpy as np
import pandas as pd
from road_to_safety.validate_temporal_calibration_v1 import (
    FEATURES, assert_values, bin_evidence, calibration_gradient, fold_partition, independent_selection,
    probability_metrics, score_logit, sigmoid,
)


class TemporalCalibrationAuditTests(unittest.TestCase):
    def test_temporal_exclusion_and_fold_boundaries(self):
        self.assertEqual(fold_partition([1998,1999,2011,2012,2013,2014,2015,2020],2014).tolist(),
            ['excluded','train','train','calibration','calibration','evaluation','excluded','excluded'])
        self.assertEqual(fold_partition([2016,2017,2018,2019,2020],2019).tolist(),
            ['train','calibration','calibration','evaluation','excluded'])
        with self.assertRaises(ValueError):
            fold_partition([2020],2020)

    def test_independent_tie_aware_ranking_and_probability_domain(self):
        metrics = probability_metrics([0,1,0,1],[.2,.2,.8,.8])
        self.assertAlmostEqual(metrics['roc_auc'],.5)
        self.assertAlmostEqual(metrics['average_precision'],.5)
        for value in [-.01,1.01,np.nan,np.inf]:
            with self.assertRaises(ValueError):
                probability_metrics([0,1],[.1,value])

    def test_coefficient_corruption_and_outcome_leakage_rejected(self):
        frame = pd.DataFrame({feature:['1','2'] for feature in FEATURES})
        model = {'features':FEATURES,'intercept':-2.,'encoded_features':
            [{'feature':'C_WTHR','code':'2'}],'coefficients':[1.]}
        expected = score_logit(frame,model)
        model['coefficients'] = [-1.]
        with self.assertRaises(ValueError):
            assert_values({'z':score_logit(frame,model)[1]}, {'z':expected[1]})
        model['encoded_features'] = [{'feature':'is_fatal','code':'1'}]
        with self.assertRaises(ValueError):
            score_logit(frame,model)

    def test_calibration_sign_flip_fails_likelihood_stationarity(self):
        z = np.array([-2.,-2.,0.,0.])
        # Exact group response probabilities are expit(z + log(3)).
        y = np.array([.28876540577240617,.28876540577240617,.75,.75])
        correct = calibration_gradient(y,z,1.,np.log(3.))
        self.assertLess(abs(correct[0]),1e-14)
        wrong = calibration_gradient(y,z,1.,-np.log(3.))
        self.assertGreater(abs(wrong[0]),.1)

    def test_selection_requires_pairing_consistency_and_brier_guardrail(self):
        rows = [{'evaluation_year':year,'method':method,'log_loss':loss,'brier_score':.01}
            for year in range(2014,2020) for method,loss in
            [('prevalence',.2),('unchanged',.1),('intercept_only',.09),('sigmoid',.08)]]
        annual = pd.DataFrame(rows)
        self.assertEqual(independent_selection(annual),'sigmoid')
        annual.loc[annual.method=='sigmoid','brier_score'] = .02
        self.assertEqual(independent_selection(annual),'intercept_only')
        annual.loc[annual.method=='intercept_only','log_loss'] = [.05,.05,.05,.11,.11,.11]
        self.assertEqual(independent_selection(annual),'unchanged')
        annual.loc[annual.method=='intercept_only','log_loss'] = .1
        self.assertEqual(independent_selection(annual),'unchanged')
        with self.assertRaises(ValueError):
            independent_selection(annual.iloc[:-1])
        with self.assertRaises(ValueError):
            independent_selection(pd.concat([annual,annual.iloc[:1]]))

    def test_bin_boundaries_empty_bins_and_sparse_flags(self):
        rows=bin_evidence([0,1,0,1],[0.,.1,.2,1.],[0.,.1,.2,.3,1.])
        self.assertEqual([row['n'] for row in rows],[1,1,1,1])
        self.assertEqual([row['fatal'] for row in rows],[0,1,0,1])
        self.assertTrue(all(row['sparse'] for row in rows))
        empty=bin_evidence([0],[.1],[0.,.1,.2])[0]
        self.assertEqual(empty['n'],0)
        self.assertTrue(np.isnan(empty['mean_prediction']))

    def test_extreme_sigmoid_is_finite_monotone(self):
        values = sigmoid([-10000.,-1.,0.,1.,10000.])
        self.assertTrue(np.isfinite(values).all())
        self.assertTrue((np.diff(values)>0).all())
        np.testing.assert_equal(values[[0,-1]],[0.,1.])


if __name__ == '__main__':
    unittest.main()
