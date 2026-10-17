import json
try:
    from .store import ROOT
except ImportError:
    from store import ROOT
PREFERENCES = json.loads((ROOT.parent / 'shared' / 'preferences.json').read_text(encoding='utf-8'))
