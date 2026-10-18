import json
import os
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from app import Store
from test_support import create_test_app as create_app
from gemini_recommendation import RECAP_FIELDS, generate_recap_narrative


class GeminiRecapClientTest(unittest.TestCase):
    def test_sends_recorded_context_and_parses_structured_json(self):
        expected = {field: f"A grounded {field} line." for field in RECAP_FIELDS}

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({'candidates': [{'content': {'parts': [{'text': json.dumps(expected)}]}}]}).encode()

        context = {'completed_quests': [{'date': '2026-10-01', 'title': 'Design a prototype', 'category': 'Design', 'skills': ['UI/UX']}], 'completed_count': 1}
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}), patch('gemini_recommendation.urlopen', return_value=Response()) as urlopen:
            result = generate_recap_narrative(context)

        self.assertEqual(result, expected)
        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.get_header('X-goog-api-key'), 'test-key')
        self.assertEqual(body['generationConfig']['responseMimeType'], 'application/json')
        self.assertEqual(body['generationConfig']['responseSchema']['required'], list(RECAP_FIELDS))
        self.assertIn('Design a prototype', body['contents'][0]['parts'][0]['text'])

    def test_missing_key_and_malformed_output_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(generate_recap_narrative({'completed_count': 1}))

    def test_quota_failure_is_reported_without_leaking_provider_details(self):
        diagnostics={}
        with patch.dict(os.environ, {'GEMINI_API_KEY':'private-test-key'}), patch('gemini_recommendation.urlopen',side_effect=HTTPError('https://example.test',429,'private-test-key',{},None)):
            self.assertIsNone(generate_recap_narrative({'completed_count':1},diagnostics=diagnostics))
        self.assertEqual(diagnostics['status'],'quota_exceeded')
        self.assertTrue(diagnostics['retryable'])
        self.assertNotIn('private-test-key',json.dumps(diagnostics))

    def test_malformed_output_fails_closed(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"candidates":[{"content":{"parts":[{"text":"not json"}]}}]}'

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}), patch('gemini_recommendation.urlopen', return_value=Response()):
            self.assertIsNone(generate_recap_narrative({'completed_count': 1}))


