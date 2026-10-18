import tempfile
import unittest
from unittest.mock import patch
from app import create_app, Store
from auth import normalize_email, supabase_settings


USERS = {
    'alice-token': {'id': 'alice-id', 'email': ' alice@GMAIL.COM ', 'email_confirmed_at': '2026-10-17T00:00:00Z', 'user_metadata': {'name': 'Alice'}},
    'bob-token': {'id': 'bob-id', 'email': 'bob@uci.edu', 'email_confirmed_at': '2026-10-17T00:00:00Z', 'user_metadata': {'name': 'Bob'}},
    'unverified': {'id': 'unverified-id', 'email': 'new@yahoo.com', 'email_confirmed_at': None},
    'unsupported': {'id': 'unsupported-id', 'email': 'bad@other.edu', 'email_confirmed_at': '2026-10-17T00:00:00Z'},
}


class AuthTest(unittest.TestCase):
    def test_supabase_settings_fall_back_to_public_vite_values(self):
        names = ['SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY', 'SUPABASE_ANON_KEY', 'VITE_SUPABASE_URL', 'VITE_SUPABASE_PUBLISHABLE_KEY', 'VITE_SUPABASE_ANON_KEY']
        with patch.dict('os.environ', {name: '' for name in names}):
            self.assertEqual(supabase_settings(), ('', ''))
        with patch.dict('os.environ', {**{name: '' for name in names}, 'VITE_SUPABASE_URL': 'https://example.supabase.co/', 'VITE_SUPABASE_PUBLISHABLE_KEY': 'sb_publishable_x'}):
            self.assertEqual(supabase_settings(), ('https://example.supabase.co', 'sb_publishable_x'))
        with patch.dict('os.environ', {'SUPABASE_URL': 'https://server.supabase.co', 'SUPABASE_PUBLISHABLE_KEY': 'sb_publishable_server', 'VITE_SUPABASE_URL': 'https://browser.supabase.co', 'VITE_SUPABASE_PUBLISHABLE_KEY': 'sb_publishable_browser'}):
            self.assertEqual(supabase_settings(), ('https://server.supabase.co', 'sb_publishable_server'))

    def test_email_policy(self):
        for domain in ['gmail.com', 'outlook.com', 'hotmail.com', 'live.com', 'yahoo.com', 'icloud.com', 'me.com', 'mac.com', 'proton.me', 'protonmail.com', 'uci.edu']:
            self.assertEqual(normalize_email('  Person+tag@' + domain.upper() + '  '), 'Person+tag@' + domain)
        for address in ['a@other.edu', 'a@gmail.com.evil', 'a@@gmail.com', 'a@gmail.com extra', 'a@-gmail.com', '.a@gmail.com', 'a..b@gmail.com', 'not-an-email', '']:
            with self.subTest(address=address), self.assertRaises(ValueError):
                normalize_email(address)

    def test_protected_routes_and_account_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            app = create_app(store=Store(path=directory + '/private.sqlite3'), data_mode='sample', auth_verifier=USERS.get)
            client = app.test_client()
            self.assertEqual(client.get('/health').status_code, 200)
            for path in ['/profiles', '/opportunities', '/saved', '/progress', '/analytics', '/progress/data', '/catalog/options']:
                self.assertEqual(client.get(path).status_code, 401, path)
            self.assertEqual(client.get('/progress', headers={'Authorization': 'Bearer bad'}).status_code, 401)
            self.assertEqual(client.get('/progress', headers={'Authorization': 'Bearer unverified'}).status_code, 403)
            self.assertEqual(client.get('/progress', headers={'Authorization': 'Bearer unsupported'}).status_code, 403)
            alice = {'Authorization': 'Bearer alice-token'}
            bob = {'Authorization': 'Bearer bob-token'}
            details = {'goal': 'Build my skills', 'interests': ['Design'], 'skills': ['Writing']}
            self.assertEqual(client.post('/profiles', headers=alice, json=details).status_code, 200)
            self.assertEqual(client.post('/profiles', headers=bob, json={**details, 'interests': ['Community']}).status_code, 200)
            self.assertEqual(client.get('/opportunities', headers=alice).json['profile']['name'], 'Alice')
            self.assertEqual(client.get('/opportunities', headers=bob).json['profile']['name'], 'Bob')
            self.assertEqual(client.post('/saved', headers=alice, json={'opportunity_id': 'design'}).status_code, 200)
            self.assertEqual(client.post('/completions', headers=alice, json={'quest_id': 'design-1'}).status_code, 200)
            self.assertEqual(client.get('/progress', headers=alice).json['completed_count'], 1)
            self.assertEqual(client.get('/progress', headers=bob).json['completed_count'], 0)
            self.assertEqual(client.get('/saved', headers=bob).json['opportunities'], [])
            self.assertEqual(client.get('/progress/data', headers=bob).json['profile_id'], 'bob-id')
            self.assertEqual(client.post('/completions', headers=bob, json={'quest_id': 'design-1'}).status_code, 400)
            recap_id = client.post('/recap/narrative', headers=alice, json={}).json['recap_id']
            self.assertEqual(client.post('/activity/events', headers=bob, json={'event': 'highlight_view', 'recap_id': recap_id}).status_code, 400)
            self.assertEqual(client.post('/demo/clock', headers=alice, json={'date': '2026-10-18'}).status_code, 403)
            self.assertEqual(client.get('/progress', headers=alice).json['completed_count'], 1)


if __name__ == '__main__':
    unittest.main()
