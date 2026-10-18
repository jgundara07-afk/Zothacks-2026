import json
try:
    from .store import ROOT
except ImportError:
    from store import ROOT
PREFERENCES = json.loads((ROOT.parent / 'shared' / 'preferences.json').read_text(encoding='utf-8'))
# Niche interests removed from the picker; older saved profiles may still contain them.
RETIRED_INTERESTS = frozenset(PREFERENCES.get('retired_interests', []))

INTEREST_GROUPS = json.loads((ROOT.parent / 'shared' / 'interest_catalog.json').read_text(encoding='utf-8'))['groups']
