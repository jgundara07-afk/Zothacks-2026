"""Adapt the immutable collected catalog to the app's card and preparation-quest contract."""
from datetime import datetime, timezone
from functools import lru_cache
try:
    from .catalog_reader import load_catalog, distance_km
except ImportError:
    from catalog_reader import load_catalog, distance_km

INTERNSHIP = 'Land a software engineering internship'

def card(row):
    p = row['personalization']
    return {**row, 'topics': p['interests'],
            'career_goals': ['Internship' if g == INTERNSHIP else g for g in p['goals']],
            'venues': p['location_preferences'], 'multi_day': 'Multi-day' in p['time_buckets'],
            'commitment_type': 'long-term' if p['commitment'].startswith('Long-term') else 'quick',
            'commitment': p['commitment'], 'mode': row.get('mode') or ('Self-guided' if row.get('general_task') else 'Check source'),
            'requirements': row['general_task'].get('requirements',[]) if row.get('general_task') else ['Check current eligibility, prerequisites, availability and access at the source.'],
            'source_type': row.get('source_type','cached'), 'color': row.get('color') or 'yellow'}

def preparation_quests(o):
    """External opportunities get preparation quests; authored tasks get actual action quests."""
    if o.get('general_task'):
        task=o['general_task'];minutes=task['minutes'];difficulty=task['difficulty']
        size='Small' if minutes<=5 else 'Medium' if minutes<=15 else 'Big'
        return [dict(id=o['id']+'::general',opportunity_id=o['id'],title=o['title'],description=o['description'],steps=task['steps'],
                     points={'Lazy':15,'Easy':25,'Medium':40,'Hard':60,'Challenging':90}[difficulty],minutes=minutes,difficulty=difficulty,
                     time_bucket=o['personalization']['time_buckets'][0],effort=size.lower(),size=size,daily=True,estimated=True,quest_type='general_task')]
    plans = [
        ('small', 'Small', 'Lazy', 2, 'Under 5 min', 15, 'Review the source',
         ['Open the linked source and check current availability and access.', 'Write one question or a fresh next step.']),
        ('medium', 'Medium', 'Easy', 10, '5–15 min', 30, 'Choose your next step',
         ['Read the source requirements and restrictions.', o.get('suggested_first_step') or 'Write a specific next step.', 'Record what you learned and what you need to verify.']),
        ('big', 'Big', 'Medium', 20, '15–30 min', 50, 'Make a preparation plan',
         ['Review eligibility, timing and any costs at the source.', 'List the skills or preparation this opportunity needs.', 'Create one concrete deliverable or plan and record your next action.']),
        ('hard', 'Big', 'Hard', 45, '30–60 min', 75, 'Practice for the opportunity',
         ['Verify that the source is current and relevant to your goal.', 'Choose a relevant skill or preparation exercise and spend focused time on it.', 'Save your practice notes or work and identify what remains.']),
        ('challenging', 'Big', 'Challenging', 90, '1–3 hours', 100, 'Build a preparation deliverable',
         ['Verify eligibility and choose a relevant preparation deliverable.', 'Spend a focused session producing a draft, practice artifact or detailed plan.', 'Review your work, record evidence and choose a next step.']),
        ('project', 'Big', 'Challenging', 240, '3+ hours', 150, 'Develop a preparation project',
         ['Verify the source and define a relevant project with achievable milestones.', 'Spend a longer focused work session developing your project, allowing breaks.', 'Review the deliverable, record your work and decide what you will do next.'])]
    return [dict(id=o['id']+'::'+key, opportunity_id=o['id'], title=title+': '+o['title'],
                 description='A self-reported preparation quest. This does not complete the course, job, event or outdoor activity. Verify source details first; use a fresh action for each daily practice.',
                 steps=steps, points=points, minutes=minutes, difficulty=difficulty,
                 time_bucket=bucket, effort=key if key in {'small','medium'} else 'big', size=size, daily=True,
                 estimated=True, quest_type='preparation')
            for key,size,difficulty,minutes,bucket,points,title,steps in plans]

def available(o, now):
    if o['status'] in {'past', 'cancelled'}:
        return False
    end = o.get('source_facts', {}).get('end')
    if isinstance(end, dict):
        end = end.get('utc')
    if isinstance(end, str):
        try:
            parsed = datetime.fromisoformat(end.replace('Z', '+00:00'))
            if parsed.tzinfo is not None:
                return parsed.astimezone(timezone.utc) >= now.astimezone(timezone.utc)
        except (ValueError, TypeError):
            pass
    return True

@lru_cache(maxsize=1)
def program_catalog():
    catalog = load_catalog()
    return {row['id']: card(row) for row in catalog.rows}
