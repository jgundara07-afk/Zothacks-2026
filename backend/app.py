import json
import os
import re
from collections import Counter
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / '.env')

class Store:
    def __init__(self, uri=None, path=None):
        self.mongo = None
        if uri:
            self.mongo = MongoClient(uri, serverSelectionTimeoutMS=3000)[os.getenv('MONGO_DB', 'one_thing')]
            self.mongo.command('ping')
        else:
            self.path = str(path or ROOT / 'demo.sqlite3')
            with self.connection() as con:
                con.execute('CREATE TABLE IF NOT EXISTS documents (collection TEXT, id TEXT, data TEXT, PRIMARY KEY(collection,id))')
    @contextmanager
    def connection(self):
        con = sqlite3.connect(self.path, timeout=10)
        try:
            with con:
                yield con
        finally:
            con.close()
    def all(self, collection):
        if self.mongo is not None:
            return list(self.mongo[collection].find({}, {'_id': 0}))
        with self.connection() as con:
            return [json.loads(row[0]) for row in con.execute('SELECT data FROM documents WHERE collection=?', (collection,))]
    def put(self, collection, doc, once=False):
        if self.mongo is not None:
            result = self.mongo[collection].update_one({'_id':doc['id']}, {'$setOnInsert' if once else '$set':doc}, upsert=True)
            return result.upserted_id is not None
        with self.connection() as con:
            sql = 'INSERT OR IGNORE' if once else 'INSERT OR REPLACE'
            return con.execute(f'{sql} INTO documents VALUES (?,?,?)', (collection,doc['id'],json.dumps(doc))).rowcount == 1

    def delete(self, collection, document_id):
        if self.mongo is not None:
            self.mongo[collection].delete_one({'_id': document_id})
        else:
            with self.connection() as con:
                con.execute('DELETE FROM documents WHERE collection=? AND id=?', (collection, document_id))

