"""Independent mutation tests: broken prepared tables must fail the validator."""
import unittest

import duckdb

from road_to_safety.validate_prepared import FEATURES, EVENT_FIELDS, inspect_table, published_profile_counts


class PreparedValidationTests(unittest.TestCase):
    def setUp(self):
        self.connection = duckdb.connect()
        fields = ','.join(f'{field} VARCHAR,{field}_conflict BOOLEAN' for field in EVENT_FIELDS)
        self.connection.execute(f'''CREATE TABLE collisions (
            source_id VARCHAR,C_YEAR VARCHAR,C_CASE VARCHAR,{fields},is_fatal INTEGER,severity_eligible BOOLEAN,
            diagnostic_source_rows BIGINT,diagnostic_exact_duplicate_extra_rows BIGINT,
            diagnostic_identified_person_keys BIGINT,diagnostic_unresolved_person_rows BIGINT)''')
        self.connection.execute("INSERT INTO collisions (source_id,C_YEAR,C_CASE,is_fatal,severity_eligible,diagnostic_source_rows,diagnostic_exact_duplicate_extra_rows,diagnostic_identified_person_keys,diagnostic_unresolved_person_rows) VALUES ('fixture','2020','1',0,true,2,0,2,0)")
        for field in EVENT_FIELDS:
            self.connection.execute(f"UPDATE collisions SET {field}=?,{field}_conflict=false", ['2' if field=='C_SEV' else '1'])
        self.contract = {'features':FEATURES.copy(),'target_column':'is_fatal','categorical_domains':{field:['1','U','X','N','Q'] for field in FEATURES}}
        self.sources = {'fixture':{'expected_year':2020,'collisions':1,'rows':2,'invalid_collision_key_rows':0}}

    def tearDown(self):
        self.connection.close()

    def checks(self):
        return {row['check'] for row in inspect_table(self.connection,self.contract,self.sources)['failures']}

    def test_valid_table_and_undocumented_values_are_preserved_as_exceptions(self):
        self.assertEqual(self.checks(),set())
        self.connection.execute("UPDATE collisions SET C_WTHR='*'")
        result = inspect_table(self.connection,self.contract,self.sources)
        self.assertEqual(result['failures'],[])
        self.assertEqual(result['domain_exceptions'][0]['value'],'*')
        self.assertEqual(result['value_counts'][next(i for i,row in enumerate(result['value_counts']) if row['field']=='C_WTHR')]['value_class'],'unresolved_star_code')

    def test_blank_and_conflict_remain_distinct_profile_states(self):
        self.connection.execute("UPDATE collisions SET C_WTHR=''")
        self.connection.execute("INSERT INTO collisions SELECT * REPLACE ('2' AS C_CASE,NULL AS C_WTHR,true AS C_WTHR_conflict) FROM collisions")
        self.sources['fixture'].update(collisions=2,rows=4)
        result = inspect_table(self.connection,self.contract,self.sources)
        self.assertEqual(result['failures'],[])
        weather = [row for row in result['value_counts'] if row['field']=='C_WTHR']
        self.assertEqual({row['value_class'] for row in weather},{'blank','conflict'})
        self.assertEqual(sum(row['collisions'] for row in weather),2)
        published = published_profile_counts([
            {'observed_year': '2020', 'field': 'C_WTHR', 'value': '',
             'value_class': 'blank', 'collisions': '1'},
            {'observed_year': '2020', 'field': 'C_WTHR', 'value': '',
             'value_class': 'conflict', 'collisions': '1'},
        ])
        self.assertEqual(published, {('2020', 'C_WTHR', '', False): 1,
                                     ('2020', 'C_WTHR', '', True): 1})

    def test_fractional_identifier_is_not_a_valid_collision_key(self):
        self.connection.execute("UPDATE collisions SET C_CASE='1.5'")
        self.assertIn('valid_collision_key',self.checks())

    def test_identity_and_unknown_features_do_not_remove_severity_eligible_event(self):
        self.connection.execute("UPDATE collisions SET diagnostic_identified_person_keys=0,diagnostic_unresolved_person_rows=2,C_WTHR='U',C_TRAF='QQ'")
        result = inspect_table(self.connection,self.contract,self.sources)
        self.assertEqual(result['failures'],[])
        self.assertTrue(self.connection.execute('SELECT severity_eligible FROM collisions').fetchone()[0])
        self.assertEqual(self.connection.execute('SELECT C_WTHR,C_TRAF FROM collisions').fetchone(),('U','QQ'))

    def test_duplicate_key_and_row_conservation_fail(self):
        self.connection.execute('INSERT INTO collisions SELECT * FROM collisions')
        self.assertTrue({'unique_collision_key','collision_count_conservation','source_row_conservation'} <= self.checks())

    def test_target_errors_and_feature_leakage_fail(self):
        self.connection.execute('UPDATE collisions SET is_fatal=1')
        self.assertIn('severity_target_mapping',self.checks())
        self.contract['features'].append('is_fatal')
        # Target/feature policy fails before profiling an unrecognized feature.
        self.assertIn('target_excluded_from_features',self.checks())

    def test_conflict_must_not_choose_arbitrary_value(self):
        self.connection.execute('UPDATE collisions SET C_WTHR_conflict=true')
        self.assertIn('C_WTHR_conflict_null',self.checks())
        self.connection.execute('UPDATE collisions SET C_WTHR=NULL')
        self.assertNotIn('C_WTHR_conflict_null',self.checks())

    def test_unselected_source_invalid_key_and_child_join_corruption_fail(self):
        self.connection.execute("UPDATE collisions SET source_id='comparison',C_CASE='U',diagnostic_identified_person_keys=3")
        self.assertTrue({'selected_source_and_expected_year','valid_collision_key','person_row_key_conservation','all_selected_sources_present'} <= self.checks())


if __name__ == '__main__':
    unittest.main()
