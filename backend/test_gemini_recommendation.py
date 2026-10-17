import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gemini_recommendation
from app import Store, create_app


class GeminiRecommendationTests(unittest.TestCase):
    def test_sends_only_choices_and_reads_generated_text(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            'candidates': [{'content': {'parts': [{'text': 'Draft a small project idea in 15 minutes.'}]}}]
        }).encode()
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-secret', 'GEMINI_MODEL': 'gemini-3.8-flash'}), \
             patch.object(gemini_recommendation, 'urlopen', return_value=response) as call:
            result = gemini_recommendation.generate_recommendation({'interests': ['Robotics'], 'time': ['15–30 min']})
        self.assertEqual(result, 'Draft a small project idea in 15 minutes.')
        request = call.call_args.args[0]
        self.assertEqual(request.headers['X-goog-api-key'], 'test-secret')
        self.assertIn('Robotics', json.loads(request.data)['contents'][0]['parts'][0]['text'])

    def test_missing_key_and_provider_failure_return_no_recommendation(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(gemini_recommendation, 'urlopen') as call:
            self.assertIsNone(gemini_recommendation.generate_recommendation({'goals': ['Internship']}))
            call.assert_not_called()
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-secret'}), \
             patch.object(gemini_recommendation, 'urlopen', side_effect=TimeoutError):
            self.assertIsNone(gemini_recommendation.generate_recommendation({'goals': ['Internship']}))

    def test_feed_calls_gemini_only_for_no_match_first_page(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch('services.generate_recommendation', return_value='Try a 15-minute portfolio sketch.') as generate:
            client = create_app(Store(path=directory + '/state.sqlite3'), data_mode='catalog').test_client()
            matched = client.get('/opportunities?interests=Software%20Engineering').json
            self.assertFalse(matched['fallback']['active'])
            generate.assert_not_called()

            later = client.get('/opportunities?interests=Astrophysics&offset=1').json
            self.assertNotIn('recommendation', later['fallback'])
            generate.assert_not_called()

            empty = client.get('/opportunities?interests=Astrophysics&cost=Free').json
            self.assertTrue(empty['fallback']['active'])
            self.assertEqual(empty['fallback']['recommendation'], 'Try a 15-minute portfolio sketch.')
            self.assertEqual(generate.call_count, 1)


if __name__ == '__main__':
    unittest.main()
