import unittest

import duckdb
import pandas as pd

from road_to_safety.analyze_temporal import annotate, summarize


class TemporalAnalysisTests(unittest.TestCase):
    def test_dictionary_weekdays_and_unknown_states_remain_distinct(self):
        frame = annotate(pd.DataFrame({'code': ['1', '7', 'U', 'X', None]}), 'weekday')
        self.assertEqual(frame.label.tolist()[:2], ['Monday', 'Sunday'])
        self.assertEqual(frame.value_class.tolist(),
                         ['stated', 'stated', 'unknown', 'unavailable', 'unresolved'])

    def test_conditional_target_denominator_excludes_unresolved_target_only(self):
        connection = duckdb.connect()
        connection.execute("""CREATE TABLE temporal AS SELECT * FROM (VALUES
            ('1', true, 1), ('1', true, 0), ('1', false, NULL),
            ('UU', true, 1)) t(code, severity_eligible, is_fatal)""")
        result = summarize(connection, 'code').set_index('code')
        self.assertEqual(result.loc['1', 'collisions'], 3)
        self.assertEqual(result.loc['1', 'eligible_collisions'], 2)
        self.assertEqual(result.loc['1', 'fatal_proportion'], .5)
        self.assertEqual(result.loc['UU', 'fatal_proportion'], 1)
        self.assertTrue(result.sparse_group.all())
        connection.close()


if __name__ == '__main__':
    unittest.main()
