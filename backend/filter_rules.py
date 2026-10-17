"""Shared strict predicates for both collected-catalog search APIs."""
import json
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

OPTIONS = json.loads((Path(__file__).resolve().parents[1] / "shared" / "catalog_filters.json").read_text(encoding="utf-8"))
EXTRA_FILTERS = {
    "experience": ("experience_level", "experience_levels"),
    "cost": ("cost", "costs"),
    "prerequisites": ("prerequisite_status", "prerequisite_statuses"),
    "duration_quality": ("duration_quality", "duration_qualities"),
    "schedule": ("schedule_type", "schedules"),
}


def supported_interests(personalization):
    if "filter_interests" in personalization:
        return personalization["filter_interests"]
    return [] if personalization.get("classification", {}).get("fallback") else personalization["interests"]


def validate_extra(filters):
    for key, (_, option) in EXTRA_FILTERS.items():
        if any(value not in OPTIONS[option] for value in filters.get(key, [])):
            raise ValueError("Unknown " + key + " filter")
    max_minutes = filters.get("max_minutes")
    if max_minutes is not None and (not math.isfinite(max_minutes) or max_minutes <= 0):
        raise ValueError("max_minutes must be finite and greater than zero")


def matches_extra(row, filters, scope="opportunity"):
    p = row["personalization"]
    assessment = p.get("assessment", {})
    for key, (field, _) in EXTRA_FILTERS.items():
        if filters.get(key) and assessment.get(field, "Unknown") not in filters[key]:
            return False
    if filters.get("max_minutes") is not None:
        maximum = p.get("duration", {}).get("max_minutes") if scope == "opportunity" else p[scope]["minutes"]
        if maximum is None or maximum > filters["max_minutes"]:
            return False
    return True


@lru_cache(maxsize=65536)
def searchable(value):
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').casefold()) if not unicodedata.combining(c))
    for pattern, replacement in [(r'front[ -]?end', 'frontend'), (r'back[ -]?end', 'backend'), (r'full[ -]?stack', 'fullstack'), (r'open[ -]?source', 'opensource')]:
        text = re.sub(pattern, replacement, text)
    return re.sub(r'[^\w+#]+', ' ', text).strip()


@lru_cache(maxsize=1024)
def search_terms(query):
    return list(dict.fromkeys(searchable(query).split()))


def matches_search(row, query):
    terms = search_terms(query)
    if not terms: return True
    text = searchable(' '.join(str(row.get(key) or '') for key in ['title','description','organization','location']))
    return all(term_matches(term, text) for term in terms)


def matches_locations(selected, resolved):
    return not selected or bool(set(selected).intersection(resolved))


def term_matches(term, text):
    # Short searches like AI must not match incidental letters inside 'trail'.
    return any(word == term if len(term) <= 2 else word.startswith(term) for word in text.split())


def matches_choices(selected, values, mode='any'):
    if mode not in {'any', 'all'}:
        raise ValueError('match_mode must be any or all')
    return not selected or (set(selected).issubset(values) if mode == 'all' else bool(set(selected).intersection(values)))
