"""Manually upsert user-supplied general tasks into the current normalized catalog."""
import json
from datetime import datetime,timezone
from pathlib import Path
from .database import Catalog
from .enrich import enrich

ROOT=Path(__file__).resolve().parent

def task_facts(task,now):
    identifier=f"{task['number']:03d}"
    return dict(source='onething',source_id=identifier,source_url='urn:onething:general-task:'+identifier,
                kind='General task',title=task['title'],description=task['description'],
                organization='OneThing',general_task=task,mode='Online' if task['number']<=45 or task['number'] in {57,58,59,60} else None,
                is_free=True,availability='Self-guided task; adapt to your circumstances. No external listing or enrollment.',
                provenance={'collected_at':now,'authored':True,'origin':'User-supplied general task list'})

def main():
    payload=json.loads((ROOT/'general_tasks.json').read_text(encoding='utf-8'))
    assert len(payload['tasks'])==60 and len({task['number'] for task in payload['tasks']})==60
    catalog=Catalog(ROOT/'data'/'opportunities.sqlite3')
    now=datetime.now(timezone.utc).isoformat()
    try:
        for task in payload['tasks']:catalog.put(enrich(task_facts(task,now)))
        print(json.dumps(catalog.stats(),indent=2))
    finally:catalog.close()

if __name__=='__main__':main()
