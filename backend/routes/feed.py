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
        allowed = {'interests','goals','challenges','time','locations','skills','kind','commitment','step_size','q','offset','limit','lat','lon','radius_km'}
        if set(request.args) - allowed:
            raise ValueError('Unknown feed filter parameter')
        filters = {key:request.args.getlist(key) for key in ['interests','goals','challenges','time','locations','skills','kind']}
        filters.update({key:request.args[key] for key in ['commitment','step_size','q'] if key in request.args})
        filters.update({key:float(request.args[key]) for key in ['lat','lon','radius_km'] if key in request.args})
        result = svc.feed_page(filters, int(request.args.get('offset',0)), int(request.args.get('limit',40)))
        return jsonify(profile=profile(), checkin=checkin(), **result)

    @app.get('/saved')
    def saved():
        rows = svc.saved_opportunities()
        return jsonify(opportunities=rows, quests=svc.mark_quests(svc.quests_for(rows)))

    @app.get('/quests')
    def quests():
        ids = request.args.getlist('opportunity_id')
        if len(ids) > 100: raise ValueError('Request at most 100 opportunities at once')
        rows = [svc.opportunity(i) for i in ids] if ids else svc.saved_opportunities()
        if any(o is None for o in rows): return jsonify(error='Opportunity not found.'), 404
        qs = svc.quests_for(rows) if svc.catalog is not None or ids else db.all('quests')
        return jsonify(quests=svc.mark_quests(qs))

    @app.post('/saved')
    def save():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if not svc.opportunity(data['opportunity_id']):
            return (jsonify(error='Opportunity not found.'), 404)
        db.put('activity', dict(id='save:demo:' + data['opportunity_id'], profile_id='demo', kind='save', opportunity_id=data['opportunity_id']), once=True)
        return jsonify(saved=True, opportunity_id=data['opportunity_id'])

    @app.delete('/saved')
    def unsave():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if not svc.opportunity(data['opportunity_id']):
            return (jsonify(error='Opportunity not found.'), 404)
        db.delete('activity', 'save:demo:' + data['opportunity_id'])
        return jsonify(saved=False, opportunity_id=data['opportunity_id'])
