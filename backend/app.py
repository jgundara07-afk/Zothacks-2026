import json
import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify
from werkzeug.exceptions import RequestEntityTooLarge
from dotenv import load_dotenv
from pymongo.errors import PyMongoError
try:
    from .store import Store, ROOT
    from .services import OneThing
    from .routes import profile, feed, progress, resume
except ImportError:
    from store import Store, ROOT
    from services import OneThing
    from routes import profile, feed, progress, resume

load_dotenv(ROOT.parent / '.env')

def create_app(store=None, now=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024
    try:
        from .catalog_routes import register_catalog
    except ImportError:
        from catalog_routes import register_catalog
    register_catalog(app)
    db = store or Store(os.getenv('MONGO_URI'))
    seed = json.loads((ROOT / 'seed.json').read_text())
    for collection, documents in seed.items():
        for doc in documents:
            db.put(collection, doc)
    svc = OneThing(db, now or (lambda: datetime.now(timezone.utc)))
    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400
    @app.errorhandler(PyMongoError)
    @app.errorhandler(sqlite3.Error)
    def unavailable(error):
        app.logger.error('Storage error: %s', error)
        return jsonify(error='Storage is unavailable. Please try again.'), 503
    @app.errorhandler(RequestEntityTooLarge)
    def too_large(error):
        return jsonify(error='Upload a PDF under 5 MB.'), 413
    @app.errorhandler(404)
    def missing(error):
        return jsonify(error='This route does not exist.'), 404
    @app.get('/health')
    def health():
        return jsonify(status='ok', storage='mongodb' if db.mongo is not None else 'sqlite-demo')
    for routes in (profile, feed, progress, resume):
        routes.register(app, svc)
    return app

if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', 5001)))
