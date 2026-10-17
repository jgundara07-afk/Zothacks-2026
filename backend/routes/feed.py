from uuid import uuid4
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
        allowed = {'interests','goals','challenges','time','locations','skills','kind','commitment','step_size','q','offset','limit','lat','lon','radius_km','source','experience','cost','prerequisites','duration_quality','schedule','max_minutes'}
        if set(request.args) - allowed:
            raise ValueError('Unknown feed filter parameter')
        filters = {key:request.args.getlist(key) for key in ['interests','goals','challenges','time','locations','skills','kind','source','experience','cost','prerequisites','duration_quality','schedule']}
        filters.update({key:request.args[key] for key in ['commitment','step_size','q'] if key in request.args})
        filters.update({key:float(request.args[key]) for key in ['lat','lon','radius_km','max_minutes'] if key in request.args})
        result = svc.feed_page(filters, int(request.args.get('offset',0)), int(request.args.get('limit',40)))
        return jsonify(profile=profile(), checkin=checkin(), **result)

    @app.get('/recommendations')
    def recommendations():
        # Intentional broad search for onboarding, separate from strict feed filters.
        filters = {'step_size': request.args.get('step_size', 'Any')}
        result = svc.feed_page(filters, int(request.args.get('offset', 0)), int(request.args.get('limit', 40)), related=True)
        return jsonify(profile=profile(), checkin=checkin(), recommendation_mode=True, **result)

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
        filters = data.get('filters', {})
        if not isinstance(filters, dict) or type(filters.get('active', False)) is not bool:
            raise ValueError('Provide valid discovery filter context.')
        challenges = filters.get('challenges', [])
        if not isinstance(challenges, list) or any(not isinstance(level,str) or level not in {'Lazy','Easy','Medium','Hard','Challenging'} for level in challenges):
            raise ValueError('Provide valid discovery difficulty choices.')
        stamp = clock().isoformat()
        details = dict(saved_at=stamp, filtered=filters.get('active',False) or bool(challenges), lazy_filter=challenges == ['Lazy'])
        created = db.put('activity', dict(id='save:demo:' + data['opportunity_id'], profile_id='demo', kind='save', opportunity_id=data['opportunity_id'], **details), once=True)
        if created:
            db.put('activity', dict(id='bookmark:'+str(uuid4()),profile_id='demo',kind='bookmark_history',action='save',opportunity_id=data['opportunity_id'],recorded_at=stamp,category=svc.opportunity(data['opportunity_id']).get('kind'),**details))
        svc.achievements()
        return jsonify(saved=True, opportunity_id=data['opportunity_id'])

    @app.delete('/saved')
    def unsave():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if not svc.opportunity(data['opportunity_id']):
            return (jsonify(error='Opportunity not found.'), 404)
        if db.get('activity', 'save:demo:' + data['opportunity_id']):
            db.put('activity',dict(id='bookmark:'+str(uuid4()),profile_id='demo',kind='bookmark_history',action='unsave',opportunity_id=data['opportunity_id'],recorded_at=clock().isoformat()))
        db.delete('activity', 'save:demo:' + data['opportunity_id'])
        svc.achievements()
        return jsonify(saved=False, opportunity_id=data['opportunity_id'])