def create_app(store=None, now=None):
    app = Flask(__name__)
    clock = now or (lambda: datetime.now(timezone.utc))
    day_zone = ZoneInfo("America/Los_Angeles")
    def today():
        return clock().astimezone(day_zone).date()
    db = store or Store(os.getenv('MONGO_URI'))
    seed = json.loads((ROOT / 'seed.json').read_text())
    for collection, documents in seed.items():
        for doc in documents:
            db.put(collection, doc)
    def profile():
        return next(iter(db.all('profiles')), None)
    def activity(kind):
        return [a for a in db.all('activity') if a['kind'] == kind and a['profile_id'] == 'demo']
    def checkin():
        return next((a for a in activity('checkin') if a['date'] == today().isoformat()), None)
    def completion_day(a):
        return datetime.fromisoformat(a['completed_at']).astimezone(day_zone).date()
    def progress():
        done = sorted(activity('completion'), key=lambda a:a['completed_at'], reverse=True)
        dates = {completion_day(a) for a in done}
        cursor = today() if today() in dates else today() - timedelta(days=1)
        streak = 0
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        best = run = 0
        previous = None
        for date in sorted(dates):
            run = run + 1 if previous and date == previous + timedelta(days=1) else 1
            best = max(best, run)
            previous = date
        return dict(streak=streak, longest_streak=best, active_today=today() in dates, today=today().isoformat(), timezone='America/Los_Angeles', points=sum(a['points'] for a in done), completed_count=len(done), saved_count=len(activity('save')), completed_ids=[a['quest_id'] for a in done], activity=done)
    def opportunities():
        p = profile() or {}
        tags = p.get('interests', []) + p.get('skills', [])
        saved = {a['opportunity_id'] for a in activity('save')}
        result = [{**o, 'matching_tags':[t for t in o['tags'] if t in tags], 'saved':o['id'] in saved} for o in db.all('opportunities')]
        effort = (checkin() or {}).get('effort')
        if effort:
            variants = {q['opportunity_id']: q for q in db.all('quests') if q.get('effort') == effort}
            result = [{**o, 'minutes': variants[o['id']]['minutes'], 'suggested_quest_id': variants[o['id']]['id'], 'effort':effort, 'difficulty':variants[o['id']]['difficulty']} for o in result]
        return sorted(result, key=lambda o:-len(o['matching_tags']))
    def body(key):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or not isinstance(data.get(key), str):
            raise ValueError(f'Provide {key} as a string in a JSON object.')
        return data
    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400
    @app.errorhandler(PyMongoError)
    @app.errorhandler(sqlite3.Error)
    def unavailable(error):
        app.logger.error('Storage error: %s', error)
        return jsonify(error='Storage is unavailable. Please try again.'), 503
    @app.errorhandler(404)
    def missing(error):
        return jsonify(error='This route does not exist.'), 404
    @app.get('/health')
    def health():
        return jsonify(status='ok', storage='mongodb' if db.mongo is not None else 'sqlite-demo')
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
    @app.get('/opportunities')
    def feed():
        return jsonify(profile=profile(), checkin=checkin(), opportunities=opportunities())
    @app.get('/saved')
    def saved():
        return jsonify(opportunities=[o for o in opportunities() if o['saved']])
    @app.get('/quests')
    def quests():
        done = activity('completion')
        return jsonify(quests=[{**q, 'completed':any(a['quest_id']==q['id'] and (not q.get('daily') or completion_day(a)==today()) for a in done)} for q in db.all('quests')])
    @app.get('/progress')
    def totals():
        return jsonify(progress())
    @app.get('/analytics')
    def analytics():
        done = activity('completion')
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
            date = today() - timedelta(days=offset)
            records = [a for a in done if completion_day(a)==date]
            days.append(dict(date=date.isoformat(), count=len(records), points=sum(a['points'] for a in records)))
        return jsonify(progress=progress(), categories=dict(categories), skills=dict(skills), difficulties=dict(difficulties), estimated_minutes=minutes, active_days=len({completion_day(a) for a in done}), week=days, top_skill=skills.most_common(1)[0][0] if skills else None, top_category=categories.most_common(1)[0][0] if categories else None, method='Recorded activity; time is estimated from quest durations.')
    @app.post('/resume-analysis')
    def resume_analysis():
        data = body('text')
        if not data['text'].strip() or len(data['text'])>30000:
            raise ValueError('Paste between 1 and 30,000 characters of resume text.')
        roles = {'Product designer':['Design','Research','Writing'], 'Software developer':['Coding','Research','Writing'], 'Community organizer':['Writing','Research','Design']}
        role = data.get('role','Software developer')
        if not isinstance(role,str) or role not in roles:
            raise ValueError('Choose a supported target role.')
        aliases = {'Coding':['coding','python','javascript','react','programming','software','html','css','sql'], 'Design':['design','figma','wireframe','prototype','ux','ui'], 'Writing':['writing','wrote','written','copywriting','communication','documentation','editor'], 'Research':['research','analysis','analytics','survey','interview','data']}
        text = data['text'].lower()
        found = [skill for skill,words in aliases.items() if any(re.search(r'\b'+re.escape(word)+r'\b',text) for word in words)]
        gaps = [skill for skill in roles[role] if skill not in found]
        recommendations = [dict(opportunity_id=o['id'], skills=[t for t in o.get('skills',[]) if t in gaps]) for o in db.all('opportunities') if any(t in gaps for t in o.get('skills',[]))]
        return jsonify(role=role, found_skills=found, gaps=gaps, recommendations=recommendations, method='Local keyword matching against fictional role templates. Missing keywords are prompts to explore, not an assessment of your ability. Resume text is not stored.')
    @app.get('/checkins')
    def get_checkin():
        return jsonify(checkin=checkin(), date=today().isoformat(), timezone='America/Los_Angeles')
    @app.post('/checkins')
    def set_checkin():
        data = body('mood')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['mood'] not in ['Low', 'Okay', 'Good'] or data.get('effort') not in ['small', 'big']:
            raise ValueError('Choose a mood (Low, Okay, Good) and an effort (small, big).')
        entry = dict(id='checkin:demo:'+today().isoformat(), profile_id='demo', kind='checkin', date=today().isoformat(), mood=data['mood'], effort=data['effort'])
        db.put('activity', entry)
        return jsonify(checkin=entry)
    @app.post('/saved')
    def save():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return jsonify(error='Opportunity not found.'), 404
        db.put('activity', dict(id='save:demo:'+data['opportunity_id'], profile_id='demo',kind='save',opportunity_id=data['opportunity_id']), once=True)
        return jsonify(saved=True, opportunity_id=data['opportunity_id'])
    @app.delete('/saved')
    def unsave():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return jsonify(error='Opportunity not found.'), 404
        db.delete('activity', 'save:demo:' + data['opportunity_id'])
        return jsonify(saved=False, opportunity_id=data['opportunity_id'])
    @app.post('/completions')
    def complete():
        data = body('quest_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        q = next((q for q in db.all('quests') if q['id']==data['quest_id']), None)
        if not q:
            return jsonify(error='Quest not found.'), 404
        if q['opportunity_id'] not in [a['opportunity_id'] for a in activity('save')]:
            raise ValueError('Save this opportunity before completing its quest.')
        completion_id = 'completion:demo:'+q['id'] + (':'+today().isoformat() if q.get('daily') else '')
        created = db.put('activity', dict(id=completion_id, profile_id='demo',kind='completion',quest_id=q['id'],title=q['title'],points=q['points'],completed_at=clock().isoformat()), once=True)
        return jsonify(already_completed=not created,points_earned=q['points'] if created else 0,progress=progress())
    return app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', 5001)))
