"""Evidence-based relevance: realistic profiles get specific, labeled, explained recommendations."""
import tempfile
import unittest
import urllib.parse
try:
    from .app import create_app, Store
    from .relevance import evidence, assess
except ImportError:
    from app import create_app, Store
    from relevance import evidence, assess


def feed(client, interests, goals, limit=20):
    client.post('/profiles', json={'interests': interests, 'goals': goals, 'skills': ['Writing'], 'preferences': {}})
    qs = urllib.parse.urlencode([(k, v) for k, vs in (('interests', interests), ('goals', goals)) for v in vs] + [('limit', limit)])
    return client.get('/opportunities?' + qs).json['opportunities']


class EvidenceTest(unittest.TestCase):
    def test_title_evidence_is_specific_and_quoted(self):
        row = dict(title='Product Manager Intern (TikTok)', kind='Internship', organization='TikTok', description='')
        result = assess(row, ['Product management'], ['Internship'], set())
        self.assertEqual(result['tier'], 'specific')
        self.assertIn('product manager internship at TikTok', result['reason'])
        self.assertIn('Internship', result['reason'])

    def test_description_mention_alone_is_only_related(self):
        row = dict(title='Battery Engineering Intern', kind='Internship', organization='GE', description='Work with a founder-led team.')
        self.assertEqual(assess(row, ['Entrepreneurship & Startups'], [], set())['tier'], 'adjacent')

    def test_same_word_different_meaning_is_ignored(self):
        row = dict(title='Student Internship - Commissioning & Startup', kind='Internship', organization='Bechtel', description='')
        self.assertEqual(evidence(row, ['Entrepreneurship & Startups']), [])

    def test_general_tasks_never_claim_a_match(self):
        result = assess(dict(title='The 20-20-20', kind='General task', general_task={'minutes': 1}), ['Product management'], [], set())
        self.assertEqual(result['tier'], 'general')


class ProfileFeedTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = create_app(Store(path=tempfile.mktemp())).test_client()

    def test_product_and_startups_profile(self):
        rows = feed(self.client, ['Product management', 'Entrepreneurship & Startups', 'Startup building'], ['Launch a startup or personal product', 'Internship'])
        top = rows[:12]
        self.assertTrue(all(r.get('match_tier') in {'specific', 'adjacent', 'general'} and r.get('match_reason') for r in top))
        self.assertGreaterEqual(sum(r['match_tier'] == 'specific' for r in top), 6)
        self.assertTrue(any(r['kind'] == 'Internship' and 'product' in r['title'].lower() for r in top), 'a product internship should surface')
        self.assertTrue(any(r['match_tier'] == 'adjacent' for r in top), 'the feed mixes in adjacent picks')

    def test_music_and_creative_profile(self):
        rows = feed(self.client, ['Music production', 'Content creation', 'Creative writing'], ['Build a strong project portfolio', 'Explore careers and discover my interests'])
        specific = [r for r in rows[:14] if r['match_tier'] == 'specific']
        self.assertTrue(any('music' in r['title'].lower() for r in specific), 'music should get a turn, not only content creation')
        for r in specific:
            self.assertTrue(any(word in r['match_reason'] for word in ('Music production', 'Content creation', 'Creative writing')))


if __name__ == '__main__':
    unittest.main()
