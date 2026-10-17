"""API routes, grouped by feature. Each module has a register(app, svc) function that app.py calls."""
from flask import request


def body(key):
    """The request's JSON object, after checking that `key` is a string in it."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get(key), str):
        raise ValueError(f'Provide {key} as a string in a JSON object.')
    return data
