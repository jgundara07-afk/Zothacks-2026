import tempfile
import unittest

from test_support import create_test_app as create_app
from program_catalog import program_catalog, preparation_quests
from store import Store


class HelperQuestTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.client = create_app(Store(path=self.directory.name + '/helpers.sqlite3'), data_mode='catalog').test_client()
        self.client.post('/profiles', json={'interests': ['Software Engineering'], 'goals': ['Internship'], 'skills': ['Coding']})

    def tearDown(self):
        self.directory.cleanup()

    def card(self, opportunity_id, kind):
        rows = self.client.get('/opportunities', query_string={'kind': kind, 'limit': 100}).json['opportunities']
        return next((o for o in rows if o['id'] == opportunity_id), None)

    def test_internship_steps_each_count_once_and_the_card_leaves_after_the_last(self):
        catalog = program_catalog()
        o = next(row for row in catalog.values() if row['kind'] == 'Internship' and self.card(row['id'], 'Internship'))
        steps = preparation_quests(o)
        self.assertEqual([q['action'] for q in steps], ['Read the listing', 'Refresh your resume', 'Tailor your resume',
                                                        'Prepare your materials', 'Submit the application', 'Prep for the interview'])
        self.assertTrue(all(len(q['steps']) == 1 and not q['daily'] for q in steps))
        self.client.post('/saved', json={'opportunity_id': o['id']})
        points = 0
        for number, quest in enumerate(steps, 1):
            card = self.card(o['id'], 'Internship')
            self.assertEqual(card['suggested_quest_id'], quest['id'])
            result = self.client.post('/completions', json={'quest_id': quest['id']}).json
            self.assertEqual(result['points_earned'], quest['points'])
            self.assertEqual(self.client.post('/completions', json={'quest_id': quest['id']}).json['points_earned'], 0)
            points += quest['points']
            self.assertEqual(result['progress']['completed_count'], number)
        self.assertIsNone(self.card(o['id'], 'Internship'))
        self.assertEqual(self.client.get('/progress').json['points'], points)
        applied = next(b for b in self.client.get('/progress').json['achievements'] if b['id'] == 'mount-24')
        self.assertTrue(applied['unlocked'])

    def test_a_completed_single_quest_does_not_return(self):
        catalog = program_catalog()
        o = next(row for row in catalog.values() if row['kind'] == 'Trail' and self.card(row['id'], 'Trail'))
        self.client.post('/saved', json={'opportunity_id': o['id']})
        quest = self.card(o['id'], 'Trail')['suggested_quest_id']
        self.assertEqual(self.client.post('/completions', json={'quest_id': quest}).status_code, 200)
        self.assertIsNone(self.card(o['id'], 'Trail'))


if __name__ == '__main__':
    unittest.main()
