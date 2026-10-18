import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from app import Store, create_app
from test_support import create_test_app as create_app
from achievements import completion_facts


class AchievementTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = self.directory.name + '/badges.sqlite3'
        self.store = Store(path=self.path)
        self.client = create_app(store=self.store, data_mode='sample').test_client()

    def add_completion(self, index, day, **values):
        record = dict(id=f'complete:{index}', profile_id='demo', kind='completion', quest_id='archived',
                      opportunity_id=f'completed:{index}', title='A recorded action', category='General task',
                      achievement_category='Wellness', achievement_tags=[], micro_goal=False,
                      difficulty='Easy', minutes=3, points=10, skills=['Writing'],
                      completed_at=day.isoformat())
        record.update(values)
        self.store.put('activity', record)

    def badges(self):
        response = self.client.get('/progress')
        self.assertEqual(response.status_code, 200)
        return {badge['id']: badge for badge in response.json['achievements']}

    def test_all_ten_criteria_and_permanent_backlog_unlock(self):
        self.assertTrue(all(not b['unlocked'] for b in self.badges().values()))
        day = datetime(2026, 1, 1, 20, tzinfo=timezone.utc)
        for index in range(7):
            self.add_completion(index, day + timedelta(days=index), micro_goal=True,
                                difficulty='Lazy' if index < 5 else 'Challenging', points=150,
                                achievement_category=['Wellness','Networking','Certification','Class','Club','Job simulation','Wellness'][index],
                                achievement_tags=['resume-linkedin','networking','wellness'] if index < 3 else [])
        for index in range(10):
            self.store.put('activity', dict(id=f'save:{index}', kind='save', profile_id='demo', opportunity_id=f'backlog:{index}'))
        badges = self.badges()
        self.assertEqual(len(badges), 94)
        self.assertTrue(all(badges[key]['unlocked'] for key in ['first-step','one-percent','couch-bound','heavy-lifter','algorithm-whisperer','touch-grass','renaissance','visionary','warm-intro','base-camp']))
        self.assertEqual(badges['one-percent']['earned_at'], (day + timedelta(days=6)).isoformat())
        self.store.delete('activity', 'save:0')
        reopened = create_app(store=Store(path=self.path), data_mode='sample').test_client()
        after = {b['id']: b for b in reopened.get('/progress').json['achievements']}
        self.assertTrue(after['visionary']['unlocked'])
        self.assertEqual(after['visionary']['earned_at'], badges['visionary']['earned_at'])

    def test_gaps_duplicate_days_and_non_micro_quests_do_not_earn_streak(self):
        day = datetime(2026, 2, 1, 20, tzinfo=timezone.utc)
        for index in range(7):
            self.add_completion(index, day + timedelta(days=index), micro_goal=False)
        self.assertFalse(self.badges()['one-percent']['unlocked'])
        for index in range(7):
            self.add_completion(index+10, day + timedelta(days=index*2), micro_goal=True)
        for index in range(7):
            self.add_completion(index+20, day, micro_goal=True)
        self.assertFalse(self.badges()['one-percent']['unlocked'])
        self.assertEqual(self.badges()['one-percent']['progress'], 1)

    def test_backlog_excludes_opportunities_with_a_completion(self):
        day = datetime(2026, 1, 1, 20, tzinfo=timezone.utc)
        self.add_completion(0, day, opportunity_id='backlog:0')
        for index in range(10):
            self.store.put('activity', dict(id=f'save:{index}', kind='save', profile_id='demo', opportunity_id=f'backlog:{index}'))
        self.assertEqual(self.badges()['visionary']['progress'], 9)
        self.assertFalse(self.badges()['visionary']['unlocked'])

    def test_real_completion_retry_does_not_inflate_badge_counts(self):
        self.client.post('/profiles', json={'goal':'Build my skills','interests':['Design'],'skills':['Writing']})
        self.client.post('/saved', json={'opportunity_id':'design'})
        for _ in range(2):
            self.client.post('/completions', json={'quest_id':'design-small'})
        badges = self.badges()
        self.assertEqual(badges['first-step']['progress'], 1)
        self.assertEqual(badges['one-percent']['progress'], 1)

    def test_task_tags_match_work_rather_than_broad_interest_labels(self):
        task={'title':'Update your headline','daily':True,'minutes':3}
        opportunity={'kind':'General task','general_task':{'category':'Resume & Interview Preparation','description':'Rewrite your LinkedIn headline.'}}
        facts=completion_facts(task, opportunity)
        self.assertIn('resume-linkedin', facts['achievement_tags'])
        self.assertTrue(facts['micro_goal'])
        opportunity['general_task']['description']='Practice an interview question.'
        self.assertNotIn('resume-linkedin', completion_facts({'title':'Interview practice'}, opportunity)['achievement_tags'])
        opportunity['general_task']['category']='Wellness & Desk Ergonomics'
        self.assertIn('wellness', completion_facts(task, opportunity)['achievement_tags'])

    def test_repeating_one_networking_opportunity_is_not_three_events(self):
        day = datetime(2026, 1, 1, 20, tzinfo=timezone.utc)
        for index in range(3):
            self.add_completion(index, day + timedelta(days=index), opportunity_id='same-event', achievement_tags=['networking'])
        self.assertEqual(self.badges()['warm-intro']['progress'], 1)
        self.assertFalse(self.badges()['warm-intro']['unlocked'])


if __name__ == '__main__':
    unittest.main()
