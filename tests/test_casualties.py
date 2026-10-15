"""Check identity and outcome decisions where raw-row counting is unsafe."""
import unittest

from truck_collisions.build import COLUMNS
from truck_collisions.build_casualties import resolve_person_records


def record(**changes):
    row = dict.fromkeys(COLUMNS, 'UU')
    row.update(source_id='fixture', C_YEAR='2021', C_CASE='case', C_SEV='1',
               V_ID='01', V_TYPE='08', P_ID='01', P_USER='1', P_PSN='11',
               P_ISEV='3')
    row.update(changes)
    return row


def event(year=2021):
    return dict(source_id='fixture', C_YEAR=year, C_CASE='case', C_SEV='1',
                is_analysis_candidate=True)


class CasualtyResolutionTests(unittest.TestCase):
    def resolve(self, rows, events=None):
        return resolve_person_records(rows, events or [event()])

    def test_all_people_retained_and_known_duplicate_not_double_counted(self):
        tractor = record()
        rows = [tractor, dict(tractor), record(V_ID='02', V_TYPE='01'),
                record(V_ID='99', V_TYPE='NN', P_USER='3', P_PSN='99')]
        units, alternatives, unresolved, quality = self.resolve(rows)
        self.assertEqual(len(units), 3)
        self.assertEqual(sum(u['deaths_min'] for u in units), 3)
        self.assertEqual({u['road_user_group'] for u in units},
                         {'tractor_occupant', 'other_motor_vehicle_occupant', 'pedestrian'})
        self.assertEqual(sum(u['input_record_rows'] for u in units), 4)
        self.assertEqual(quality['exact_repeated_rows_beyond_first'], 1)
        self.assertEqual(len(alternatives), 3)
        self.assertEqual(unresolved, [])

    def test_repeated_unknown_identity_never_becomes_invented_person(self):
        unknown = record(P_ID='UU', P_ISEV='2')
        units, _, unresolved, quality = self.resolve([unknown, dict(unknown)])
        self.assertEqual(units, [])
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]['P_ID'], 'UU')
        self.assertEqual(unresolved[0]['record_multiplicity'], 2)
        self.assertEqual(quality['unresolved_identity_rows'], 2)
        units, _, unresolved, _ = self.resolve([record(V_ID='UU')])
        self.assertEqual(units, [])
        self.assertEqual(unresolved[0]['identity_status'], 'unresolved_identity')

    def test_dummy_person_excluded_even_when_outcome_is_positive(self):
        units, _, unresolved, quality = self.resolve([record(P_ID='NN', P_ISEV='2')])
        self.assertEqual(units, [])
        self.assertEqual(unresolved[0]['identity_status'], 'dummy')
        self.assertEqual(quality['dummy_positive_casualty_rows'], 1)

    def test_conflicting_outcomes_preserve_possibilities(self):
        units, alternatives, _, _ = self.resolve([record(P_ISEV='2'), record(P_ISEV='3')])
        unit = units[0]
        self.assertEqual((unit['deaths_min'], unit['deaths_max']), (0, 1))
        self.assertEqual((unit['injuries_min'], unit['injuries_max']), (0, 1))
        self.assertEqual((unit['casualties_min'], unit['casualties_max']), (1, 1))
        self.assertTrue(unit['severity_conflict'])
        self.assertEqual(len(alternatives), 2)

    def test_unknown_and_not_applicable_outcomes_are_distinct(self):
        rows = [record(P_ISEV='U'), record(P_ID='02', P_ISEV='N')]
        units, _, _, _ = self.resolve(rows)
        by_id = {u['P_ID']: u for u in units}
        self.assertTrue(by_id['01']['unknown_severity'])
        self.assertFalse(by_id['01']['not_applicable_severity'])
        self.assertTrue(by_id['02']['not_applicable_severity'])
        self.assertFalse(by_id['02']['unknown_severity'])
        self.assertEqual(sum(u['casualties_max'] for u in units), 0)

    def test_conflicting_vehicle_or_road_user_assignment_is_not_chosen(self):
        units, _, _, _ = self.resolve([record(), record(V_TYPE='01')])
        self.assertEqual(units[0]['road_user_group'], 'ambiguous')
        self.assertTrue(units[0]['vehicle_type_conflict'])
        units, _, _, _ = self.resolve([record(P_USER='3')])
        self.assertEqual(units[0]['road_user_group'], 'ambiguous')

    def test_case_and_person_ids_are_scoped_to_year_and_parent_event(self):
        units, _, _, _ = self.resolve([record(), record(C_YEAR='2020')],
                                      [event(), event(2020)])
        self.assertEqual(len(units), 2)
        with self.assertRaisesRegex(ValueError, 'parent event'):
            self.resolve([record(C_CASE='orphan')])


if __name__ == '__main__':
    unittest.main()
