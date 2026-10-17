import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app import Store, create_app
from achievements import BADGES, EXPANSION


class MountainAchievementTest(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.store=Store(path=self.directory.name+'/map.sqlite3')
        self.day=datetime(2026,10,1,15,tzinfo=timezone.utc)
        self.client=create_app(store=self.store,data_mode='sample',now=lambda:self.day).test_client()

    def badges(self):
        response=self.client.get('/progress');self.assertEqual(response.status_code,200)
        return {b['id']:b for b in response.json['achievements']}

    def completion(self,index,**extra):
        row=dict(id=f'completion:{index}',profile_id='demo',kind='completion',quest_id='archived',opportunity_id=f'opp:{index}',title='An actual recorded quest',category='General task',achievement_category='Wellness',achievement_tags=[],micro_goal=True,daily=True,minutes=2,points=15,skills=['Writing'],difficulty='Lazy',completed_at=(self.day+timedelta(days=index)).isoformat())
        row.update(extra);self.store.put('activity',row)

    def test_unsupported_achievements_are_omitted_and_every_peak_has_a_rule(self):
        self.assertEqual(len(BADGES),95)
        self.assertEqual(len({b[0] for b in BADGES}),95)
        omitted={'mount-21','mount-25','mount-31','mount-33','mount-34'}
        self.assertFalse(omitted.intersection(self.badges()))
        self.assertTrue(all(not badge['tracking_hint'] for badge in EXPANSION))
        self.assertTrue(all(not badge['unlocked'] for badge in self.badges().values()))

    def test_estimates_do_not_count_as_logged_time_or_real_outcomes(self):
        for index in range(3):self.completion(index,minutes=1200,category='Online course')
        badges=self.badges()
        self.assertFalse(badges['mount-03']['unlocked'])
        self.assertFalse(badges['mount-23']['unlocked'])
        self.assertFalse(badges['mount-24']['unlocked'])
        self.completion(3,actual_minutes=1440)
        self.completion(4,actual_minutes=1440)
        self.completion(5,actual_minutes=120)
        self.assertTrue(self.badges()['mount-03']['unlocked'])

    def test_pacific_streaks_and_difficulty_order_are_based_on_recorded_work(self):
        for index in range(5):self.completion(index,difficulty=['Lazy','Easy','Hard','Challenging','Lazy'][index])
        badges=self.badges()
        self.assertTrue(badges['mount-01']['unlocked'])
        self.assertTrue(badges['mount-05']['unlocked'])
        self.assertTrue(badges['mount-18']['unlocked'])
        self.assertFalse(badges['mount-10']['unlocked'])
        self.assertFalse(badges['mount-17']['unlocked'])

    def test_explicit_outcomes_need_the_correct_opportunity_type(self):
        for index in range(3):self.completion(index,category='Online course',outcomes=['certification_completed'])
        self.assertTrue(self.badges()['mount-23']['unlocked'])
        self.completion(4,category='Online course',outcomes=['applied'])
        self.assertFalse(self.badges()['mount-24']['unlocked'])
        self.completion(5,category='Internship',outcomes=['applied'])
        self.assertTrue(self.badges()['mount-24']['unlocked'])

    def test_saves_work_logs_and_retries_are_persistent_and_idempotent(self):
        self.client.post('/profiles',json={'goal':'Build my skills','interests':['Design'],'skills':['Writing']})
        for _ in range(2):self.client.post('/saved',json={'opportunity_id':'design','filters':{'active':True,'challenges':['Lazy']}})
        self.assertEqual(len([r for r in self.store.all('activity') if r['kind']=='bookmark_history']),1)
        log={'quest_id':'design-small','actual_minutes':3,'outcomes':['portfolio_updated']}
        for _ in range(2):self.assertEqual(self.client.post('/completions',json=log).status_code,200)
        badges=self.badges()
        self.assertTrue(badges['mount-35']['unlocked'])
        self.assertTrue(badges['mount-44']['unlocked'])
        self.assertEqual(badges['mount-03']['progress'],3)
        for invalid in [True,-1,1.2,2000]:
            self.assertEqual(self.client.post('/completions',json={**log,'actual_minutes':invalid}).status_code,400)
        self.assertEqual(self.client.post('/completions',json={**log,'outcomes':['invented']}).status_code,400)
        self.assertEqual(self.client.post('/completions',json={**log,'outcomes':['applied']}).status_code,400)

    def test_view_badges_require_ui_events_not_just_api_generation(self):
        with patch('routes.progress.generate_recap_narrative',return_value=None):
            recap=self.client.post('/recap/narrative',json={'period':'month','month':'2026-10'}).json
        badges=self.badges()
        self.assertTrue(badges['mount-81']['unlocked'])
        self.assertFalse(badges['mount-86']['unlocked'])
        self.assertEqual(self.client.post('/activity/events',json={'event':'fallback_read','recap_id':recap['recap_id']}).status_code,200)
        self.assertTrue(self.badges()['mount-86']['unlocked'])
        self.assertEqual(self.client.post('/activity/events',json={'event':'highlight_view','recap_id':recap['recap_id']}).status_code,400)
        self.assertEqual(self.client.post('/activity/events',json={'event':'share_click','recap_id':'missing'}).status_code,400)
        self.assertEqual(self.client.post('/activity/events',json={'event':'analytics_view','recap_id':{}}).status_code,400)
        self.client.get('/analytics')
        self.assertFalse(self.badges()['mount-89']['unlocked'])
        self.client.post('/activity/events',json={'event':'analytics_view'})
        self.assertTrue(self.badges()['mount-89']['unlocked'])

    def test_monthly_sequence_and_yearly_recap_are_implemented(self):
        for month in ['2026-08','2026-09','2026-10']:
            self.assertEqual(self.client.post('/recap/narrative',json={'period':'month','month':month}).status_code,200)
        self.assertTrue(self.badges()['mount-82']['unlocked'])
        result=self.client.post('/recap/narrative',json={'period':'year','year':'2026'})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json['start'],'2026-01-01')
        self.assertTrue(self.badges()['mount-83']['unlocked'])


if __name__=='__main__':unittest.main()
