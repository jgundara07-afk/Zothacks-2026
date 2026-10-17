from flask import jsonify, request
from collections import Counter
from datetime import timedelta, date, datetime
from zoneinfo import ZoneInfo
from io import BytesIO
import re
from pypdf import PdfReader
try:
    from . import body
    from ..preferences import PREFERENCES
except ImportError:
    from routes import body
    from preferences import PREFERENCES

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
            categories[o.get('kind', 'Other')] += 1
            skills.update(o.get('skills', []))
            difficulties[q.get('difficulty', 'Easy')] += 1
            minutes += q.get('minutes', 0)
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
            climb=dict(mountain=max(1, (points+499)//500), level=points//100+1,
                       fraction=((points-1)%500+1)/500 if points else 0,
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
        created = db.put('activity', dict(id=completion_id, profile_id='demo', kind='completion', quest_id=q['id'], title=q['title'], points=q['points'], completed_at=clock().isoformat()), once=True)
        return jsonify(already_completed=not created, points_earned=q['points'] if created else 0, progress=progress())
