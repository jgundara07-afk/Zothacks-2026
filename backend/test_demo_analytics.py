import tempfile
import unittest
from datetime import datetime, timezone
from app import create_app, Store

class DemoAnalyticsTest(unittest.TestCase):
    def test_date_persistence_daily_duplicates_and_ranges(self):
        with tempfile.TemporaryDirectory() as directory:
            path = directory + '/demo.sqlite3'
            now = lambda: datetime(2026, 10, 17, 19, tzinfo=timezone.utc)
            client = create_app(store=Store(path=path), now=now, data_mode='sample').test_client()
            client.post('/profiles', json={'goal':'Build my skills','interests':['Design'],'skills':['Writing']})
            client.post('/saved', json={'opportunity_id':'design'})
            for day in ['2026-10-17','2026-10-18','2026-11-01','2027-01-01']:
                self.assertEqual(client.post('/demo/clock', json={'date':day}).status_code, 200)
                self.assertFalse(client.post('/completions', json={'quest_id':'design-small'}).json['already_completed'])
                self.assertTrue(client.post('/completions', json={'quest_id':'design-small'}).json['already_completed'])
            for period, anchor, count, bins in [('day','2026-10-17',1,24),('week','2026-10-17',2,7),('month','2026-10-17',2,31),('year','2026-10-17',3,12)]:
                result = client.get('/analytics', query_string={'period':period,'date':anchor}).json
                self.assertEqual(result['completed_count'], count)
                self.assertEqual(sum(result['categories'].values()), count)
                self.assertEqual(sum(d['count'] for d in result['series']), count)
                self.assertEqual(len(result['series']), bins)
            monthly = client.get('/analytics?period=month&date=2026-10-17').json
            self.assertEqual([d['label'] for d in monthly['series']], [str(i) for i in range(1,32)])
            self.assertEqual(monthly['series'][16]['count'], 1)
            self.assertEqual(monthly['series'][17]['count'], 1)
            leap = client.get('/analytics?period=month&date=2028-02-15').json
            self.assertEqual(len(leap['series']), 29)
            snapshot = client.get('/progress/data?date=2026-10-17').json
            self.assertEqual(snapshot['schema_version'], 1)
            self.assertEqual(snapshot['progress']['completed_count'], 4)
            self.assertEqual(sum(d['count'] for d in snapshot['calendar']), 4)
            self.assertEqual(snapshot['analytics']['month']['completed_count'], 2)
            self.assertEqual(snapshot['recap']['completed_count'], 4)
            self.assertEqual(snapshot['climb']['fraction'], (snapshot['progress']['points']%100)/100)
            self.assertEqual(snapshot['climb']['mountain'], snapshot['progress']['points']//100+1)
            self.assertEqual(snapshot['climb']['level'], snapshot['progress']['points']//100+1)
            self.assertEqual(client.get('/progress/data?date=invalid').status_code, 400)
            reopened = create_app(store=Store(path=path), now=now, data_mode='sample').test_client()
            self.assertEqual(reopened.get('/progress').json['today'], '2027-01-01')
            self.assertEqual(reopened.post('/demo/clock', json={'reset':True}).json['today'], '2026-10-17')
            self.assertEqual(reopened.get('/progress').json['completed_count'], 4)
            self.assertEqual(reopened.post('/demo/clock', json={'date':'bad'}).status_code,400)
            self.assertEqual(reopened.get('/analytics?period=bad').status_code,400)
