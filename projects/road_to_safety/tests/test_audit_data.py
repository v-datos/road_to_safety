"""Regression checks for grain, unresolved identities, and sentinel semantics."""
import csv
import json
from pathlib import Path
import tempfile
import unittest

from road_to_safety.audit_data import COLUMNS, profile_file, value_class, run, sha256


class AuditTests(unittest.TestCase):
    def test_dictionary_sentinel_classes(self):
        self.assertEqual(value_class('P_USER', 'U'), 'not_stated_other_unknown')
        for value, expected in [('UU', 'unknown'), ('XX', 'jurisdiction_unavailable'),
                                ('NN', 'not_applicable'), ('QQ', 'other'),
                                ('**', 'unresolved_star_code'), ('', 'blank')]:
            self.assertEqual(value_class('P_AGE', value), expected)
        self.assertEqual(value_class('P_ISEV', '1'), 'stated')

    def test_repeated_rows_conflicts_and_unknown_keys_remain_visible(self):
        base = dict(zip(COLUMNS, ['2020','01','1','10','2','02','32','01','1','1','1','18','01','01','2015','01','M','35','11','2','02','1','1']))
        def row(case, person='01', **changes):
            return {**base, 'C_CASE':case, 'P_ID':person, **changes}
        rows = [row('1'), row('1'), row('1','02'), row('2',C_SEV='1'),
                row('2','02'), row('3','NN',P_ISEV='N'),
                row('4',V_ID='UU',P_ISEV='U'),row('U')]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'input.csv'
            with path.open('w',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            result = profile_file((directory, {'local_path':'input.csv','year':2020,'resource_id':'fixture'}))
        self.assertEqual(result['rows'],8)
        self.assertEqual(result['collisions'],4)
        self.assertEqual(result['invalid_collision_key_rows'],1)
        self.assertEqual(result['identified_person_rows'],5)
        self.assertEqual(result['identified_person_keys'],4)
        self.assertEqual(result['unresolved_person_identity_rows'],3)
        self.assertEqual(result['exact_duplicate_extra_rows'],1)
        self.assertEqual(result['duplicate_identified_person_keys'],1)
        self.assertEqual(result['severity_conflict_collisions'],1)
        self.assertEqual(result['valid_severity_collisions'],3)
        self.assertEqual(result['fatal_collisions'],0)
        self.assertEqual(result['injury_collisions'],3)

    def test_cache_checks_current_manifest_hash_and_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'data').mkdir()
            path = root/'input.csv'
            with path.open('w',newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(COLUMNS)
                writer.writerow(['2020','01','1','10','2','01','02','01','1','1','1','18','01','01','2015','01','M','35','11','2','02','1','1'])
            resource = {'resource_id':'fixture','local_path':'input.csv','year':2020,
                        'selected':True,'sha256':sha256(path),'sheet':None}
            manifest = {'resources':[resource]}
            manifest_path = root/'data/sources.json'
            manifest_path.write_text(json.dumps(manifest))
            first = run(root,workers=1)
            self.assertTrue(first[0]['selected'])
            resource['sha256'] = '0' * 64
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'manifest SHA256 mismatch'):
                run(root,workers=1)
            resource['sha256'] = sha256(path)
            resource['selected'] = False
            manifest_path.write_text(json.dumps({'resources':[], 'alternatives':[resource]}))
            second = run(root,workers=1,include_comparator=True)
            self.assertFalse(second[0]['selected'])


if __name__ == '__main__':
    unittest.main()
