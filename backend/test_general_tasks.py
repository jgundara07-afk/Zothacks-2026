import tempfile
import unittest
from unittest.mock import patch
from app import Store
from test_support import create_test_app as create_app
from program_catalog import program_catalog,preparation_quests


class GeneralTaskJourneyTests(unittest.TestCase):
    def setUp(self):
        self.gemini = patch('services.generate_recommendation', return_value=None)
        self.gemini.start()

    def tearDown(self):
        self.gemini.stop()

    def test_sixty_authored_tasks_have_real_action_quests(self):
        tasks=[o for o in program_catalog().values() if o.get('general_task')]
        self.assertEqual(len(tasks),60)
        self.assertEqual(len({o['id'] for o in tasks}),60)
        for o in tasks:
            self.assertEqual(o['source_type'],'authored')
            q,*follow_up=preparation_quests(o)
            # "Draft it" tasks keep the authored step first and add one helper step that sends it.
            self.assertLessEqual(len(follow_up),1)
            if follow_up: self.assertEqual((follow_up[0]['quest_type'],follow_up[0]['project']['step']),('helper',2))
            self.assertEqual(q['quest_type'],'general_task')
            self.assertEqual(q['steps'],o['general_task']['steps'])
            self.assertEqual(q['difficulty'],o['general_task']['difficulty'])
            self.assertEqual(q['minutes'],o['general_task']['minutes'])
            self.assertNotIn('Review the source',q['title'])

    def test_fallback_prioritizes_general_tasks_and_completion_counts_once(self):
        with tempfile.TemporaryDirectory() as directory:
            client=create_app(Store(path=directory+'/state.sqlite3'),data_mode='catalog').test_client()
            result=client.get('/opportunities',query_string={'interests':'Quantum computing','goals':'Internship','limit':10}).json
            self.assertTrue(result['opportunities'])
            o=next(o for o in result['opportunities'] if o.get('general_task'))
            self.assertEqual(o['placement'],'sprinkled')
            q=next(q for q in result['quests'] if q['opportunity_id']==o['id'])
            self.assertEqual(client.post('/profiles',json={'interests':[],'goals':[],'skills':['Writing']}).status_code,200)
            self.assertEqual(client.post('/saved',json={'opportunity_id':o['id']}).status_code,200)
            first=client.post('/completions',json={'quest_id':q['id']}).json
            second=client.post('/completions',json={'quest_id':q['id']}).json
            self.assertEqual(first['points_earned'],q['points'])
            self.assertEqual(second['points_earned'],0)

    def test_sprinkling_is_sparse_stable_and_respects_explicit_constraints(self):
        with tempfile.TemporaryDirectory() as directory:
            client=create_app(Store(path=directory+'/state.sqlite3'),data_mode='catalog').test_client()
            first=client.get('/opportunities?interests=Software%20Engineering&limit=16').json
            second=client.get('/opportunities?interests=Software%20Engineering&limit=16&offset=16').json
            self.assertFalse(first['fallback']['active'])
            self.assertEqual([i for i,o in enumerate(first['opportunities']) if o.get('general_task')],[7,15])
            self.assertFalse({o['id'] for o in first['opportunities']} & {o['id'] for o in second['opportunities']})
            for params in ({'kind':'Internship'},{'duration_quality':'Source reported'},{'locations':'Near me','lat':33.7,'lon':-117.8}):
                response=client.get('/opportunities',query_string=params).json
                self.assertFalse(any(o.get('general_task') for o in response['opportunities']))


if __name__=='__main__':unittest.main()
