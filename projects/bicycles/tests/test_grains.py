import unittest

import duckdb

from bicycle_collisions.build import COLUMNS, derive


def record(**changes):
    row=dict.fromkeys(COLUMNS,'1')
    row.update(source_id='fixture',C_YEAR='2020',C_CASE='1',V_ID='01',V_TYPE='17',
               P_ID='01',P_USER='4',P_ISEV='2',P_SEX='F',P_AGE='30')
    row.update(changes)
    return row


class GrainTests(unittest.TestCase):
    def setUp(self):
        self.connection=duckdb.connect()

    def tearDown(self):
        self.connection.close()

    def build(self,records):
        names=['source_id',*COLUMNS]
        self.connection.execute('CREATE TABLE records ('+','.join(n+' VARCHAR' for n in names)+')')
        self.connection.executemany('INSERT INTO records VALUES ('+','.join('?' for _ in names)+')',
            [[r[n] for n in names] for r in records])
        derive(self.connection)

    def test_two_bicycles_and_duplicate_person_do_not_multiply_events(self):
        self.build([record(),record(),record(V_ID='02'),
            record(V_ID='03',V_TYPE='01',P_USER='1',P_ISEV='3')])
        self.assertEqual(self.connection.execute('SELECT count(*) FROM collisions').fetchone()[0],1)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM vehicles').fetchone()[0],3)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM people').fetchone()[0],3)
        self.assertEqual(self.connection.execute("SELECT sum(deaths_min) FROM people WHERE P_USER='1'").fetchone()[0],1)

    def test_identifiers_are_scoped_to_year_and_release(self):
        self.build([record(),record(C_YEAR='2021'),record(source_id='other')])
        self.assertEqual(self.connection.execute('SELECT count(*) FROM people').fetchone()[0],3)

    def test_unknown_and_dummy_identities_remain_unresolved(self):
        self.build([record(P_ID='UU',P_ISEV='3'),record(P_ID='NN',P_ISEV='N')])
        self.assertEqual(self.connection.execute('SELECT count(*) FROM people').fetchone()[0],0)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM unresolved_records').fetchone()[0],2)

    def test_conflicting_person_classification_and_outcome_not_chosen(self):
        self.build([record(P_ISEV='1'),record(P_ISEV='2',P_USER='1')])
        user,severity,low,high=self.connection.execute('SELECT P_USER,P_ISEV,injuries_min,injuries_max FROM people').fetchone()
        self.assertEqual((user,severity,low,high),('conflict',None,0,1))


if __name__=='__main__':
    unittest.main()
