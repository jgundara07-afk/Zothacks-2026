from flask import jsonify
try:
    from . import body
except ImportError:
    from routes import body

def register(app, svc):
    db = svc.db
    @app.post('/profiles')
    def save_profile():
        data = body('goal')
        if data['goal'] not in ['Explore my interests', 'Build my skills', 'Make an impact']:
            raise ValueError('Choose a valid goal.')
        allowed = {'interests':{'Design','Technology','Community','Sustainability','Arts'}, 'skills':{'Writing','Coding','Research','Design'}}
        for key, values in allowed.items():
            if not isinstance(data.get(key), list) or not data[key] or any(not isinstance(t,str) or t not in values for t in data[key]):
                raise ValueError(f'Choose at least one valid {key} tag.')
        p = dict(id='demo', name='Alex', goal=data['goal'], interests=list(dict.fromkeys(data['interests'])), skills=list(dict.fromkeys(data['skills'])))
        db.put('profiles', p)
        return jsonify(profile=p)
    @app.get('/checkins')
    def get_checkin():
        return jsonify(checkin=svc.checkin(), date=svc.today().isoformat(), timezone='America/Los_Angeles')
    @app.post('/checkins')
    def set_checkin():
        data = body('mood')
        if not svc.profile():
            raise ValueError('Set up your profile first.')
        if data['mood'] not in ['Low', 'Okay', 'Good'] or data.get('effort') not in ['small', 'big']:
            raise ValueError('Choose a mood (Low, Okay, Good) and an effort (small, big).')
        today = svc.today().isoformat()
        entry = dict(id='checkin:demo:'+today, profile_id='demo', kind='checkin', date=today, mood=data['mood'], effort=data['effort'])
        db.put('activity', entry)
        return jsonify(checkin=entry)
