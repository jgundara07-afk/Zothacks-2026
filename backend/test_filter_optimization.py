import tempfile
import unittest
from unittest.mock import patch
from app import create_app, Store
from ranking import match_details
from filter_rules import matches_search, matches_locations

class FilterOptimizationTest(unittest.TestCase):
    def test_title_evidence_ranks_ahead_of_incidental_description(self):
        primary=dict(title='Front-end engineering internship',description='',skills=[],personalization={'filter_interests':[],'goals':[]})
        incidental={**primary,'title':'Sales course','description':'Talk to a frontend engineer'}
        self.assertTrue(matches_search(primary,'frontend'))
        self.assertTrue(matches_search(incidental,'front-end'))
        self.assertGreater(match_details(primary,query='frontend')['score'],match_details(incidental,query='frontend')['score'])
        self.assertTrue(matches_search({'title':'Résumé building'},'resume'))
        self.assertFalse(matches_search({'title':'Frontend development'},'backend'))
        self.assertFalse(matches_search({'title':'Hiking trail'},'AI'))
        self.assertTrue(matches_search({'title':'AI research'},'AI'))

    def test_location_choices_are_alternatives(self):
        self.assertTrue(matches_locations(['Near me','Online / Remote'],['Online / Remote']))
        self.assertTrue(matches_locations(['Near me','Online / Remote'],['Near me']))
        self.assertFalse(matches_locations(['Near me'],['Online / Remote']))

    @patch('services.generate_recommendation', return_value=None)
    def test_related_suggestions_keep_hard_filters_and_pagination(self, generate):
        with tempfile.TemporaryDirectory() as directory:
            client=create_app(Store(path=directory+'/filters.sqlite3'),data_mode='catalog').test_client()
            query={'interests':'Astrophysics','goals':'Internship','locations':'Online / Remote','challenges':'Easy','max_minutes':120,'limit':10}
            first=client.get('/recommendations',query_string=query)
            self.assertEqual(first.status_code,200,first.json)
            self.assertTrue(first.json['opportunities'])
            for row in first.json['opportunities']:
                self.assertIn('Online / Remote',row['venues'])
                self.assertIn('Easy',row['personalization']['challenge_levels'])
                self.assertLessEqual(row['personalization']['duration']['max_minutes'],120)
            second=client.get('/recommendations',query_string={**query,'offset':10}).json
            self.assertFalse({o['id'] for o in first.json['opportunities']} & {o['id'] for o in second['opportunities']})
            self.assertEqual(client.get('/recommendations?cost=invalid').status_code,400)
            for route in ['/opportunities','/catalog/opportunities']:
                result=client.get(route,query_string={'q':'front-end','limit':5}).json
                self.assertTrue(result['opportunities'])
                self.assertTrue(all(matches_search(row,'frontend') for row in result['opportunities']))
                self.assertTrue(all('match_details' in row for row in result['opportunities']))


class AdvancedFilterTest(unittest.TestCase):
    @patch('services.generate_recommendation', return_value=None)
    def test_all_matches_are_subset_of_any_and_sorts_use_displayed_quest(self, generate):
        with tempfile.TemporaryDirectory() as directory:
            client=create_app(Store(path=directory+'/advanced.sqlite3'),data_mode='catalog').test_client()
            tags=['Frontend development','Machine learning']
            for route in ['/opportunities','/catalog/opportunities']:
                params=[('interests',v) for v in tags]
                any_result=client.get(route,query_string=params).json
                all_result=client.get(route,query_string=params+[('match_mode','all')]).json
                self.assertGreater(any_result['total'],all_result['total'])
                for row in all_result['opportunities']:
                    if row.get('recommendation_type')=='neutral':continue
                    self.assertTrue(set(tags).issubset(row['personalization']['filter_interests']))
            for sort in ['shortest','points']:
                first=client.get('/opportunities',query_string={'sort':sort,'limit':30}).json
                second=client.get('/opportunities',query_string={'sort':sort,'offset':30,'limit':30}).json
                rows=first['opportunities']+second['opportunities']
                quests={q['id']:q for q in first['quests']+second['quests']}
                values=[quests[o['suggested_quest_id']]['minutes' if sort=='shortest' else 'points'] for o in rows]
                self.assertEqual(values, sorted(values,reverse=sort=='points'))
                self.assertEqual(len(rows),len({o['id'] for o in rows}))
            for query in ['match_mode=bad','sort=bad','hide_saved=1','hide_completed=yes']:
                self.assertEqual(client.get('/opportunities?'+query).status_code,400)

    @patch('services.generate_recommendation', return_value=None)
    def test_saved_and_completed_hide_independently_and_daily_reset(self, generate):
        with tempfile.TemporaryDirectory() as directory:
            client=create_app(Store(path=directory+'/hide.sqlite3'),data_mode='catalog').test_client()
            client.post('/profiles',json={'interests':['Frontend development'],'skills':['Coding']})
            first=client.get('/opportunities?limit=1').json
            row=first['opportunities'][0]
            client.post('/saved',json={'opportunity_id':row['id']})
            visible=client.get('/opportunities?limit=100&hide_saved=true').json
            self.assertNotIn(row['id'],[o['id'] for o in visible['opportunities']])
            self.assertEqual(client.get('/saved').json['opportunities'][0]['id'],row['id'])
            first_quest=row['suggested_quest_id']
            result=client.post('/completions',json={'quest_id':first_quest})
            self.assertEqual(result.status_code,200)
            self.assertEqual(client.get('/progress').json['completed_count'],1)
            def card():
                rows=client.get('/opportunities?limit=100').json['opportunities']
                return next((o for o in rows if o['id']==row['id']),None)
            # Completed work never returns: a project card moves on to its next step, on later days too.
            after=card()
            if after: self.assertNotEqual(after['suggested_quest_id'],first_quest)
            from datetime import date,timedelta
            today=date.fromisoformat(client.get('/progress').json['today'])
            client.post('/demo/clock',json={'date':str(today+timedelta(days=1))})
            again=card()
            self.assertEqual(again and again['suggested_quest_id'],after and after['suggested_quest_id'])
