"""Production entry point: serves the built frontend and mounts the API under /api.

Local development keeps using `python app.py` with Vite's /api proxy.
Run with: gunicorn --chdir backend wsgi:app
"""
from pathlib import Path
from flask import Flask, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware
try:
    from .app import create_app
except ImportError:
    from app import create_app

DIST = Path(__file__).resolve().parent.parent / 'frontend' / 'dist'

site = Flask(__name__, static_folder=None)

@site.get('/', defaults={'path': ''})
@site.get('/<path:path>')
def frontend(path):
    if path and (DIST / path).is_file():
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, 'index.html')

# Same rewrite as the Vite dev proxy: /api/opportunities -> /opportunities.
app = DispatcherMiddleware(site, {'/api': create_app()})
