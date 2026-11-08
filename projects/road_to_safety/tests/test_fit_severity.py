"""Boundary cases for the frozen baseline's threshold and metric definitions."""
import unittest
import numpy as np
from road_to_safety.fit_severity import validation_threshold, calibration, evaluate


class SeverityHelpersTest(unittest.TestCase):
    def test_precision_optimum_can_be_below_first_recall_eligible_threshold(self):
        # At .4 recall reaches .8 with precision4/6; lower .3 reaches1 at5/7.
        y = np.array([1,1,0,0,1,1,1])
        p = np.array([.9,.8,.7,.6,.5,.4,.3])
        self.assertEqual(validation_threshold(y,p), .3)

    def test_threshold_ties_are_inclusive_and_precision_ties_choose_higher(self):
        y = np.array([1,1,0,0])
        p = np.array([.5,.5,.2,.1])
        self.assertEqual(validation_threshold(y,p), .5)
        y = np.array([1,0,1,0])
        p = np.array([.9,.8,.7,.6])
        self.assertEqual(validation_threshold(y,p,target=.5), .9)

    def test_fixed_calibration_edges_and_empty_bins(self):
        bins = calibration(np.array([0,1,1]),np.array([0.,.1,1.]))
        self.assertEqual([bins[i]['n'] for i in (0,1,9)],[1,1,1])
        self.assertEqual(bins[1]['fatal'],1)
        self.assertIsNone(bins[2]['observed_fraction'])

    def test_one_class_ranking_undefined_and_zero_denominator_scores(self):
        row = evaluate(np.array([0,0]),np.array([.1,.2]),.5)
        self.assertIsNone(row['average_precision'])
        self.assertIsNone(row['roc_auc'])
        self.assertEqual(row['precision'],0.)
        self.assertEqual(row['recall'],0.)
        row = evaluate(np.array([1,1]),np.array([.1,.2]),.5)
        self.assertIsNone(row['average_precision'])


if __name__ == '__main__': unittest.main()
