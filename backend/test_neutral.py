import tempfile
import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import Store
from test_support import create_test_app as create_app
from program_catalog import card
from opportunity_data.enrich import enrich
from opportunity_data.export_app import project


class NeutralFeedTests(unittest.TestCase):
    """The feed never empties: closest matches first, then farther ones, and an honest note when nothing is close."""
    def setUp(self):
        self.gemini = patch('services.generate_recommendation', return_value=None)
        self.gemini.start()
        self.directory = tempfile.TemporaryDirectory()
        self.now = datetime(2026,10,17,19,tzinfo=timezone.utc)
        def opportunity(identifier,title,kind,**extra):
            facts=dict(source='irvine' if kind=='Park' else 'coursera', source_id=identifier,
                       source_url='https://example.org/'+identifier,title=title,kind=kind,
                       description='Python coding practice.' if identifier=='robot' else '',
                       mode='Local' if kind=='Park' else 'Online',
                       provenance={'collected_at':self.now.isoformat()},**extra)
            return card(project(enrich(facts),self.now))
        rows=[opportunity('robot','Robotics programming','Online course',workload='2 hours'),
              opportunity('park','A peaceful park','Park',coordinates={'latitude':33.7,'longitude':-117.8}),
              opportunity('mindful','Mindfulness and personal growth','Online course',workload='1 hour'),
              opportunity('expired','Mindfulness retreat','Online course',workload='1 hour',start='2026-01-01T10:00:00+00:00',end='2026-01-01T11:00:00+00:00')]
        with patch('services.program_catalog',return_value={row['id']:row for row in rows}):
            self.client=create_app(Store(path=self.directory.name+'/state.sqlite3'),now=lambda:self.now,data_mode='catalog').test_client()

    def tearDown(self):
        self.directory.cleanup()
        self.gemini.stop()

    def titles(self, result):
        return [row['title'] for row in result['opportunities']]

    def test_no_close_match_still_returns_a_feed_with_an_honest_note(self):
        result=self.client.get('/opportunities',query_string={'interests':'Quantum computing'}).json
        self.assertTrue(result['fallback']['active'])
        self.assertIn('closest', result['fallback']['message'])
        self.assertEqual(set(self.titles(result)),{'Robotics programming','A peaceful park','Mindfulness and personal growth'})
        self.assertNotIn('Mindfulness retreat', self.titles(result))
        self.assertTrue(all(row['match_reason'] for row in result['opportunities']))
        self.assertTrue(result['quests'])

    def test_real_matches_come_first_then_the_feed_keeps_going(self):
        result=self.client.get('/opportunities',query_string={'interests':'Robotics'}).json
        self.assertFalse(result['fallback']['active'])
        self.assertEqual(self.titles(result)[0],'Robotics programming')
        self.assertEqual(result['opportunities'][0]['match_tier'],'close')
        self.assertEqual(result['total'],3)
        self.assertTrue(all(row['match_tier'] in {'related','explore'} for row in result['opportunities'][1:]))

    def test_filters_narrow_the_first_stretch_then_widen(self):
        online=self.client.get('/opportunities',query_string={'interests':'Quantum computing','locations':'Online / Remote'}).json
        inside=[row for row in online['opportunities'] if not row['beyond_filters']]
        self.assertEqual({row['title'] for row in inside},{'Robotics programming','Mindfulness and personal growth'})
        self.assertEqual(self.titles(online)[-1],'A peaceful park')
        self.assertTrue(online['opportunities'][-1]['beyond_filters'])
        for extra in ({'max_minutes':5},{'cost':'Free'},{'skills':'Coding'},{'locations':'Near me','lat':0,'lon':0}):
            result=self.client.get('/opportunities',query_string={'interests':'Quantum computing',**extra}).json
            self.assertGreater(result['total'],0,extra)
            self.assertTrue(all(row['match_reason'] for row in result['opportunities']),extra)

    def test_feed_pages_without_duplicates(self):
        first=self.client.get('/opportunities',query_string={'interests':'Quantum computing','limit':2}).json
        second=self.client.get('/opportunities',query_string={'interests':'Quantum computing','limit':2,'offset':2}).json
        self.assertTrue(first['has_more'])
        self.assertFalse(second['has_more'])
        ids=[row['id'] for row in first['opportunities']+second['opportunities']]
        self.assertEqual(len(ids),len(set(ids)))


if __name__=='__main__':unittest.main()
