"""Serve the built UI and API from one origin for a hackathon demo."""
from pathlib import Path

from flask import Flask, send_from_directory
from werkzeug.middleware.dispatcher import DispatcherMiddleware

try:
    from .app import create_app
except ImportError:
    from app import create_app


DIST = Path(__file__).resolve().parent.parent / 'frontend' / 'dist'
web = Flask('onething-web', static_folder=str(DIST), static_url_path='')


@web.get('/')
@web.get('/<path:path>')
def index(path=''):
    requested = DIST / path
    if path and requested.is_file() and requested.resolve().is_relative_to(DIST.resolve()):
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, 'index.html')


app = DispatcherMiddleware(web, {'/api': create_app()})
