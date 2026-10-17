from flask import jsonify, request
from collections import Counter
from datetime import timedelta
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

    @app.get('/opportunities')
    def feed():
        return jsonify(profile=profile(), checkin=checkin(), opportunities=opportunities())

    @app.get('/saved')
    def saved():
        return jsonify(opportunities=[o for o in opportunities() if o['saved']])

    @app.get('/quests')
    def quests():
        done = activity('completion')
        return jsonify(quests=[{**q, 'completed': any((a['quest_id'] == q['id'] and (not q.get('daily') or completion_day(a) == today()) for a in done))} for q in db.all('quests')])

    @app.post('/saved')
    def save():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return (jsonify(error='Opportunity not found.'), 404)
        db.put('activity', dict(id='save:demo:' + data['opportunity_id'], profile_id='demo', kind='save', opportunity_id=data['opportunity_id']), once=True)
        return jsonify(saved=True, opportunity_id=data['opportunity_id'])

    @app.delete('/saved')
    def unsave():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return (jsonify(error='Opportunity not found.'), 404)
        db.delete('activity', 'save:demo:' + data['opportunity_id'])
        return jsonify(saved=False, opportunity_id=data['opportunity_id'])
