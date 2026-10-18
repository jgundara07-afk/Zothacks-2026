import tempfile
import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, Store
from test_support import create_test_app as create_app
from program_catalog import card
from opportunity_data.enrich import enrich
from opportunity_data.export_app import project


class NeutralFeedTests(unittest.TestCase):
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

    def test_no_interest_goal_matches_returns_labeled_neutral_alternatives(self):
        result=self.client.get('/opportunities',query_string={'interests':'Physics','goals':'Internship'}).json
        self.assertTrue(result['fallback']['active'])
        self.assertEqual(result['total'],2)
        self.assertEqual({row['title'] for row in result['opportunities']},{'A peaceful park','Mindfulness and personal growth'})
        self.assertTrue(all(row['recommendation_type']=='neutral' and not row['matching_tags'] for row in result['opportunities']))
        self.assertTrue(result['quests'])

    def test_real_matches_take_precedence_and_later_empty_pages_do_not_fallback(self):
        result=self.client.get('/opportunities',query_string={'interests':'Robotics'}).json
        self.assertFalse(result['fallback']['active'])
        self.assertEqual(result['total'],1)
        self.assertEqual(result['opportunities'][0]['title'],'Robotics programming')
        later=self.client.get('/opportunities',query_string={'interests':'Robotics','offset':10}).json
        self.assertFalse(later['fallback']['active'])
        self.assertEqual(later['opportunities'],[])

    def test_neutral_still_respects_location_time_skills_and_cost(self):
        online=self.client.get('/opportunities',query_string={'interests':'Physics','locations':'Online / Remote'}).json
        self.assertEqual([row['title'] for row in online['opportunities']],['Mindfulness and personal growth'])
        for extra in ({'max_minutes':5},{'cost':'Free'},{'skills':'Coding'},{'locations':'Near me','lat':0,'lon':0}):
            result=self.client.get('/opportunities',query_string={'interests':'Physics',**extra}).json
            self.assertEqual(result['total'],0,extra)
            self.assertFalse(result['fallback']['active'])

    def test_fallback_is_paginated_without_duplicates(self):
        first=self.client.get('/opportunities',query_string={'interests':'Physics','limit':1}).json
        second=self.client.get('/opportunities',query_string={'interests':'Physics','limit':1,'offset':1}).json
        self.assertTrue(first['fallback']['active'] and second['fallback']['active'])
        self.assertTrue(first['has_more'])
        self.assertFalse(second['has_more'])
        self.assertNotEqual(first['opportunities'][0]['id'],second['opportunities'][0]['id'])


if __name__=='__main__':unittest.main()
