import json
import tempfile
import unittest
from pathlib import Path

from app import Store
from test_support import create_test_app as create_app

ROOT = Path(__file__).resolve().parents[1]


class RetiredInterestTests(unittest.TestCase):
    def test_interest_lists_stay_in_sync_and_exclude_retired_labels(self):
        preferences = json.loads((ROOT / 'shared' / 'preferences.json').read_text(encoding='utf-8'))
        taxonomy = json.loads((ROOT / 'opportunity_data' / 'taxonomy.json').read_text(encoding='utf-8'))
        manifest = json.loads((ROOT / 'backend' / 'catalog' / 'manifest.json').read_text(encoding='utf-8'))
        retired = set(preferences['retired_interests'])
        self.assertEqual(preferences['interests'], taxonomy['interests'])
        self.assertEqual(manifest['taxonomy']['interests'], taxonomy['interests'])
        self.assertFalse(retired & set(taxonomy['interests']))
        # Retired labels reach almost nothing in the catalog (fewer than 5 tagged records each).
        self.assertTrue(all(manifest['coverage']['interests'].get(label, 0) < 5 for label in retired))

    def test_saved_profile_with_retired_interest_still_saves_without_it(self):
        with tempfile.TemporaryDirectory() as directory:
            client = create_app(data_mode='sample', store=Store(path=directory + '/retired.sqlite3')).test_client()
            response = client.post('/profiles', json={'goal': 'Build my skills', 'interests': ['Robotics', 'Birdwatching'], 'skills': ['Research']})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['profile']['interests'], ['Robotics'])
            feed = client.get('/opportunities', query_string={'interests': 'Birdwatching'})
            self.assertEqual(feed.status_code, 200)


if __name__ == '__main__':
    unittest.main()
