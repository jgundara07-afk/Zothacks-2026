"""Exercise the real portable catalog through the core app, without upstream network calls."""
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from app import create_app, Store

class CollectedJourneyTest(unittest.TestCase):
    def test_catalog_paging_filters_and_persistent_rewards(self):
        with tempfile.TemporaryDirectory() as directory:
            path = directory+'/catalog.sqlite3'
            current = [datetime(2026,10,17,19,tzinfo=timezone.utc)]
            def reopen():
                return create_app(Store(path=path), now=lambda:current[0], data_mode='catalog').test_client()
            client = reopen()
            health = client.get('/health').json
            self.assertEqual(health['data_mode'], 'catalog')
            self.assertEqual(health['catalog_records'], 28678)
            self.assertEqual(Store(path=path).all('opportunities'), [])
            first = client.get('/opportunities?limit=10').json
            second = client.get('/opportunities?limit=10&offset=10').json
            self.assertGreater(first['total'], 25000)
            self.assertTrue(first['has_more'])
            self.assertFalse({o['id'] for o in first['opportunities']} & {o['id'] for o in second['opportunities']})
            self.assertTrue(all(not o['sample'] and o['source_url'] for o in first['opportunities']))
            params = [('interests','Software Engineering'),('interests','AI & Machine Learning'),('goals','Internship'),('challenges','Challenging'),('time','Multi-day'),('locations','Online / Remote')]
            filtered = client.get('/opportunities',query_string=params)
            self.assertEqual(filtered.status_code,200)
            self.assertGreater(filtered.json['total'],0)
            for o in filtered.json['opportunities']:
                self.assertTrue(set(o['topics']) & {'Software Engineering','AI & Machine Learning'})
                self.assertIn('Internship',o['career_goals'])
                q = next(q for q in filtered.json['quests'] if q['id']==o['suggested_quest_id'])
                self.assertIn('Challenging',o['personalization']['challenge_levels'])
                self.assertIn('Multi-day',o['personalization']['time_buckets'])
                self.assertEqual(q['difficulty'],'Lazy')
                self.assertEqual(q['minutes'],2)
            o = second['opportunities'][0]
            q = next(q for q in second['quests'] if q['id']==o['suggested_quest_id'])
            self.assertEqual(client.post('/saved',json={'opportunity_id':o['id']}).status_code,400)
            profile = dict(goals=['Internship'], interests=['Software Engineering'],skills=['Coding'])
            self.assertEqual(client.post('/profiles',json=profile).status_code,200)
            self.assertEqual(client.post('/completions',json={'quest_id':q['id']}).status_code,400)
            for _ in range(2): self.assertEqual(client.post('/saved',json={'opportunity_id':o['id']}).status_code,200)
            result = client.post('/completions',json={'quest_id':q['id']}).json
            self.assertEqual(result['points_earned'],q['points'])
            self.assertEqual(client.post('/completions',json={'quest_id':q['id']}).json['points_earned'],0)
            reopened = reopen()
            self.assertEqual(reopened.get('/saved').json['opportunities'][0]['id'],o['id'])
            analytics = reopened.get('/analytics').json
            self.assertEqual(analytics['progress']['points'],q['points'])
            self.assertEqual(analytics['categories'],{o['kind']:1})
            self.assertEqual(analytics['estimated_minutes'],q['minutes'])
            self.assertTrue(next(x for x in reopened.get('/quests').json['quests'] if x['id']==q['id'])['completed'])
            current[0] += timedelta(days=1)
            self.assertEqual(reopened.post('/completions',json={'quest_id':q['id']}).json['points_earned'],q['points'])
            self.assertEqual(reopened.delete('/saved',json={'opportunity_id':o['id']}).status_code,200)
            self.assertEqual(reopened.get('/progress').json['saved_count'],0)
            self.assertEqual(reopened.get('/progress').json['completed_count'],2)

    def test_nearby_invalid_filters_and_resume_use_real_records(self):
        with tempfile.TemporaryDirectory() as directory:
            client = create_app(Store(path=directory+'/catalog.sqlite3'),data_mode='catalog').test_client()
            for query in ['limit=0','offset=-1','challenges=Impossible','locations=Near%20me','unknown=1','lat=nan&lon=0','step_size=Huge']:
                self.assertEqual(client.get('/opportunities?'+query).status_code,400,query)
            nearby = client.get('/opportunities',query_string={'locations':'Near me','lat':33.7,'lon':-117.8,'radius_km':10}).json
            self.assertEqual(nearby['total'],294)
            self.assertTrue(all(o['source']=='irvine' and 'Near me' in o['venues'] for o in nearby['opportunities']))
            result = client.post('/resume-analysis',json={'text':'Built an app with Python.','role':'Software developer'}).json
            self.assertTrue(result['recommendations'])
            self.assertTrue(all(not r['opportunity_id'].startswith('sample-') for r in result['recommendations']))
            self.assertEqual(client.post('/saved',json={'opportunity_id':'invalid'}).status_code,400)

    def test_three_choice_limits_and_canonical_filter_options(self):
        from preferences import PREFERENCES
        with tempfile.TemporaryDirectory() as directory:
            client = create_app(Store(path=directory+'/limits.sqlite3'),data_mode='catalog').test_client()
            options = client.get('/catalog/options').json
            self.assertEqual(options['max_selected_interests'],3)
            for ui,stored in [('interests','interests'),('challenges','challenge_levels'),('time','time_buckets'),('locations','location_preferences'),('commitments','commitment_preferences')]:
                self.assertEqual(PREFERENCES[ui],options[stored])
            self.assertEqual(['Internship' if g=='Land a software engineering internship' else g for g in options['goals']],PREFERENCES['goals'])
            for field in ['interests','goals']:
                values = PREFERENCES[field][:4]
                profile = dict(interests=['Software Engineering'],goals=[],skills=['Coding'])
                profile[field] = values
                self.assertEqual(client.post('/profiles',json=profile).status_code,400)
                self.assertEqual(client.get('/opportunities',query_string=[(field,v) for v in values]).status_code,400)
                canonical = options[field][:4]
                self.assertEqual(client.get('/catalog/opportunities',query_string=[(field,v) for v in canonical]).status_code,400)
                profile[field] = values[:3]
                self.assertEqual(client.post('/profiles',json=profile).status_code,200)
                self.assertEqual(client.get('/opportunities').json['profile'][field],values[:3])

if __name__ == '__main__':
    unittest.main()
