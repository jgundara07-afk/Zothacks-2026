from uuid import uuid4
import hashlib
import json
import os
from flask import jsonify, request
from collections import Counter
from datetime import timedelta, date, datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import re
from pypdf import PdfReader
try:
    from ..achievement_expansion import OUTCOMES
    from ..achievements import completion_facts
    from . import body
    from ..gemini_recommendation import generate_recap_narrative
    from ..preferences import PREFERENCES
except ImportError:
    from achievement_expansion import OUTCOMES
    from achievements import completion_facts
    from routes import body
    from gemini_recommendation import generate_recap_narrative
    from preferences import PREFERENCES

WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DIFFICULTY_RANK = {'Lazy': 0, 'Easy': 1, 'Medium': 2, 'Hard': 3, 'Challenging': 4}


def recap_stats(completed, summary, day_of, best_streak, badges):
    """Facts for the recap slides, computed only from recorded completions in the period."""
    def quest(row):
        return dict(title=str(row.get('title') or 'Completed quest')[:180], date=day_of(row).isoformat(),
                    difficulty=row.get('difficulty') or 'Unknown', category=row.get('category') or 'Other')
    weekdays = [0] * 7
    per_day = Counter()
    for row in completed:
        day = day_of(row)
        weekdays[day.weekday()] += 1
        per_day[day] += 1
    busiest_day, busiest_count = max(per_day.items(), key=lambda item: (item[1], item[0])) if per_day else (None, 0)
    ranked = [row for row in completed if row.get('difficulty') in DIFFICULTY_RANK]
    toughest = max(ranked, key=lambda row: (DIFFICULTY_RANK[row['difficulty']], row.get('completed_at', ''))) if ranked else None
    earned = sorted((b for b in badges if b.get('earned_in_period')), key=lambda b: b.get('earned_at') or '')
    categories = Counter(summary['categories'])
    return dict(
        completed_count=summary['completed_count'], points=summary['points'], minutes=summary['estimated_minutes'],
        active_days=summary['active_days'], best_streak=best_streak,
        top_category=summary['top_category'], top_category_count=categories.most_common(1)[0][1] if categories else 0,
        category_count=len(categories), categories=[[name, count] for name, count in categories.most_common(4)],
        top_skills=[[name, count] for name, count in Counter(summary['skills']).most_common(3)],
        weekday_counts=weekdays, busiest_weekday=WEEKDAYS[weekdays.index(max(weekdays))] if completed else None,
        busiest_weekday_count=max(weekdays),
        busiest_day=dict(date=busiest_day.isoformat(), count=busiest_count) if busiest_day else None,
        first_quest=quest(completed[0]) if completed else None, latest_quest=quest(completed[-1]) if completed else None,
        toughest_quest=quest(toughest) if toughest else None, difficulties=summary['difficulties'],
        badges_earned=len(earned), latest_badge=earned[-1]['name'] if earned else None,
    )


