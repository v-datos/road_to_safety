"""Mutations targeting retrospective stress-test leakage and transfer claims."""
import copy
import unittest

import numpy as np
import pandas as pd

from road_to_safety.validate_calibration_stress_v1 import (
    FEATURES, assert_values, compare_metrics, frozen_parameters, group_masks,
    probability_metrics, score_logit, sigmoid, transfer_assessment, validate_population,
)


class CalibrationStressAuditTests(unittest.TestCase):
    def annual(self):
        return pd.DataFrame([{'population':str(year),'method':method,
            'log_loss':loss,'brier_score':.01}
            for year in [2020,2021] for method,loss in
            [('unchanged',.1),('sigmoid',.09),('prevalence',.2)]])

    def test_annual_both_year_rule_and_tolerance_not_pooled(self):
        annual=self.annual()
        self.assertEqual(transfer_assessment(annual),'favorable_descriptive_transfer')
        annual.loc[annual.population.eq('2021') & annual.method.eq('sigmoid'),'log_loss']=.11
        self.assertEqual(transfer_assessment(annual),'transfer_not_demonstrated')
        annual=self.annual()
        annual.loc[annual.method.eq('sigmoid'),'brier_score']=.011
        self.assertEqual(transfer_assessment(annual),'transfer_not_demonstrated')
        annual=self.annual()
        annual.loc[annual.method.eq('sigmoid'),'log_loss']=.1-5e-11
        self.assertEqual(transfer_assessment(annual),'transfer_not_demonstrated')
        for invalid in [annual.iloc[:-1],pd.concat([annual,annual.iloc[:1]]),
            annual.assign(population='2019')]:
            with self.assertRaises(ValueError):
                transfer_assessment(invalid)

    def test_immutable_model_calibrator_and_development_selection(self):
        model={'intercept':-4.,'coefficients':[.2], 'calibrators':{'sigmoid':{'slope':.9,'intercept':-.1}}}
        protocol={'frozen_model_parameters':{'intercept':-4.,'coefficients':[.2]},
            'frozen_sigmoid_parameters':{'slope':.9,'intercept':-.1},'selected_method':'sigmoid'}
        frozen_parameters(model,protocol)
        for change in ['coefficient','slope','selection']:
            altered_model,altered_protocol=copy.deepcopy(model),copy.deepcopy(protocol)
            if change=='coefficient': altered_model['coefficients']=[-.2]
            elif change=='slope': altered_model['calibrators']['sigmoid']['slope']=-.9
            else: altered_protocol['selected_method']='unchanged'
            with self.assertRaises(ValueError):
                frozen_parameters(altered_model,altered_protocol)

    def test_quality_flags_overlap_and_zero_unavailable_groups_retained(self):
        frame=pd.DataFrame({field:['1','1','1'] for field in FEATURES})
        frame.loc[0,'C_WTHR']='U'
        frame.loc[0,'C_RSUR']='Q'
        frame['has_train_unobserved_level']=False
        masks=group_masks(frame)
        self.assertTrue(masks['has_unknown=True'][0] and masks['has_other=True'][0])
        self.assertEqual(int(masks['has_unavailable=True'].sum()),0)
        self.assertIn('C_HOUR:unavailable',masks)
        self.assertNotIn('contains_unknown_or_unavailable',masks)

    def test_tie_aware_ranking_and_corrupted_probabilities(self):
        y=[0,1,0,1]
        metrics=probability_metrics(y,[.1,.1,.8,.8])
        self.assertAlmostEqual(metrics['roc_auc'],.5)
        self.assertAlmostEqual(metrics['average_precision'],.5)
        for value in [np.nan,np.inf,-.01,1.01]:
            with self.assertRaises(ValueError):
                probability_metrics([0,1],[.2,value])
        with self.assertRaises(ValueError):
            probability_metrics([0,2],[.1,.9])

    def test_empty_group_undefined_scores_and_sparse_not_excluded(self):
        row={'n':0,'fatal':0,'nonfatal':0,'sparse_n_lt_100_or_fatal_lt_5':True}
        row.update(dict.fromkeys(['observed_prevalence','mean_prediction','prediction_minus_observed',
            'observed_expected_ratio','log_loss','brier_score','average_precision','roc_auc'],np.nan))
        compare_metrics(row,[],[])
        row['roc_auc']=0.
        with self.assertRaises(ValueError): compare_metrics(row,[],[])

    def test_coefficient_mutation_and_unexpected_year_rejected(self):
        frame=pd.DataFrame({field:['1','2'] for field in FEATURES})
        model={'features':FEATURES,'intercept':-2.,'encoded_features':[{'feature':'C_WTHR','code':'2'}],
            'coefficients':[1.]}
        correct=sigmoid(score_logit(frame,model))
        model['coefficients']=[-1.]
        with self.assertRaises(ValueError):
            assert_values({'p':sigmoid(score_logit(frame,model))[1]},{'p':correct[1]})
        source=pd.DataFrame({'source_id':['x'],'C_YEAR':['2019'],'C_CASE':['1'],
            'severity_eligible':[True],'is_fatal':[0]})
        with self.assertRaises(ValueError): validate_population(source)


if __name__=='__main__':
    unittest.main()
