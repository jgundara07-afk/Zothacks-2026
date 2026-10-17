import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
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

def create_app(store=None):
    app = Flask(__name__)
    db = store or Store(os.getenv('MONGO_URI'))
    seed = json.loads((ROOT / 'seed.json').read_text())
    for collection, documents in seed.items():
        for doc in documents:
            db.put(collection, doc, once=True)
    def profile():
        return next(iter(db.all('profiles')), None)
    def activity(kind):
        return [a for a in db.all('activity') if a['kind'] == kind and a['profile_id'] == 'demo']
    def progress():
        done = sorted(activity('completion'), key=lambda a:a['completed_at'], reverse=True)
        return dict(points=sum(a['points'] for a in done), completed_count=len(done), saved_count=len(activity('save')), completed_ids=[a['quest_id'] for a in done], activity=done)
    def opportunities():
        p = profile() or {}
        tags = p.get('interests', []) + p.get('skills', [])
        saved = {a['opportunity_id'] for a in activity('save')}
        result = [{**o, 'matching_tags':[t for t in o['tags'] if t in tags], 'saved':o['id'] in saved} for o in db.all('opportunities')]
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
        return jsonify(profile=profile(), opportunities=opportunities())
    @app.get('/saved')
    def saved():
        return jsonify(opportunities=[o for o in opportunities() if o['saved']])
    @app.get('/quests')
    def quests():
        ids = progress()['completed_ids']
        return jsonify(quests=[{**q, 'completed':q['id'] in ids} for q in db.all('quests')])
    @app.get('/progress')
    def totals():
        return jsonify(progress())
    @app.post('/saved')
    def save():
        data = body('opportunity_id')
        if not profile():
            raise ValueError('Set up your profile first.')
        if data['opportunity_id'] not in [o['id'] for o in db.all('opportunities')]:
            return jsonify(error='Opportunity not found.'), 404
        db.put('activity', dict(id='save:demo:'+data['opportunity_id'], profile_id='demo',kind='save',opportunity_id=data['opportunity_id']), once=True)
        return jsonify(saved=True, opportunity_id=data['opportunity_id'])
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
        created = db.put('activity', dict(id='completion:demo:'+q['id'], profile_id='demo',kind='completion',quest_id=q['id'],title=q['title'],points=q['points'],completed_at=datetime.now(timezone.utc).isoformat()), once=True)
        return jsonify(already_completed=not created,points_earned=q['points'] if created else 0,progress=progress())
    return app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', 5001)))
