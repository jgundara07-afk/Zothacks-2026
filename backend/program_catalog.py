"""Adapt the immutable collected catalog to the app's card and preparation-quest contract."""
from datetime import datetime, timezone
from functools import lru_cache
import re
try:
    from .catalog_reader import load_catalog, distance_km
    from .preferences import PREFERENCES
except ImportError:
    from catalog_reader import load_catalog, distance_km
    from preferences import PREFERENCES

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
    # Steps depend on what the opportunity is: for an internship the first step might be writing one question,
    # or it might be applying outright. Each row: key, size, difficulty, minutes, time-bucket index, base points,
    # action (the short label shown on the card), steps.
    kind = (o.get('kind') or '').lower()
    group = ('career' if any(k in kind for k in ('intern', 'job')) else
             'event' if 'event' in kind or 'network' in kind else
             'outdoor' if any(k in kind for k in ('trail', 'park', 'sports')) else 'course')
    source = 'Open the linked source and check it is current.'
    ladders = {
        'career': [
            ('small', 'Small', 'Lazy', 2, 0, 15, 'Save it', [source, 'Note the deadline and what the application asks for.']),
            ('medium', 'Medium', 'Easy', 10, 1, 30, 'Write one question', [source, 'Write one specific question you would ask the team or a recruiter.']),
            ('big', 'Big', 'Medium', 25, 2, 50, 'Tailor your resume', ['Read the role requirements at the source.', 'Rewrite two resume bullets so they match the role.', 'Save the tailored version.']),
            ('hard', 'Big', 'Hard', 45, 3, 75, 'Apply', ['Check eligibility and the deadline at the source.', 'Attach your resume and answer the application questions.', 'Submit, and note the date you applied.']),
            ('challenging', 'Big', 'Challenging', 90, 4, 100, 'Prep for the interview', ['Research the team and the role.', 'Practice answers to three likely questions out loud.', 'Write down two questions to ask them.']),
            ('project', 'Big', 'Challenging', 240, 5, 150, 'Build a portfolio piece', ['Pick a small project that shows the skills the role needs.', 'Build a first version in a focused session.', 'Write a short summary you could share with the team.'])],
        'course': [
            ('small', 'Small', 'Lazy', 5, 1, 15, 'Preview it', [source, 'Skim the syllabus and pick the first lesson.']),
            ('medium', 'Medium', 'Easy', 15, 1, 30, 'Do the first lesson', ['Open the course and start lesson one.', 'Write down one thing you learned.']),
            ('big', 'Big', 'Medium', 30, 2, 50, 'Finish a module', ['Work through one full module.', 'Do its practice questions.', 'Note what to review next time.']),
            ('hard', 'Big', 'Hard', 60, 3, 75, 'Complete an exercise', ['Pick the module\'s graded exercise or project task.', 'Complete and submit it.', 'Review any feedback.']),
            ('challenging', 'Big', 'Challenging', 120, 4, 100, 'Finish a week of it', ['Work through a full week of the course.', 'Complete that week\'s assessments.', 'Write a short summary of what you can now do.']),
            ('project', 'Big', 'Challenging', 240, 5, 150, 'Build something with it', ['Choose a small project that uses what the course teaches.', 'Build a first version.', 'Share it or save it to your portfolio.'])],
        'event': [
            ('small', 'Small', 'Lazy', 2, 0, 15, 'RSVP', [source, 'RSVP and add it to your calendar.']),
            ('medium', 'Medium', 'Easy', 10, 1, 30, 'Prepare a question', ['Read the event description.', 'Write one question for the speaker or host.']),
            ('big', 'Big', 'Medium', 25, 2, 50, 'Read up on it', ['Look up the speaker or topic.', 'Note two things you want to learn there.']),
            ('hard', 'Big', 'Hard', 60, 3, 75, 'Go to it', ['Check the time and place at the source.', 'Attend the event.', 'Write down one takeaway.']),
            ('challenging', 'Big', 'Challenging', 120, 4, 100, 'Go and meet people', ['Attend the event.', 'Introduce yourself to two people.', 'Follow up with one of them afterwards.']),
            ('project', 'Big', 'Challenging', 240, 5, 150, 'Share what you learned', ['Attend and take notes.', 'Write a short post or summary.', 'Share it with a friend, club or class.'])],
        'outdoor': [
            ('small', 'Small', 'Lazy', 5, 1, 15, 'Plan the route', [source, 'Check the route, conditions and how to get there.']),
            ('medium', 'Medium', 'Easy', 15, 1, 30, 'Pack and plan', ['Pick a day and time.', 'Pack water, layers and anything the place requires.']),
            ('big', 'Big', 'Medium', 30, 2, 50, 'Take a short walk', ['Go for a short walk or warm-up there.', 'Note how it felt.']),
            ('hard', 'Big', 'Hard', 60, 3, 75, 'Go', ['Check conditions at the source.', 'Go and do it at your own pace.', 'Note one thing you noticed.']),
            ('challenging', 'Big', 'Challenging', 120, 4, 100, 'Do the full route', ['Plan for the full distance or session.', 'Complete it safely.', 'Record your time or distance.']),
            ('project', 'Big', 'Challenging', 240, 5, 150, 'Plan a day trip', ['Plan a longer outing with stops and timing.', 'Go.', 'Write a short log of the day.'])],
    }
    # A deterministic mix of suggested first steps, so not every card shows the smallest one.
    mix = {'career': ['medium', 'big', 'hard'], 'course': ['small', 'medium', 'big'], 'event': ['small', 'medium', 'hard'], 'outdoor': ['small', 'big', 'hard']}[group]
    suggested = mix[sum(map(ord, o['id'])) % len(mix)]
    times = PREFERENCES['time']
    level = (o['personalization'].get('challenge_levels') or ['Easy'])[-1]
    weight = {'Lazy': .8, 'Easy': 1, 'Medium': 1.3, 'Hard': 1.6, 'Challenging': 2}.get(level, 1)
    scaled = lambda base: max(5, int(round(base * weight / 5)) * 5)
    return [dict(id=o['id']+'::'+key, opportunity_id=o['id'], title=action+': '+o['title'], action=action,
                 description='A self-reported step toward this opportunity. Verify details at the source first.',
                 steps=steps, points=scaled(points), minutes=minutes, difficulty=difficulty,
                 time_bucket=times[bucket], effort=key if key in {'small','medium'} else 'big', size=size, daily=True,
                 estimated=True, quest_type='preparation', suggested=key == suggested)
            for key,size,difficulty,minutes,bucket,points,action,steps in ladders[group]]

def available(o, now):
    if o['status'] in {'past', 'cancelled'}:
        return False
    # Some imported internship records have no closing date. Do not offer a
    # cohort whose named season has already ended as a current opportunity.
    title = o.get('title') or ''
    season = re.search(r'\b(summer|spring|winter|fall)\s+(20\d{2})\b|\b(20\d{2})\s+(summer|spring|winter|fall)\b', title, re.I)
    if season:
        name = (season.group(1) or season.group(4)).lower()
        year = int(season.group(2) or season.group(3))
        end_month = {'winter': 3, 'spring': 5, 'summer': 8, 'fall': 12}[name]
        if (now.year, now.month) > (year, end_month):
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