def local_recap_story(stats, completed, archetypes):
    """Deterministic story used when Gemini is unavailable; every line is drawn from recorded facts."""
    if not completed:
        return {
            'archetype': 'The First-Step Scout',
            'evidence': 'Your recap is ready for your first completed quest.',
            'description': 'Your OneThing story is just getting started. One small step will give the next recap its first chapter.',
            'quest_line': 'The opening track is still yours to choose.',
            'signature_move': 'Start with a quest that fits the energy you have today.',
            'rhythm_line': 'No streak yet. The first day of one is any day you choose.',
            'plot_twist': 'The plot twist is that you do not need a grand plan to begin.',
            'onething_line': 'No points yet, and all the possibility in front of you.',
            'next_step': 'Pick one short quest and take its first step.',
        }
    n, category, skills = stats['completed_count'], stats['top_category'], stats['top_skills']
    plural = lambda count, word: f'{count} {word}' + ('' if count == 1 else 's')
    skill, skill_count = skills[0] if skills else (None, 0)
    first, latest, toughest = stats['first_quest'], stats['latest_quest'], stats['toughest_quest']
    weekday, weekday_count = stats['busiest_weekday'], stats['busiest_weekday_count']
    if skill and len(skills) > 1:
        pair = 'tied with' if skills[1][1] == skill_count else 'with'
        signature = f'{skill} kept showing up ({plural(skill_count, "time")}), {pair} {skills[1][0]} right beside it. That is a thread worth pulling.'
    elif skill:
        signature = f'You returned to {skill} {plural(skill_count, "time")}. Repetition is how a skill starts to feel like yours.'
    else:
        signature = f'You kept coming back to {category}: {plural(stats["top_category_count"], "quest")} and counting.'
    if stats['best_streak'] > 1:
        rhythm = f'Your best run was {stats["best_streak"]} days in a row, and {weekday}s carried the most quests ({weekday_count}).'
    elif stats['active_days'] > 1:
        rhythm = f'You showed up on {plural(stats["active_days"], "different day")}. {weekday}s were your most active.'
    else:
        rhythm = f'Everything happened on a single {weekday}. One focused day still counts as a chapter.'
    if toughest and first and DIFFICULTY_RANK.get(toughest['difficulty'], 0) > DIFFICULTY_RANK.get(first['difficulty'], 0):
        twist = f'You opened on a {first["difficulty"]} step and later chose a {toughest["difficulty"]} one. The climb got steeper and you kept going.'
    elif stats['category_count'] > 1:
        names = [name for name, _ in stats['categories']]
        twist = f'Your story crossed {stats["category_count"]} kinds of work, from {names[0]} to {names[-1]}. Range was the quiet theme.'
    elif n > 1:
        twist = f'Every quest stayed on {category}. Most stories wander; yours went deep instead.'
    else:
        twist = 'One finished quest is already more than most plans ever get. That is the twist.'
    hours = round(stats['minutes'] / 60, 1)
    effort = f'about {hours} hours' if stats['minutes'] >= 90 else plural(stats['minutes'], 'estimated minute')
    return {
        'archetype': archetypes.get(category, 'The OneThing Climber'),
        'evidence': f'{plural(stats["top_category_count"], category + " quest")}' + (f' · {skill} ×{skill_count}' if skill else ''),
        'description': f'Across {plural(stats["active_days"], "active day")}, your completed work leaned toward {category}. You kept turning a little time into progress you can point to.',
        'quest_line': f'{plural(n, "quest")} made the reel, most recently “{latest["title"]}”.' if n > 1 else f'“{latest["title"]}” opened your highlight reel.',
        'signature_move': signature,
        'rhythm_line': rhythm,
        'plot_twist': twist,
        'onething_line': f'{effort}, {stats["points"]} points' + (f' and {plural(stats["badges_earned"], "new badge")}' if stats['badges_earned'] else '') + ': proof that small things add up.',
        'next_step': f'Choose one manageable quest that builds on {skill}.' if skill else f'Pick one more {category} quest to keep the thread going.',
    }


