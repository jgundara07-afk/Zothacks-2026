import json
import unittest
from pathlib import Path
from .seed_tasks import task_facts
from .enrich import enrich
from .export_app import project,validate
from datetime import datetime,timezone


class AuthoredTaskTests(unittest.TestCase):
    def test_all_user_tasks_validate_without_fake_external_links(self):
        tasks=json.loads((Path(__file__).parent/'general_tasks.json').read_text(encoding='utf-8'))['tasks']
        self.assertEqual([task['number'] for task in tasks],list(range(1,61)))
        now=datetime(2026,10,17,tzinfo=timezone.utc)
        for task in tasks:
            row=enrich(task_facts(task,now.isoformat()))
            exported=project(row,now);validate(exported)
            self.assertEqual(exported['source_type'],'authored')
            self.assertEqual(exported['difficulty'],task['difficulty'])
            self.assertEqual(exported['personalization']['duration']['quality'],'Estimated')
            self.assertEqual(exported['personalization']['duration']['minutes'],task['minutes'])

    def test_external_source_still_requires_https(self):
        with self.assertRaises(ValueError):
            enrich(dict(source='coursera',source_id='1',kind='Online course',title='Python',source_url='urn:onething:general-task:1'))


if __name__=='__main__':unittest.main()