class RecapNarrativeRouteTest(unittest.TestCase):
    def prepare_history(self,directory):
        client=create_app(data_mode='sample',store=Store(path=directory+'/cache.sqlite3')).test_client()
        client.post('/profiles',json={'goal':'Build my skills','interests':['Design'],'skills':['Writing']})
        client.post('/saved',json={'opportunity_id':'design'})
        client.post('/completions',json={'quest_id':'design-small'})
        return client

    def test_success_is_reused_until_completed_history_changes(self):
        story={field:f'Generated {field}' for field in RECAP_FIELDS}
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative',return_value=story) as generate:
            client=self.prepare_history(directory)
            first=client.post('/recap/narrative').json
            second=client.post('/recap/narrative').json
            self.assertFalse(first['cached'])
            self.assertTrue(second['cached'])
            self.assertEqual(second['source'],'gemini')
            self.assertEqual(generate.call_count,1)
            client.post('/saved',json={'opportunity_id':'code'})
            client.post('/completions',json={'quest_id':'code-small'})
            third=client.post('/recap/narrative').json
            self.assertFalse(third['cached'])
            self.assertEqual(generate.call_count,2)

    def test_quota_cooldown_survives_repeated_page_requests(self):
        def quota(context,diagnostics):
            diagnostics.update(status='quota_exceeded',message='Gemini quota reached.',retryable=True)
            return None
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative',side_effect=quota) as generate:
            client=self.prepare_history(directory)
            first=client.post('/recap/narrative').json
            second=client.post('/recap/narrative').json
            self.assertEqual(first['source'],'local')
            self.assertEqual(second['generation']['status'],'quota_exceeded')
            self.assertIn('retry_at',second['generation'])
            self.assertEqual(generate.call_count,1)

    def test_completed_activity_is_sent_to_gemini_and_returned_to_frontend(self):
        story = {field: f"Generated {field}" for field in RECAP_FIELDS}
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative', return_value=story) as generate:
            client = create_app(data_mode='sample', store=Store(path=directory + '/recap.sqlite3')).test_client()
            client.post('/profiles', json={'goal': 'Build my skills', 'interests': ['Design'], 'skills': ['Writing']})
            client.post('/saved', json={'opportunity_id': 'design'})
            client.post('/completions', json={'quest_id': 'design-1'})

            response = client.post('/recap/narrative')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['source'], 'gemini')
        self.assertEqual(response.json['narrative'], story)
        self.assertEqual(response.json['activity_count'], 1)
        context = generate.call_args.args[0]
        self.assertEqual(context['completed_count'], 1)
        self.assertEqual(context['completed_quests'][0]['title'], 'Find one tiny friction')
        self.assertEqual(context['category_counts'], {'Creative project': 1})
        self.assertNotIn('profile', context)

    def test_all_months_of_completions_are_included_in_the_gemini_context(self):
        story = {field: f"Generated {field}" for field in RECAP_FIELDS}
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative', return_value=story) as generate:
            store = Store(path=directory + '/history.sqlite3')
            client = create_app(data_mode='sample', store=store).test_client()
            client.post('/profiles', json={'goal': 'Build my skills', 'interests': ['Design'], 'skills': ['Writing']})
            store.put_many('activity', [{
                'id': f'history:{index}', 'profile_id': 'demo', 'kind': 'completion',
                'quest_id': 'design-1', 'title': f'Quest {index}', 'category': 'Creative project',
                'skills': ['Writing'], 'difficulty': 'Easy', 'minutes': 10, 'points': 20,
                'completed_at': f'2026-{index // 31 + 1:02d}-{index % 28 + 1:02d}T12:00:00+00:00',
            } for index in range(35)])

            response = client.post('/recap/narrative')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['activity_count'], 35)
        context = generate.call_args.args[0]
        self.assertEqual(len(context['completed_quests']), 35)
        self.assertEqual(context['completed_quests'][0]['title'], 'Quest 0')
        self.assertEqual(context['completed_quests'][-1]['title'], 'Quest 34')
        self.assertIn('date', context['completed_quests'][0])

    def test_no_completions_uses_local_first_step_story_without_api_call(self):
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative') as generate:
            client = create_app(data_mode='sample', store=Store(path=directory + '/empty.sqlite3')).test_client()
            response = client.post('/recap/narrative')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['source'], 'local')
        self.assertEqual(response.json['narrative']['archetype'], 'The First-Step Scout')
        generate.assert_not_called()

    def test_local_story_gives_each_slide_its_own_grounded_facts(self):
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative', return_value=None):
            client = create_app(data_mode='sample', store=Store(path=directory + '/slides.sqlite3')).test_client()
            client.post('/profiles', json={'goal': 'Build my skills', 'interests': ['Design'], 'skills': ['Writing']})
            for opportunity, quest in (('design', 'design-1'), ('code', 'code-1'), ('green', 'green-1')):
                client.post('/saved', json={'opportunity_id': opportunity})
                client.post('/completions', json={'quest_id': quest})
            response = client.post('/recap/narrative').json

        stats, story = response['stats'], response['narrative']
        self.assertEqual(stats['completed_count'], 3)
        self.assertEqual(sum(stats['weekday_counts']), 3)
        self.assertEqual(stats['toughest_quest']['difficulty'], 'Medium')
        self.assertEqual(stats['category_count'], len(stats['categories']))
        self.assertTrue(set(RECAP_FIELDS) <= set(story))
        lines = [story[field] for field in RECAP_FIELDS]
        self.assertEqual(len(set(lines)), len(lines))
        self.assertIn(stats['busiest_weekday'], story['rhythm_line'])
        self.assertIn(stats['toughest_quest']['difficulty'], story['plot_twist'])

    def test_month_scope_observes_pacific_boundaries_and_empty_month_skips_model(self):
        story = {field: f'Generated {field}' for field in RECAP_FIELDS}
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative', return_value=story) as generate:
            store = Store(path=directory + '/monthly.sqlite3')
            client = create_app(data_mode='sample', store=store).test_client()
            for index, stamp in enumerate(['2026-10-01T06:59:00+00:00','2026-10-01T07:00:00+00:00','2026-11-01T06:59:00+00:00','2026-11-01T07:00:00+00:00']):
                store.put('activity', dict(id=f'row:{index}',profile_id='demo',kind='completion',quest_id='design-1',title=f'Quest {index}',category='Creative project',skills=['Writing'],difficulty='Easy',minutes=10,points=20,completed_at=stamp))
            response = client.post('/recap/narrative',json={'period':'month','month':'2026-10'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['activity_count'], 2)
            self.assertEqual(response.json['period'], 'month')
            context = generate.call_args.args[0]
            self.assertEqual([q['title'] for q in context['completed_quests']], ['Quest 1','Quest 2'])
            self.assertEqual(context['points'], 40)
            self.assertEqual(context['period_start'], '2026-10-01')
            self.assertEqual(context['period_end_exclusive'], '2026-11-01')
            generate.reset_mock()
            response=client.post('/recap/narrative',json={'period':'month','month':'2025-01'})
            self.assertEqual(response.json['activity_count'],0)
            self.assertEqual(response.json['source'],'local')
            generate.assert_not_called()
            for choices in [{'period':'week'},{'period':'month','month':'2026-13'},{'period':'month','month':'oops'},[]]:
                self.assertEqual(client.post('/recap/narrative',json=choices).status_code,400)


if __name__ == '__main__':
    unittest.main()
