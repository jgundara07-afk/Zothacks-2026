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

if __name__=='__main__':
    unittest.main()
