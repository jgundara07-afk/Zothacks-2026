import tempfile
import unittest
from app import create_app, Store

class JourneyTest(unittest.TestCase):
    def test_complete_journey_and_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = directory + '/test.sqlite3'
            client = create_app(Store(path=path)).test_client()
            self.assertEqual(client.get('/health').status_code, 200)
            self.assertIsNone(client.get('/opportunities').json['profile'])
            self.assertEqual(client.post('/saved', json={'opportunity_id':'design'}).status_code, 400)
            self.assertEqual(client.post('/profiles', json={'goal':'invalid'}).status_code, 400)
            self.assertEqual(client.post('/profiles', json={'goal':'Build my skills','interests':['Design'],'skills':['Writing']}).status_code, 200)
            self.assertEqual(client.get('/opportunities').json['opportunities'][0]['matching_tags'], ['Design','Writing'])
            for opportunity, quest in [('design','design-1'),('code','code-1')]:
                for _ in range(2):
                    self.assertEqual(client.post('/saved', json={'opportunity_id':opportunity}).status_code,200)
                first=client.post('/completions',json={'quest_id':quest}).json
                self.assertFalse(first['already_completed'])
                duplicate=client.post('/completions',json={'quest_id':quest}).json
                self.assertTrue(duplicate['already_completed'])
                self.assertEqual(duplicate['points_earned'],0)
            reopened=create_app(Store(path=path)).test_client()
            progress=reopened.get('/progress').json
            self.assertEqual(progress['points'],125)
            self.assertEqual(progress['completed_count'],2)
            self.assertEqual(len(reopened.get('/saved').json['opportunities']),2)
            self.assertEqual(reopened.post('/completions',json={'quest_id':'unknown'}).status_code,404)
            self.assertEqual(reopened.post('/saved',data='broken',content_type='application/json').status_code,400)
            self.assertEqual(reopened.post('/completions',json={'quest_id':'green-1'}).status_code,400)
            for _ in range(2):
                response = reopened.delete('/saved', json={'opportunity_id':'design'})
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.json['saved'])
            after_unsave = create_app(Store(path=path)).test_client()
            self.assertEqual(after_unsave.get('/progress').json['saved_count'], 1)
            self.assertEqual(after_unsave.get('/progress').json['points'], 125)
            self.assertEqual(after_unsave.get('/progress').json['completed_count'], 2)
            self.assertEqual([o['id'] for o in after_unsave.get('/saved').json['opportunities']], ['code'])
            self.assertFalse(next(o for o in after_unsave.get('/opportunities').json['opportunities'] if o['id']=='design')['saved'])
            self.assertEqual(after_unsave.delete('/saved', json={'opportunity_id':'missing'}).status_code, 404)
            self.assertEqual(after_unsave.delete('/saved', json={}).status_code, 400)
            after_unsave.post('/saved', json={'opportunity_id':'design'})
            self.assertEqual(after_unsave.get('/progress').json['saved_count'], 2)
            self.assertEqual(after_unsave.post('/completions',json={'quest_id':'design-1'}).json['points_earned'], 0)


