import tempfile
import unittest
from app import create_app, Store
from test_support import create_test_app as create_app
from goal_matching import RULES, with_goal_matches

class GoalFilterTest(unittest.TestCase):
    def test_new_goals_work_on_both_search_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            client = create_app(Store(path=directory+'/goals.sqlite3'), data_mode='catalog').test_client()
            self.assertTrue(set(RULES).issubset(client.get('/catalog/options').json['goals']))
            for goal in RULES:
                for route in ['/opportunities', '/catalog/opportunities']:
                    response = client.get(route, query_string={'goals':goal,'limit':3})
                    self.assertEqual(response.status_code,200,(goal,response.json))
                    self.assertGreater(response.json['total'],0,goal)
                    for row in response.json['opportunities']:
                        if row.get('placement') == 'sprinkled': continue
                        self.assertIn(goal,row['personalization']['goals'])
                        self.assertIn(goal,row['personalization']['inferred_goal_matches'])
                # Selecting goals does not exempt other constraints.
                response=client.get('/opportunities',query_string={'goals':goal,'locations':'Near me','lat':0,'lon':0})
                self.assertEqual(response.json['total'],0)

    def test_incidental_description_does_not_create_goal_match(self):
        row=with_goal_matches({'title':'Walking practice','description':'Open source research certification internship competition LinkedIn', 'personalization':{'goals':[]}})
        self.assertEqual(row['personalization']['inferred_goal_matches'],{})
