"""Guard stale-input reuse and misleading descriptive evidence."""
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from road_to_safety.explore import sha256, verify_inputs
from road_to_safety.validate_exploration import check_counts


class ExplorationValidationTests(unittest.TestCase):
    def test_changed_input_rejects_old_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'data/derived').mkdir(parents=True)
            source=root/'input'
            source.write_text('original')
            receipt={'status':'passed','failures':[], 'input_fingerprints':{'input':sha256(source)}}
            (root/'data/derived/prepared_validation.json').write_text(json.dumps(receipt))
            verify_inputs(root)
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError,'Stale'):
                verify_inputs(root)

    def test_incorrect_rate_and_duplicate_groups_rejected(self):
        correct=pd.DataFrame({'code':['1','U'],'collisions':[100,10],'fatal_collisions':[2,1]})
        wrong=correct.assign(fatal_proportion=[.02,.01])
        with self.assertRaisesRegex(ValueError,'denominators'):
            check_counts(wrong,correct,['code'])
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            check_counts(pd.concat([correct,correct]),correct,['code'])

    def test_fatal_numerator_change_and_injury_loss_rejected(self):
        correct=pd.DataFrame({'code':['1'],'collisions':[100],'fatal_collisions':[2]})
        with self.assertRaises(AssertionError):
            check_counts(correct.assign(fatal_collisions=3),correct,['code'])
        with self.assertRaisesRegex(ValueError,'conserve'):
            check_counts(correct.assign(injury_collisions=97),correct,['code'])


if __name__=='__main__':
    unittest.main()
