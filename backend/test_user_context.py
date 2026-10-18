import tempfile
import unittest
from unittest.mock import patch
from app import create_app,Store
from user_context import validate_context,context_match,context_relevance,first_step_limit

class UserContextTest(unittest.TestCase):
    @patch('services.generate_recommendation', return_value=None)
    def test_profile_persistence_and_filters(self,generate):
        with tempfile.TemporaryDirectory() as directory:
            path=directory+'/context.sqlite3'
            client=create_app(Store(path=path),data_mode='catalog').test_client()
            context=dict(situation='Student',country='United States',state='California',city='Irvine',school='Fictional College',travel='Can commute',relocate='Open to it',experience='Complete beginner',availability='10–15 min',days='Either',formats=['Online'],budget='Free only',transportation='Bike')
            response=client.post('/profiles',json={'interests':[],'skills':['Research'],'context':context})
            self.assertEqual(response.status_code,200,response.json)
            for route in ['/opportunities','/recommendations']:
                feed=client.get(route+'?limit=50').json
                self.assertTrue(feed['context_applied'])
                self.assertTrue(feed['opportunities'])
                # Situation details are preferences, not gates: the feed stays full, and confirmed free picks rank on page one.
                self.assertGreaterEqual(len(feed['opportunities']),20)
                free=[row for row in feed['opportunities'] if row['personalization']['assessment']['cost']=='Free']
                self.assertTrue(free or route=='/recommendations')
            # Normal filter saves don't erase context, and reopening keeps it.
            client.post('/profiles',json={'interests':['Career Development'],'skills':['Research']})
            reopened=create_app(Store(path=path),data_mode='catalog').test_client()
            self.assertEqual(reopened.get('/opportunities').json['profile']['context'],context)
            for invalid in [{'formats':'Online'},{'experience':'Expert'},{'city':'x'*121},{'budget':None},{'unexpected':'value'}]:
                self.assertEqual(client.post('/profiles',json={'interests':[],'skills':['Research'],'context':invalid}).status_code,400)

    def row(self,**extra):
        return dict(title='Beginner volunteering in Irvine',location='Irvine, California',organization='Fictional College',coordinates={'latitude':33.7,'longitude':-117.8},personalization=dict(location_preferences=['In-person events'],assessment=dict(cost='Free',experience_level='Beginner',schedule_type='Scheduled')),source_facts=dict(start='2026-10-17T19:00:00Z'),**extra)

    def test_evidence_based_constraints_and_unknowns(self):
        row=self.row()
        self.assertTrue(context_match(row,{'days':'Weekends'},{}))
        self.assertFalse(context_match(row,{'days':'Weekdays'},{}))
        self.assertFalse(context_match(row,{'formats':['Online']},{}))
        self.assertTrue(context_match(row,{'travel':'Local only','city':'Irvine'},{}))
        self.assertFalse(context_match(row,{'travel':'Local only','city':'Los Angeles'},{}))
        self.assertGreater(context_relevance(row,{'city':'Irvine','school':'Fictional College'})[0],0)
        row['personalization']['assessment']['experience_level']='Advanced'
        self.assertFalse(context_match(row,{'experience':'Complete beginner'},{}))
        row['personalization']['assessment']['cost']='Unknown'
        self.assertFalse(context_match(row,{'budget':'Under $25'},{}))
        self.assertIsNone(first_step_limit({'availability':'2+ hours'}))
        self.assertEqual(first_step_limit({'availability':'30 min'}),30)
        # Missing dates do not invent day-of-week certainty.
        row['source_facts']={}
        self.assertTrue(context_match(row,{'days':'Weekdays'},{}))
