import unittest
from ranking import rank_records


class RankingTests(unittest.TestCase):
    def rows(self):
        return [dict(id='duplicate-1',title='Python basics',organization='Courses',kind='Online course'),
                dict(id='duplicate-2',title='Python basics',organization='Courses',kind='Online course'),
                dict(id='unique',title='Mentor evening',organization='Local club',kind='Campus event')]

    def test_rarity_breaks_relevance_ties_but_cannot_override_a_match(self):
        rows=self.rows()
        equal=rank_records(rows,lambda row:1)
        self.assertEqual(equal[0][0]['id'],'unique')
        self.assertTrue(all(0 < bonus <= .25 for _,_,bonus in equal))
        relevant=rank_records(rows,lambda row:int(row['id']!='unique'))
        self.assertEqual(relevant[-1][0]['id'],'unique')

    def test_order_is_repeatable_and_pagination_has_no_repeats(self):
        rows=self.rows()
        order=lambda:[row['id'] for row,_,_ in rank_records(rows,lambda row:0)]
        self.assertEqual(order(),order())
        self.assertEqual(len(set(order()[:2]+order()[2:])),len(rows))


if __name__=='__main__':unittest.main()
