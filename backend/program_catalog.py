"""Adapt the immutable collected catalog to the app's card and preparation-quest contract."""
from datetime import datetime, timezone
from functools import lru_cache
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

# Authored tasks whose single goal is itself the self-reported outcome (completing the task reports it).
TASK_OUTCOMES = {9: ['peer_endorsed'], 10: ['unsubscribed_five'], 20: ['followed_five'], 25: ['shortcut_five'], 28: ['portfolio_updated'],
                 36: ['workday_audit'], 37: ['focused_pomodoro'], 53: ['phone_free_walk'], 54: ['three_wins']}
# Authored "draft it" tasks get one helper step that actually sends it. The authored step stays unchanged as step 1.
TASK_FOLLOW_UPS = {
    8: ('Connect with them', 'Send the connection request you drafted, and mark this done once you are connected.', ['alumni_connected']),
    12: ('Post your introduction', 'Post the introduction you drafted in the community you chose.', ['community_posted']),
    14: ('Send the email', 'Send the cold-outreach email you drafted.', ['outreach_sent']),
    15: ('Set up the chat', 'Send your invitation and schedule the 15-minute conversation.', ['coffee_chat']),
}
# Big opportunities are projects: ordered helper quests, each a single goal that counts as its own completed quest.
# Each row: key, size, difficulty, minutes, base points, action, goal, outcomes the goal self-reports.
PROJECTS = {
    'career': [
        ('research', 'Small', 'Lazy', 5, 15, 'Read the listing', 'Open the listing, check it is current, and note the deadline and what it asks for.', []),
        ('resume', 'Medium', 'Easy', 20, 30, 'Refresh your resume', 'Update your resume with your latest classes, projects and experience.', []),
        ('tailor', 'Big', 'Medium', 25, 45, 'Tailor your resume', "Rewrite two or three resume bullets so they match this role's requirements.", []),
        ('materials', 'Big', 'Medium', 30, 50, 'Prepare your materials', 'Draft any cover letter or application answers, and gather links to your work.', []),
        ('apply', 'Big', 'Hard', 20, 75, 'Submit the application', 'Submit the application at the source and note the date you applied.', ['applied']),
        ('interview', 'Big', 'Challenging', 60, 90, 'Prep for the interview', 'Practice answers to three likely interview questions out loud.', [])],
    'course': [
        ('preview', 'Small', 'Lazy', 5, 15, 'Preview the course', 'Open the course, check it is current, and skim the syllabus.', []),
        ('lesson', 'Medium', 'Easy', 15, 30, 'Do the first lesson', 'Complete the first lesson and write down one thing you learned.', []),
        ('module', 'Big', 'Medium', 45, 50, 'Finish a module', 'Work through one full module and its practice questions.', []),
        ('halfway', 'Big', 'Hard', 120, 75, 'Reach the halfway point', 'Complete half of the course, including its graded work.', []),
        ('finish', 'Big', 'Challenging', 120, 100, 'Finish the course', 'Complete the final module and any certificate requirements.', ['certification_completed'])],
    'event': [
        ('rsvp', 'Small', 'Lazy', 5, 15, 'RSVP', 'Check the details at the source, RSVP, and add it to your calendar.', []),
        ('prepare', 'Medium', 'Easy', 15, 30, 'Prepare a question', 'Read about the speaker or topic and write one question to ask.', []),
        ('attend', 'Big', 'Hard', 90, 75, 'Go to the event', 'Attend the event and write down one takeaway.', ['event_attended']),
        ('thanks', 'Small', 'Easy', 5, 25, 'Send a thank-you', 'Send a thank-you note to the host or someone you met.', ['thank_you_sent'])],
}

def opportunity_group(o):
    kind = (o.get('kind') or '').lower()
    return ('career' if any(k in kind for k in ('intern', 'job')) else
            'event' if 'event' in kind or 'network' in kind else
            'outdoor' if any(k in kind for k in ('trail', 'park', 'sports')) else 'course')

def time_bucket(minutes):
    times = PREFERENCES['time']
    return times[0 if minutes < 5 else 1 if minutes <= 15 else 2 if minutes <= 30 else 3 if minutes <= 60 else 4 if minutes <= 180 else 5]

