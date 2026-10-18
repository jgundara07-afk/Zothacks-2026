"""Explicit test-only identity for legacy journey fixtures. Never imported by the app."""
from flask.testing import FlaskClient
from app import create_app


def _fixture_user(token):
    if token != 'fixture-token':
        return None
    return {'id': 'demo', 'email': 'fixture@uci.edu', 'email_confirmed_at': '2026-01-01T00:00:00Z', 'user_metadata': {'name': 'Fixture'}}


class FixtureClient(FlaskClient):
    def open(self, *args, **kwargs):
        headers = dict(kwargs.pop('headers', {}) or {})
        headers.setdefault('Authorization', 'Bearer fixture-token')
        return super().open(*args, headers=headers, **kwargs)


def create_test_app(*args, **kwargs):
    kwargs['auth_verifier'] = _fixture_user
    kwargs['demo_tools'] = True
    app = create_app(*args, **kwargs)
    app.test_client_class = FixtureClient
    return app
