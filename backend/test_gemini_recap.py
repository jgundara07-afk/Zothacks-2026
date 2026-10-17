import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app import Store, create_app
from gemini_recommendation import RECAP_FIELDS, generate_recap_narrative


class GeminiRecapClientTest(unittest.TestCase):
    def test_sends_recorded_context_and_parses_structured_json(self):
        expected = {field: f"A grounded {field} line." for field in RECAP_FIELDS}

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({'candidates': [{'content': {'parts': [{'text': json.dumps(expected)}]}}]}).encode()

        context = {'recent_completed_quests': [{'title': 'Design a prototype', 'category': 'Design', 'skills': ['UI/UX']}], 'completed_count': 1}
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

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"candidates":[{"content":{"parts":[{"text":"not json"}]}}]}'

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}), patch('gemini_recommendation.urlopen', return_value=Response()):
            self.assertIsNone(generate_recap_narrative({'completed_count': 1}))


class RecapNarrativeRouteTest(unittest.TestCase):
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
        self.assertEqual(context['recent_completed_quests'][0]['title'], 'Find one tiny friction')
        self.assertEqual(context['category_counts'], {'Creative project': 1})
        self.assertNotIn('profile', context)

    def test_no_completions_uses_local_first_step_story_without_api_call(self):
        with tempfile.TemporaryDirectory() as directory, patch('routes.progress.generate_recap_narrative') as generate:
            client = create_app(data_mode='sample', store=Store(path=directory + '/empty.sqlite3')).test_client()
            response = client.post('/recap/narrative')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['source'], 'local')
        self.assertEqual(response.json['narrative']['archetype'], 'The First-Step Scout')
        generate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