class DailyJourneyTest(unittest.TestCase):
    def test_checkin_daily_practice_and_streak(self):
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as directory:
            current = [datetime(2026, 10, 17, 19, tzinfo=timezone.utc)]
            path = directory + '/daily.sqlite3'
            client = create_app(Store(path=path), now=lambda:current[0]).test_client()
            self.assertEqual(client.post('/checkins',json={'mood':'Low','effort':'small'}).status_code,400)
            client.post('/profiles',json={'goal':'Build my skills','interests':['Design'],'skills':['Writing']})
            self.assertEqual(client.post('/checkins',json={'mood':'Low','effort':'huge'}).status_code,400)
            client.post('/checkins',json={'mood':'Low','effort':'small'})
            self.assertEqual(client.get('/progress').json['streak'],0)
            feed=client.get('/opportunities').json
            self.assertTrue(all(o['minutes']==2 for o in feed['opportunities']))
            self.assertEqual(feed['opportunities'][0]['suggested_quest_id'],'design-small')
            client.post('/saved',json={'opportunity_id':'design'})
            def complete():
                return client.post('/completions',json={'quest_id':'design-small'}).json
            self.assertEqual(complete()['points_earned'],15)
            self.assertEqual(complete()['points_earned'],0)
            self.assertEqual(client.get('/progress').json['streak'],1)
            current[0]=datetime(2026,10,18,6,59,tzinfo=timezone.utc) # Still Oct 17 Pacific
            self.assertEqual(complete()['points_earned'],0)
            current[0]=datetime(2026,10,18,7,1,tzinfo=timezone.utc)
            self.assertIsNone(client.get('/checkins').json['checkin'])
            self.assertEqual(client.get('/progress').json['streak'],1)
            self.assertFalse(next(q for q in client.get('/quests').json['quests'] if q['id']=='design-small')['completed'])
            self.assertEqual(complete()['points_earned'],15)
            self.assertEqual(client.get('/progress').json['streak'],2)
            client.post('/checkins',json={'mood':'Good','effort':'big'})
            self.assertTrue(all(o['effort']=='big' for o in client.get('/opportunities').json['opportunities']))
            current[0]=datetime(2026,10,20,19,tzinfo=timezone.utc)
            self.assertEqual(client.get('/progress').json['streak'],0)
            self.assertEqual(complete()['progress']['streak'],1)
            reopened=create_app(Store(path=path), now=lambda:current[0]).test_client()
            self.assertEqual(reopened.get('/progress').json['longest_streak'],2)
            self.assertEqual(reopened.get('/progress').json['points'],45)

class CareerToolsTest(unittest.TestCase):
    def test_catalog_resume_and_analytics(self):
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as directory:
            store = Store(path=directory+'/career.sqlite3')
            client = create_app(store, now=lambda:datetime(2026,10,17,19,tzinfo=timezone.utc)).test_client()
            client.post('/profiles',json={'goal':'Build my skills','interests':['Technology'],'skills':['Coding']})
            feed = client.get('/opportunities').json['opportunities']
            self.assertEqual(len(feed),11)
            self.assertTrue(all(o['sample'] for o in feed))
            self.assertTrue({'Class','Club','Certification','Local event','Networking','Job simulation','Internship'}.issubset({o['kind'] for o in feed}))
            quests = client.get('/quests').json['quests']
            for o in feed:
                self.assertEqual({q['difficulty'] for q in quests if q['opportunity_id']==o['id'] and q.get('daily')}, {'Lazy','Easy','Hard','Challenging'})
            result = client.post('/resume-analysis',json={'text':'Built a React app using Python. Wrote documentation.','role':'Software developer'}).json
            self.assertEqual(result['found_skills'],['Coding','Writing'])
            self.assertEqual(result['gaps'],['Research'])
            self.assertTrue(result['recommendations'])
            self.assertFalse(any('text' in d for d in store.all('activity')))
            self.assertEqual(client.post('/resume-analysis',json={'text':'   '}).status_code,400)
            self.assertEqual(client.post('/resume-analysis',json={'text':'x'*30001}).status_code,400)
            self.assertEqual(client.post('/resume-analysis',json={'text':'Python','role':[]}).status_code,400)
            empty = client.get('/analytics').json
            self.assertEqual(empty['estimated_minutes'],0)
            self.assertIsNone(empty['top_skill'])
            client.post('/saved',json={'opportunity_id':'simulation'})
            for _ in range(2):
                client.post('/completions',json={'quest_id':'simulation-hard'})
            analytics = client.get('/analytics').json
            self.assertEqual(analytics['progress']['points'],100)
            self.assertEqual(analytics['estimated_minutes'],30)
            self.assertEqual(analytics['categories'],{'Job simulation':1})
            self.assertEqual(analytics['difficulties'],{'Hard':1})
            self.assertEqual(analytics['active_days'],1)
            self.assertEqual(sum(day['count'] for day in analytics['week']),1)

if __name__=='__main__':
    unittest.main()
