import unittest
from .duration import parse_workload
from .test_personalization import example
from .personalize import TAXONOMY
from backend.catalog_reader import CatalogReader


class EffortTests(unittest.TestCase):
    def test_workload_ranges_weekly_and_supported_units(self):
        self.assertEqual(parse_workload("4 weeks of study, 2–3 hours/week")[:3], (480, 720, True))
        self.assertEqual(parse_workload("2 heures")[:2], (120, 120))
        self.assertEqual(parse_workload("1 hour 30 minutes")[:2], (90, 90))
        self.assertEqual(parse_workload("1,5 horas")[:2], (90, 90))
        self.assertEqual(parse_workload("4 weeks, 8 hours total")[:2], (480, 480))
        self.assertIsNone(parse_workload("30 mins/week"))
        self.assertIsNone(parse_workload("3 hours per day"))
        self.assertIsNone(parse_workload("Provider did not supply workload"))

    def test_advanced_guided_lab_is_not_lazy_and_source_time_is_preserved(self):
        row = example(title="Advanced neural networks", description="A step-by-step guided lab.", workload="2 hours")
        p = row['personalization']
        self.assertEqual(p['assessment']['difficulty'], 'Challenging')
        self.assertEqual(p['duration']['minutes'], 120)
        self.assertEqual(p['assessment']['duration_quality'], 'Source reported')
        self.assertEqual(p['assessment']['cost'], 'Unknown')
        self.assertEqual(p['assessment']['prerequisite_status'], 'Unknown')

    def test_unknown_prerequisites_not_confused_with_none_stated(self):
        unknown = example(description='Learn Python.')
        explicit = example(source_id='beginner', description='No prior experience is required. Learn Python.')
        self.assertEqual(unknown['personalization']['assessment']['prerequisite_status'], 'Unknown')
        self.assertEqual(explicit['personalization']['assessment']['prerequisite_status'], 'None stated')
        reader = CatalogReader([unknown, explicit], TAXONOMY)
        self.assertEqual(reader.query(prerequisites=['None stated'])['total'], 1)
        self.assertEqual(reader.query(cost=['Free'])['total'], 0)

    def test_time_cap_uses_upper_bound_and_excludes_unknown_totals(self):
        course = example(workload='1-2 hours')
        job = example(source_id='job', source='muse', kind='Job', title='Software engineer', description='Build systems.')
        reader = CatalogReader([course, job], TAXONOMY)
        self.assertEqual(reader.query(max_minutes=90)['total'], 0)
        self.assertEqual(reader.query(max_minutes=120)['total'], 1)
        self.assertEqual(reader.query(max_minutes=2, scope='micro_step')['total'], 2)
        self.assertEqual(job['personalization']['duration']['quality'], 'Unknown')
        with self.assertRaises(ValueError):
            reader.query(max_minutes=float('nan'))

    def test_strict_groups_unknown_filters_and_fallback_topics(self):
        fallback = example(source_id='other', title='General learning', description='Explore a subject.')
        course = example(workload='1 hour')
        reader = CatalogReader([fallback, course], TAXONOMY)
        self.assertEqual(reader.query(interests=['Productivity & Personal Growth'])['total'], 0)
        self.assertEqual(reader.query(skills=['Coding', 'Data analysis'])['total'], 1)
        self.assertEqual(reader.query(goals=['Learn a new technical skill', 'Develop leadership experience'])['total'], 0)
        for options in ({'experience':['Impossible']}, {'cost':['Cheap']}, {'skills':['Magic']}, {'source':'imaginary'}):
            with self.assertRaises(ValueError):
                reader.query(**options)

    def test_near_me_cannot_be_bypassed_by_another_location(self):
        online = example()
        reader = CatalogReader([online], TAXONOMY)
        self.assertEqual(reader.query(locations=['Near me', 'Online / Remote'], lat=33.7, lon=-117.8)['total'], 0)

    def test_source_prerequisite_requirement_and_cost(self):
        row = example(prerequisites='Python programming required', is_free=False)
        self.assertEqual(row['personalization']['assessment']['prerequisite_status'], 'Required')
        self.assertEqual(row['personalization']['assessment']['cost'], 'Paid')
        self.assertEqual(CatalogReader([row], TAXONOMY).query(cost=['Paid'], prerequisites=['Required'])['total'], 1)


if __name__ == '__main__':
    unittest.main()
