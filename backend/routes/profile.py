from uuid import uuid4
from flask import jsonify, request, g
from collections import Counter
from datetime import timedelta
from io import BytesIO
import re
from pypdf import PdfReader
try:
    from . import body
    from ..preferences import PREFERENCES
    from ..user_context import validate_context
except ImportError:
    from routes import body
    from preferences import PREFERENCES
    from user_context import validate_context

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

    @app.post('/profiles')
    def save_profile():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValueError('Provide profile preferences as a JSON object.')
        legacy_goals = ['Explore my interests', 'Build my skills', 'Make an impact']
        goals = data.get('goals', [])
        if isinstance(goals, list):
            goals = ['Internship' if g == 'Land a software engineering internship' else g for g in goals]
        if not isinstance(goals, list) or len(goals) > 3 or any((not isinstance(g, str) or g not in PREFERENCES['goals'] for g in goals)):
            raise ValueError('Choose up to 3 valid goals.')
        goal = data.get('goal', goals[0] if goals else legacy_goals[0])
        if goal == 'Land a software engineering internship':
            goal = 'Internship'
        if not isinstance(goal, str) or goal not in legacy_goals + PREFERENCES['goals']:
            raise ValueError('Choose a valid goal.')
        allowed = {'interests': set(PREFERENCES['interests'] + ['Design', 'Technology', 'Community', 'Sustainability', 'Arts']), 'skills': {'Writing', 'Coding', 'Research', 'Design'}}
        for key, values in allowed.items():
            if not isinstance(data.get(key), list) or (key == 'skills' and (not data[key])) or any((not isinstance(t, str) or t not in values for t in data[key])):
                raise ValueError(f'Choose valid {key} tags.')
        if len(set(data['interests'])) > PREFERENCES['max_selected_interests']:
            raise ValueError('Choose up to 10 interests.')
        preferences = data.get('preferences', {})
        if not isinstance(preferences, dict):
            raise ValueError('Provide preferences as a JSON object.')
        normalized = {}
        for key in ['challenges', 'time', 'locations']:
            value = preferences.get(key, [])
            if not isinstance(value, list) or any((not isinstance(v, str) or v not in PREFERENCES[key] for v in value)):
                raise ValueError(f'Choose valid {key} preferences.')
            normalized[key] = list(dict.fromkeys(value))
        commitment = preferences.get('commitment', 'A mix of both')
        if commitment not in PREFERENCES['commitments']:
            raise ValueError('Choose a valid commitment.')
        normalized['commitment'] = commitment
        context = validate_context(data.get('context', (profile() or {}).get('context', {})))
        p = dict(context=context, id=g.user_id, name=g.user_name, goal=goal, goals=list(dict.fromkeys(goals)), interests=list(dict.fromkeys(data['interests'])), skills=list(dict.fromkeys(data['skills'])), preferences=normalized)
        previous = profile()
        if previous and (previous.get('goals',[]) != p['goals'] or previous.get('goal') != p['goal']):
            db.put('activity',dict(id='profile-update:'+str(uuid4()),profile_id=g.user_id,kind='profile_update',recorded_at=clock().isoformat()))
        db.put('profiles', p)
        return jsonify(profile=p)

    @app.get('/checkins')
    def get_checkin():
        return jsonify(checkin=checkin(), date=today().isoformat(), timezone='America/Los_Angeles')

    @app.post('/checkins')
    def set_checkin():
        data = body('mood')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['mood'] not in ['Low', 'Okay', 'Good'] or data.get('effort') not in ['small', 'medium', 'big']:
            raise ValueError('Choose a mood (Low, Okay, Good) and a step size (small, medium, big).')
        entry = dict(id='checkin:' + g.user_id + ':' + today().isoformat(), profile_id=g.user_id, kind='checkin', date=today().isoformat(), mood=data['mood'], effort=data['effort'])
        db.put('activity', entry)
        return jsonify(checkin=entry)
