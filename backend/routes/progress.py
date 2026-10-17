from collections import Counter
from datetime import timedelta
from flask import jsonify
from routes import body

def register(app, svc):
    db = svc.db
    @app.get('/progress')
    def totals():
        return jsonify(svc.progress())
    @app.get('/analytics')
    def analytics():
        done = svc.activity('completion')
        quests_by_id = {q['id']:q for q in db.all('quests')}
        opps = {o['id']:o for o in db.all('opportunities')}
        categories, skills, difficulties = Counter(), Counter(), Counter()
        minutes = 0
        for a in done:
            q = quests_by_id.get(a['quest_id'], {})
            o = opps.get(q.get('opportunity_id'), {})
            categories[o.get('kind','Other')] += 1
            skills.update(o.get('skills', []))
            difficulties[q.get('difficulty','Easy')] += 1
            minutes += q.get('minutes', 0)
        days = []
        for offset in range(6,-1,-1):
            date = svc.today() - timedelta(days=offset)
            records = [a for a in done if svc.completion_day(a)==date]
            days.append(dict(date=date.isoformat(), count=len(records), points=sum(a['points'] for a in records)))
        return jsonify(progress=svc.progress(), categories=dict(categories), skills=dict(skills), difficulties=dict(difficulties), estimated_minutes=minutes, active_days=len({svc.completion_day(a) for a in done}), week=days, top_skill=skills.most_common(1)[0][0] if skills else None, top_category=categories.most_common(1)[0][0] if categories else None, method='Recorded activity; time is estimated from quest durations.')
    @app.post('/completions')
    def complete():
        data = body('quest_id')
        if not svc.profile():
            raise ValueError('Set up your profile first.')
        q = next((q for q in db.all('quests') if q['id']==data['quest_id']), None)
        if not q:
            return jsonify(error='Quest not found.'), 404
        if q['opportunity_id'] not in [a['opportunity_id'] for a in svc.activity('save')]:
            raise ValueError('Save this opportunity before completing its quest.')
        # Original quests complete once ever; daily practices once per day. The id makes retries harmless.
        completion_id = 'completion:demo:'+q['id'] + (':'+svc.today().isoformat() if q.get('daily') else '')
        created = db.put('activity', dict(id=completion_id, profile_id='demo',kind='completion',quest_id=q['id'],title=q['title'],points=q['points'],completed_at=svc.clock().isoformat()), once=True)
        return jsonify(already_completed=not created,points_earned=q['points'] if created else 0,progress=svc.progress())
