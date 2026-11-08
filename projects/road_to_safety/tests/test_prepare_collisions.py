"""Synthetic proof of retained grain, target conflicts and identity handling."""
import csv
from pathlib import Path
import tempfile
import unittest

import duckdb

from road_to_safety.audit_data import COLUMNS, sha256
from road_to_safety.prepare_collisions import prepare_file


class PreparationTests(unittest.TestCase):
    def test_decimal_key_is_quarantined_and_field_specific_invalid_codes_are_flagged(self):
        base=dict(zip(COLUMNS,['2020','01','1','00','2','02','32','01','1','1','1','18',
            '01','01','2015','01','M','35','11','2','02','1','1']))
        rows=[{**base,'C_CASE':'1.5'}, {**base,'C_CASE':'2','C_WTHR':'N'},
              {**base,'C_CASE':'3','C_SEV':'U'}, {**base,'C_CASE':'4','C_MNTH':''},
              {**base,'C_CASE':'4','C_MNTH':'01'}]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/'fixture.csv'
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            resource={'local_path':'fixture.csv','year':2020,'resource_id':'fixture','sha256':sha256(path)}
            result=prepare_file((str(root),resource,str(root)))
            self.assertEqual((result['collisions'],result['invalid_collision_key_rows'],result['target_ineligible_collisions']),(3,1,1))
            profiles={(p['field'],p['value']):p for p in result['profiles']}
            self.assertEqual(profiles['C_WTHR','N']['value_class'],'invalid_code')
            self.assertFalse(profiles['C_WTHR','N']['documented_domain_valid'])
            self.assertEqual(profiles['C_MNTH',None]['value_class'],'conflict')
            connection=duckdb.connect()
            exceptions=dict(connection.execute(f"SELECT C_CASE,reasons FROM read_parquet('{root/'2020_exceptions.parquet'}')").fetchall())
            self.assertIn('invalid_collision_key',exceptions['1.5'])
            self.assertIn('undocumented_collision_code',exceptions['2'])
            self.assertIn('unresolved_target',exceptions['3'])
            with self.assertRaisesRegex(ValueError,'observed year differs'):
                prepare_file((str(root),{**resource,'year':2019},str(root)))

    def test_canonical_duplicates_retain_raw_multiplicity_and_original_codes(self):
        base=['2020','01','1','00','2','02','32','01','1','1','1','18',
              '01','01','2015','01','M','35','11','2','02','1','1']
        alternate=base.copy()
        alternate[1]='1'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/'fixture.csv'
            with path.open('w',newline='') as stream:
                writer=csv.writer(stream)
                writer.writerow(COLUMNS)
                writer.writerows([base,alternate])
            resource={'local_path':'fixture.csv','year':2020,'resource_id':'fixture','sha256':sha256(path)}
            result=prepare_file((str(root),resource,str(root)))
            connection=duckdb.connect()
            counters=connection.execute(f"SELECT diagnostic_source_rows,diagnostic_normalized_distinct_rows,diagnostic_exact_duplicate_extra_rows FROM read_parquet('{root/'2020_collisions.parquet'}')").fetchone()
            self.assertEqual(counters,(2,1,0))
            self.assertEqual(result['collisions'],1)
            originals=connection.execute(f"SELECT C_MNTH FROM read_parquet('{root/'2020_exceptions.parquet'}') ORDER BY source_row_number").fetchall()
            self.assertEqual(originals,[('01',),('1',)])

    def test_conflicts_duplicates_and_unresolved_children_do_not_multiply_or_drop_events(self):
        base=dict(zip(COLUMNS,['2020','01','1','00','2','02','32','01','1','1','1','18',
            '01','01','2015','01','M','35','11','2','02','1','1']))
        def row(case,**changes):
            return {**base,'C_CASE':case,**changes}
        rows=[row('1'),row('1'),row('1',P_ID='02',V_YEAR='2018'),
            row('2',C_SEV='1',P_ISEV='3'),row('2',C_SEV='2'),
            row('3',P_ID='NN',P_ISEV='N',C_WTHR='Q'),
            row('4',V_ID='UU',C_MNTH='UU',C_RSUR='*'),
            row('5',V_ID='99',V_TYPE='NN'),row('U')]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            path=root/'fixture.csv'
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            resource={'local_path':'fixture.csv','year':2020,'resource_id':'fixture','sha256':sha256(path)}
            summary=prepare_file((str(root),resource,str(root)))
            connection=duckdb.connect()
            connection.execute(f"CREATE VIEW collisions AS SELECT * FROM read_parquet('{root/'2020_collisions.parquet'}')")
            self.assertEqual(connection.execute('SELECT count(*),sum(diagnostic_source_rows) FROM collisions').fetchone(),(5,8))
            self.assertEqual(summary['rows'],9)
            self.assertEqual(summary['invalid_collision_key_rows'],1)
            self.assertEqual(summary['exact_duplicate_extra_rows'],1)
            self.assertEqual(summary['target_ineligible_collisions'],1)
            self.assertEqual(connection.execute("SELECT diagnostic_source_rows,diagnostic_identified_person_keys,diagnostic_duplicate_person_keys,diagnostic_vehicle_keys,diagnostic_vehicle_conflict_keys,diagnostic_exact_duplicate_extra_rows,diagnostic_normalized_distinct_rows FROM collisions WHERE C_CASE='1'").fetchone(),(3,2,1,1,1,1,2))
            self.assertEqual(connection.execute("SELECT C_SEV,C_SEV_conflict,is_fatal,severity_eligible,diagnostic_person_conflict_keys,diagnostic_person_severity_conflict_keys FROM collisions WHERE C_CASE='2'").fetchone(),(None,True,None,False,1,1))
            self.assertEqual(connection.execute("SELECT C_MNTH,C_RSUR,severity_eligible,diagnostic_unresolved_person_rows FROM collisions WHERE C_CASE='4'").fetchone(),('UU','*',True,1))
            self.assertEqual(connection.execute("SELECT C_HOUR,C_MNTH FROM collisions WHERE C_CASE='1'").fetchone(),('0','1'))
            exception_rows=connection.execute(f"SELECT source_row_number,C_CASE,reasons FROM read_parquet('{root/'2020_exceptions.parquet'}') ORDER BY source_row_number").fetchall()
            self.assertEqual(len(exception_rows),9)
            self.assertIn('exact_duplicate_source_row',exception_rows[0][2])
            self.assertEqual(exception_rows[0][0],2)
            self.assertEqual(exception_rows[-1][1],'U')
            self.assertIn('invalid_collision_key',exception_rows[-1][2])
            classes={(p['field'],p['value']):p['value_class'] for p in summary['profiles']}
            self.assertEqual(classes['C_WTHR','Q'],'other')
            self.assertEqual(classes['C_MNTH','UU'],'unknown')
            self.assertEqual(classes['C_RSUR','*'],'unresolved_star_code')
            self.assertEqual(classes['C_SEV',None],'conflict')
            self.assertEqual(sha256(path),resource['sha256'])


if __name__=='__main__':
    unittest.main()
