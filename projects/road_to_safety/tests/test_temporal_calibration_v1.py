import unittest
import numpy as np
import pandas as pd
from scipy.special import expit
from road_to_safety.fit_temporal_calibration_v1 import fit_calibrator, probability_metrics, reliability, select_method

class TemporalCalibrationTests(unittest.TestCase):
    def test_intercept_fit_matches_calibration_prevalence(self):
        z=np.tile(np.array([-4.,-3.,-2.,-1.]),100)
        y=np.zeros(400); y[::10]=1
        result=fit_calibrator(z,y,'intercept_only')
        self.assertAlmostEqual(expit(z+result['intercept']).mean(),y.mean(),places=7)
        self.assertEqual(result['slope'],1.)

    def test_sigmoid_fit_has_small_projected_gradient(self):
        z=np.tile(np.array([-4.,-3.,-2.,-1.]),100)
        y=np.zeros(400); y[::10]=1; y[3::20]=1
        result=fit_calibrator(z,y,'sigmoid')
        self.assertGreaterEqual(result['slope'],1e-6)
        self.assertLessEqual(result['max_abs_projected_gradient'],1e-6)

    def test_reliability_preserves_empty_and_endpoint_bins(self):
        rows=reliability(np.array([0,1]),np.array([0.,1.]),[0,.5,.75,1])
        self.assertEqual([r['n'] for r in rows],[1,0,1])
        self.assertIsNone(rows[1]['mean_prediction'])

    def test_selection_requires_four_improved_years_and_brier_guardrail(self):
        rows=[]
        for year in range(2014,2020):
            for name in ('unchanged','intercept_only','sigmoid'):
                rows.append({'eval_year':year,'phase':'evaluation','group':'all','method':name,
                    'log_loss':.1 if name=='unchanged' else .09,
                    'brier_score':.01 if name!='sigmoid' else .011})
        selected=select_method(pd.DataFrame(rows))
        self.assertEqual(selected['selected_method'],'intercept_only')
        self.assertFalse(next(r for r in selected['candidates'] if r['method']=='sigmoid')['eligible'])

    def test_lower_mean_alone_is_insufficient(self):
        rows=[]
        for year in range(2014,2020):
            for name in ('unchanged','intercept_only','sigmoid'):
                score=.1 if name=='unchanged' else (.08 if year<2017 else .101)
                rows.append({'eval_year':year,'phase':'evaluation','group':'all','method':name,
                    'log_loss':score,'brier_score':.01})
        selected=select_method(pd.DataFrame(rows))
        self.assertEqual(selected['selected_method'],'unchanged')

    def test_one_class_calibration_fails(self):
        with self.assertRaises(ValueError): fit_calibrator(np.array([-2.,-1.]),np.array([0,0]),'sigmoid')

    def test_probability_metrics_reject_nonfinite(self):
        with self.assertRaises(ValueError): probability_metrics([0,1],[0,np.nan])

if __name__=='__main__': unittest.main()
