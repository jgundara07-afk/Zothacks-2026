import unittest
from .enrich import enrich

class ExpandedInterestTests(unittest.TestCase):
    def row(self,title,description=''):
        return enrich({'source':'coursera','source_id':'test','source_url':'https://example.org/test',
                       'kind':'Online course','title':title,'description':description,
                       'provenance':{'collected_at':'2026-10-17T00:00:00+00:00'}})['personalization']

    def test_specific_subtopics_match_title_evidence(self):
        p=self.row('Frontend development with JavaScript')
        self.assertIn('Frontend development',p['filter_interests'])
        self.assertIn('Web development',p['filter_interests'])
        self.assertIn('Cloud computing',self.row('AWS Cloud Fundamentals')['filter_interests'])
        self.assertIn('Hiking',self.row('Hiking basics')['filter_interests'])

    def test_specific_tags_do_not_leak_from_generic_marketing(self):
        p=self.row('General learning','Explore robotics, camping, and cooking as future career possibilities.')
        self.assertNotIn('Robotics',p['filter_interests'])
        self.assertNotIn('Cooking',p['filter_interests'])

if __name__=='__main__':unittest.main()
