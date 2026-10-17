from flask import jsonify
from routes import body

def register(app, svc):
    db = svc.db
    @app.get('/opportunities')
    def feed():
        return jsonify(profile=svc.profile(), checkin=svc.checkin(), opportunities=svc.opportunities())
    @app.get('/quests')
    def quests():
        done = svc.activity('completion')
        return jsonify(quests=[{**q, 'completed':any(a['quest_id']==q['id'] and (not q.get('daily') or svc.completion_day(a)==svc.today()) for a in done)} for q in db.all('quests')])
    @app.get('/saved')
    def saved():
        return jsonify(opportunities=[o for o in svc.opportunities() if o['saved']])
    @app.post('/saved')
    def save():
        data = body('opportunity_id')
        if not svc.profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return jsonify(error='Opportunity not found.'), 404
        db.put('activity', dict(id='save:demo:'+data['opportunity_id'], profile_id='demo',kind='save',opportunity_id=data['opportunity_id']), once=True)
        return jsonify(saved=True, opportunity_id=data['opportunity_id'])
    @app.delete('/saved')
    def unsave():
        data = body('opportunity_id')
        if not svc.profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return jsonify(error='Opportunity not found.'), 404
        db.delete('activity', 'save:demo:' + data['opportunity_id'])
        return jsonify(saved=False, opportunity_id=data['opportunity_id'])