def preparation_quests(o):
    """Authored tasks get their action quest; big opportunities get ordered helper quests; outings get one quest."""
    if o.get('general_task'):
        task=o['general_task'];minutes=task['minutes'];difficulty=task['difficulty']
        size='Small' if minutes<=5 else 'Medium' if minutes<=15 else 'Big'
        quest=dict(id=o['id']+'::general',opportunity_id=o['id'],title=o['title'],description=o['description'],steps=task['steps'],
                   points={'Lazy':15,'Easy':25,'Medium':40,'Hard':60,'Challenging':90}[difficulty],minutes=minutes,difficulty=difficulty,
                   time_bucket=o['personalization']['time_buckets'][0],effort=size.lower(),size=size,daily=True,estimated=True,quest_type='general_task',
                   outcomes=TASK_OUTCOMES.get(task['number'],[]))
        follow_up=TASK_FOLLOW_UPS.get(task['number'])
        if not follow_up:
            return [quest]
        action,goal,outcomes=follow_up
        return [{**quest,'project':dict(step=1,total=2)},
                dict(id=o['id']+'::followup',opportunity_id=o['id'],title=action+': '+o['title'],action=action,description='Step 2 of 2. Do this only if and when you choose to.',
                     steps=[goal],points=25,minutes=5,difficulty='Easy',time_bucket=time_bucket(5),effort='small',size='Small',daily=False,estimated=True,
                     quest_type='helper',project=dict(step=2,total=2),outcomes=outcomes)]
    group = opportunity_group(o)
    level = (o['personalization'].get('challenge_levels') or ['Easy'])[-1]
    weight = {'Lazy': .8, 'Easy': 1, 'Medium': 1.3, 'Hard': 1.6, 'Challenging': 2}.get(level, 1)
    scaled = lambda base: max(5, int(round(base * weight / 5)) * 5)
    if group in PROJECTS:
        steps = PROJECTS[group]
        return [dict(id=o['id']+'::'+key, opportunity_id=o['id'], title=action+': '+o['title'], action=action,
                     description=f'Step {i} of {len(steps)} toward this opportunity. A self-reported step; verify details at the source first.',
                     steps=[goal], points=scaled(points), minutes=minutes, difficulty=difficulty, time_bucket=time_bucket(minutes),
                     effort='small' if size == 'Small' else 'medium' if size == 'Medium' else 'big', size=size, daily=False, estimated=True,
                     quest_type='helper', project=dict(step=i, total=len(steps)), outcomes=outcomes)
                for i,(key,size,difficulty,minutes,points,action,goal,outcomes) in enumerate(steps, 1)]
    # Outings (trails, parks, sports facilities) stay single quests in a choice of sizes.
    source = 'Open the linked source and check it is current.'
    ladder = [
        ('small', 'Small', 'Lazy', 5, 15, 'Plan the route', [source, 'Check the route, conditions and how to get there.']),
        ('medium', 'Medium', 'Easy', 15, 30, 'Pack and plan', ['Pick a day and time.', 'Pack water, layers and anything the place requires.']),
        ('big', 'Big', 'Medium', 30, 50, 'Take a short walk', ['Go for a short walk or warm-up there.', 'Note how it felt.']),
        ('hard', 'Big', 'Hard', 60, 75, 'Go', ['Check conditions at the source.', 'Go and do it at your own pace.', 'Note one thing you noticed.']),
        ('challenging', 'Big', 'Challenging', 120, 100, 'Do the full route', ['Plan for the full distance or session.', 'Complete it safely.', 'Record your time or distance.']),
        ('project', 'Big', 'Challenging', 240, 150, 'Plan a day trip', ['Plan a longer outing with stops and timing.', 'Go.', 'Write a short log of the day.'])]
    # A deterministic mix of suggested first steps, so not every card shows the smallest one.
    mix = ['small', 'big', 'hard']
    suggested = mix[sum(map(ord, o['id'])) % len(mix)]
    return [dict(id=o['id']+'::'+key, opportunity_id=o['id'], title=action+': '+o['title'], action=action,
                 description='A self-reported step toward this opportunity. Verify details at the source first.',
                 steps=steps, points=scaled(points), minutes=minutes, difficulty=difficulty,
                 time_bucket=time_bucket(minutes), effort=key if key in {'small','medium'} else 'big', size=size, daily=True,
                 estimated=True, quest_type='preparation', suggested=key == suggested, outcomes=[])
            for key,size,difficulty,minutes,points,action,steps in ladder]

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