def register(app, svc):
    db = svc.db
    clock = svc.clock
    profile = svc.profile
    activity = svc.activity
    checkin = svc.checkin
    completion_day = svc.completion_day
    progress = svc.progress
    opportunities = svc.opportunities
    today = svc.today

    @app.post('/demo/clock')
    def demo_clock():
        if not svc.demo_enabled:
            return jsonify(error='Demo date controls are disabled.'), 403
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError("Provide a demo date or reset in a JSON object.")
        target = data.get('date')
        if data.get('reset') is True:
            target = None
        else:
            try:
                parsed = date.fromisoformat(target)
                if not 2000 <= parsed.year <= 2100:
                    raise ValueError()
                target = parsed.isoformat()
            except (ValueError, TypeError):
                raise ValueError('Choose a valid demo date between 2000 and 2100 (YYYY-MM-DD).')
        db.put('activity', dict(id='demo-clock', profile_id='demo', kind='demo_clock', date=target))
        return jsonify(svc.demo_state())

    @app.get('/progress')
    def totals():
        return jsonify(progress())

    def analytics_payload(period=None, date_value=None):
        done = activity('completion')
        anchor = today()
        try:
            if date_value:
                anchor = date.fromisoformat(date_value)
        except ValueError:
            raise ValueError('Choose a valid analytics date (YYYY-MM-DD).')
        start = end = None
        if period:
            if period not in {'day', 'week', 'month', 'year'}:
                raise ValueError('Period must be day, week, month, or year.')
            start = anchor
            if period == 'week': start = anchor - timedelta(days=anchor.weekday())
            if period == 'month': start = anchor.replace(day=1)
            if period == 'year': start = anchor.replace(month=1, day=1)
            if period == 'day': end = start + timedelta(days=1)
            if period == 'week': end = start + timedelta(days=7)
            if period == 'month': end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            if period == 'year': end = start.replace(year=start.year+1)
            done = [a for a in done if start <= completion_day(a) < end]
        categories, skills, difficulties = (Counter(), Counter(), Counter())
        minutes = 0
        for a in done:
            q = svc.quest(a['quest_id']) or {}
            o = svc.opportunity(q.get('opportunity_id')) or {}
            categories[a.get('category', o.get('kind', 'Other'))] += 1
            skills.update(a.get('skills', o.get('skills', [])))
            difficulties[a.get('difficulty', q.get('difficulty', 'Easy'))] += 1
            minutes += a.get('minutes', q.get('minutes', 0))
        days = []
        for offset in range(6, -1, -1):
            day_date = today() - timedelta(days=offset)
            records = [a for a in done if completion_day(a) == day_date]
            days.append(dict(date=day_date.isoformat(), count=len(records), points=sum((a['points'] for a in records))))
        series = days
        if period:
            series = []
            bins = 24 if period == 'day' else 12 if period == 'year' else (end-start).days
            for i in range(bins):
                if period == 'day':
                    records = [a for a in done if datetime.fromisoformat(a['completed_at']).astimezone(ZoneInfo('America/Los_Angeles')).hour == i]
                    label = f'{i:02d}:00'
                elif period == 'year':
                    records = [a for a in done if completion_day(a).month == i+1]
                    label = date(start.year, i+1, 1).strftime('%b')
                else:
                    day = start + timedelta(days=i)
                    records = [a for a in done if completion_day(a) == day]
                    label = day.strftime('%a') if period == 'week' else str(day.day)
                series.append(dict(label=label, count=len(records)))
        return dict(period=period, start=start.isoformat() if start else None, end=end.isoformat() if end else None, series=series, completed_count=len(done), points=sum(a['points'] for a in done), progress=progress(), categories=dict(categories), skills=dict(skills), difficulties=dict(difficulties), estimated_minutes=minutes, active_days=len({completion_day(a) for a in done}), week=days, top_skill=skills.most_common(1)[0][0] if skills else None, top_category=categories.most_common(1)[0][0] if categories else None, method='Recorded activity; time is estimated from quest durations.')

    @app.get('/analytics')
    def analytics():
        return jsonify(analytics_payload(request.args.get('period'), request.args.get('date')))

    @app.post('/recap/narrative')
    def recap_narrative():
        options = request.get_json(silent=True)
        if options is None and request.data:
            raise ValueError('Provide recap choices as a JSON object.')
        options = {} if options is None else options
        if not isinstance(options, dict):
            raise ValueError('Provide recap choices as a JSON object.')
        period = options.get('period', 'lifetime')
        if period not in {'lifetime', 'month', 'year'}:
            raise ValueError('Choose a lifetime, month or year recap.')
        anchor = today().isoformat()
        if period == 'month':
            month = options.get('month', today().strftime('%Y-%m'))
            if not isinstance(month, str) or not re.fullmatch(r'\d{4}-\d{2}', month):
                raise ValueError('Choose a valid recap month (YYYY-MM).')
            anchor = month + '-01'
        if period == 'year':
            year = str(options.get('year', today().year))
            if not re.fullmatch(r'\d{4}', year) or not 2000 <= int(year) <= 2100:
                raise ValueError('Choose a valid recap year from 2000 to 2100.')
            anchor = year + '-01-01'
        summary = analytics_payload(period if period in {'month','year'} else None, anchor)
        completed = sorted(activity('completion'), key=lambda item: item.get('completed_at', ''))
        if period != 'lifetime':
            completed = [row for row in completed if summary['start'] <= completion_day(row).isoformat() < summary['end']]
        badges = svc.achievements()
        for badge in badges:
            earned_day = completion_day({'completed_at': badge['earned_at']}).isoformat() if badge['earned_at'] else None
            badge['earned_in_period'] = bool(earned_day and (period == 'lifetime' or summary['start'] <= earned_day < summary['end']))
        history = [{
            'date': completion_day(item).isoformat(),
            'title': str(item.get('title') or 'Completed quest')[:180],
            'category': str(item.get('category') or 'Other')[:80],
            'skills': [str(skill)[:80] for skill in item.get('skills', [])[:8]],
            'difficulty': str(item.get('difficulty') or 'Unknown')[:40],
        } for item in completed]
        days = sorted({completion_day(row) for row in completed})
        best = run = 0
        previous = None
        for day in days:
            run = run + 1 if previous and day == previous + timedelta(days=1) else 1
            best = max(best, run)
            previous = day
        stats = recap_stats(completed, summary, completion_day, best, badges)
        context = {
            'period': period, 'period_start': summary['start'], 'period_end_exclusive': summary['end'],
            'earned_badges': [badge['name'] for badge in badges if badge['earned_in_period']],
            'completed_count': summary['completed_count'],
            'estimated_minutes': summary['estimated_minutes'],
            'points': summary['points'],
            'active_days': summary['active_days'],
            'best_streak': best,
            'category_counts': summary['categories'],
            'skill_counts': summary['skills'],
            'difficulty_counts': summary['difficulties'],
            'weekday_counts': dict(zip(WEEKDAYS, stats['weekday_counts'])),
            'busiest_day': stats['busiest_day'],
            'toughest_quest': stats['toughest_quest'],
            'history_start': history[0]['date'] if history else None,
            'history_end': history[-1]['date'] if history else None,
            'completed_quests': history,
        }
        model=os.getenv('GEMINI_MODEL','gemini-3.5-flash-lite').strip()
        stable_context={key:value for key,value in context.items() if key!='earned_badges'}
        fingerprint=hashlib.sha256(json.dumps({'version':3,'model':model,'context':stable_context},sort_keys=True).encode()).hexdigest()
        cached_record=db.get('recap_cache',fingerprint) if completed else None
        cached=bool(cached_record)
        generation={'status':'no_activity','message':'Complete a quest in this period to generate a Gemini recap.','retryable':False}
        narrative=None
        if cached_record:
            narrative=cached_record['narrative']
            generation=dict(status='ready',message='Using your saved Gemini story for this quest history.',retryable=False)
        elif completed:
            scope=hashlib.sha256((model+'|'+os.getenv('GEMINI_API_KEY','').strip()).encode()).hexdigest()
            cooldown=db.get('recap_state',scope)
            now=svc.real_clock()
            if cooldown and datetime.fromisoformat(cooldown['retry_at'])>now:
                generation={**cooldown['generation'],'retry_at':cooldown['retry_at']}
            else:
                generation=dict(status='unavailable',message='Gemini did not return a story. Your local story is ready; you can retry.',retryable=True)
                narrative=generate_recap_narrative(context,diagnostics=generation)
                if narrative:
                    generation=dict(status='ready',message='Your Gemini story is ready.',retryable=False)
                    db.put('recap_cache',dict(id=fingerprint,narrative=narrative,model=model,created_at=now.isoformat()))
                elif generation['status']=='quota_exceeded':
                    retry_at=(now+timedelta(seconds=60)).isoformat()
                    db.put('recap_state',dict(id=scope,generation=generation,retry_at=retry_at))
                    generation={**generation,'retry_at':retry_at}
        source = 'gemini' if narrative else 'local'
        if not narrative:
            archetypes = {
                'General task': 'The Small-Step Strategist',
                'Online course': 'The Skill Collector',
                'Certification': 'The Skill Collector',
                'Class': 'The Curious Scholar',
                'Internship': 'The Career Pathfinder',
                'Job': 'The Career Pathfinder',
                'Job simulation': 'The Career Pathfinder',
                'Networking': 'The Connector',
                'Club': 'The Community Builder',
                'Park': 'The Trailblazer',
            }
            narrative = local_recap_story(stats, completed, archetypes)
        # Stories cached before these fields existed still render every slide.
        fallback = local_recap_story(stats, completed, {})
        for field in ('signature_move', 'rhythm_line', 'plot_twist'):
            narrative.setdefault(field, fallback[field])
        recap_id = 'recap:'+str(uuid4())
        highlights = [dict(title=row.get('title','Completed quest'),date=completion_day(row).isoformat()) for row in sorted(completed,key=lambda row:(row.get('points',0),row['completed_at']),reverse=True)[:5]]
        db.put('activity',dict(id=recap_id,profile_id='demo',kind='recap',period=period,month=anchor[:7],source=source,archetype=narrative['archetype'],has_highlights=bool(highlights),recorded_at=clock().isoformat()))
        badges = svc.achievements()
        for badge in badges:
            earned_day=completion_day({'completed_at':badge['earned_at']}).isoformat() if badge['earned_at'] else None
            badge['earned_in_period']=bool(earned_day and (period=='lifetime' or summary['start']<=earned_day<summary['end']))
        return jsonify(narrative=narrative, source=source, generation=generation,cached=cached,activity_count=len(completed),recap_id=recap_id,highlights=highlights,stats=stats,
                       period=period, start=summary['start'], end=summary['end'], badges=badges)

    @app.get('/progress/data')
    def progress_data():
        """Versioned, read-only handoff for the complete Progress experience."""
        totals = progress()
        points = max(0, totals['points'])
        dates = Counter(completion_day(a).isoformat() for a in totals['activity'])
        anchor = request.args.get('date') or today().isoformat()
        views = {period: analytics_payload(period, anchor) for period in ('week', 'month', 'year')}
        return jsonify(
            schema_version=1, profile_id='demo', timezone='America/Los_Angeles',
            generated_at=svc.real_clock().isoformat(), view_date=anchor,
            progress=totals,
            climb=dict(mountain=points//100+1, level=points//100+1,
                       fraction=(points%100)/100,
                       next_milestone=(points//100+1)*100,
                       points_to_next_milestone=100-points%100),
            calendar=[dict(date=day, count=count) for day, count in sorted(dates.items())],
            analytics=views, recap=analytics_payload(),
            definitions=dict(week='Monday–Sunday', month='One bin per day', year='One bin per month',
                             percentages='Divide each counter by the sum of that chart; skill tags may overlap.',
                             persistence='Completions, saves and demo date persist in the configured backend store.'))

    @app.post('/completions')
    def complete():
        data = body('quest_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        q = svc.quest(data['quest_id'])
        if not q:
            return (jsonify(error='Quest not found.'), 404)
        if q['opportunity_id'] not in [a['opportunity_id'] for a in activity('save')]:
            raise ValueError('Save this opportunity before completing its quest.')
        completion_id = 'completion:demo:' + q['id'] + (':' + today().isoformat() if q.get('daily') else '')
        opportunity = svc.opportunity(q['opportunity_id']) or {}
        actual_minutes = data.get('actual_minutes')
        if actual_minutes is not None and (type(actual_minutes) is not int or not 1 <= actual_minutes <= 1440):
            raise ValueError('Log between 1 and 1440 actual minutes, or leave time blank.')
        outcomes=data.get('outcomes',[])
        if not isinstance(outcomes,list) or len(outcomes)>3 or any(not isinstance(value,str) or value not in OUTCOMES for value in outcomes):
            raise ValueError('Choose up to 3 valid self-reported outcomes.')
        outcome_kinds={'applied':{'Job','Internship'},'certification_completed':{'Online course','Certification'},'simulation_completed':{'Job simulation'},'event_attended':{'Local event','Networking','Networking event','Campus event','Club','Campus initiative'}}
        if any(value in outcome_kinds and opportunity.get('kind') not in outcome_kinds[value] for value in outcomes):
            raise ValueError('Choose an outcome that belongs to this opportunity type.')
        # A quest whose single goal is the outcome (e.g. "Submit the application") self-reports it when completed.
        outcomes=outcomes+q.get('outcomes',[])
        saved_record=db.get('activity','save:demo:'+q['opportunity_id']) or {}
        goals=set((profile() or {}).get('goals',[])+[(profile() or {}).get('goal','')])
        work_log=dict(actual_minutes=actual_minutes,outcomes=list(dict.fromkeys(outcomes)),saved_at=saved_record.get('saved_at'),lazy_filter=saved_record.get('lazy_filter',False),goal_match=bool(goals.intersection(opportunity.get('career_goals',[]))))
        created = db.put('activity', dict(**work_log, **completion_facts(q, opportunity), opportunity_id=q['opportunity_id'], category=opportunity.get('kind', 'Other'), skills=opportunity.get('skills', []), difficulty=q.get('difficulty', 'Easy'), minutes=q.get('minutes', 0), id=completion_id, profile_id='demo', kind='completion', quest_id=q['id'], title=q['title'], points=q['points'], completed_at=clock().isoformat()), once=True)
        return jsonify(already_completed=not created, points_earned=q['points'] if created else 0, progress=progress())

    @app.get('/achievement-options')
    def achievement_options():
        return jsonify(outcomes=[dict(value=value,label=label) for value,label in OUTCOMES.items() if value != 'simulation_completed'])

    @app.post('/activity/events')
    def record_event():
        data=body('event')
        event=data['event']
        if event not in {'analytics_view','skills_view','fallback_read','highlight_view','share_click'}:
            raise ValueError('Choose a supported activity event.')
        recap_id=data.get('recap_id')
        if recap_id is not None and not isinstance(recap_id,str):
            raise ValueError('Provide a recap identifier as a string.')
        if event in {'fallback_read','highlight_view','share_click'}:
            if not isinstance(recap_id,str): raise ValueError('Choose a generated recap.')
            recap=db.get('activity',recap_id)
            if not recap or recap.get('kind')!='recap' or recap.get('profile_id')!='demo': raise ValueError('Recap not found.')
            if event=='fallback_read' and recap['source']!='local': raise ValueError('This recap is not a local fallback.')
            if event in {'highlight_view','share_click'} and not recap.get('has_highlights'): raise ValueError('This recap has no completed quests to share.')
        identifier='event:demo:'+event+':'+(recap_id if recap_id else today().isoformat())
        db.put('activity',dict(id=identifier,profile_id='demo',kind='ui_event',event=event,recorded_at=clock().isoformat()),once=True)
        return jsonify(recorded=True,achievements=svc.achievements())
