"""Small, deterministic diversity preference; relevance always takes priority."""
import math
import re
from collections import Counter


def normalized(value):
    return re.sub(r'\W+', ' ', str(value or '').casefold()).strip()


def rank_records(rows, relevance):
    """Reward less repeated titles/providers/types by at most 0.25 points.

    Scores are computed over the full eligible set before pagination. There is
    no randomness or offset-dependent reranking, so subsequent pages stay stable.
    This is catalog rarity, not a claim that a listing is exclusive or better.
    """
    titles = Counter(normalized(row.get('title')) for row in rows)
    providers = Counter(normalized(row.get('organization') or row.get('source')) for row in rows)
    kinds = Counter(row['kind'] for row in rows)
    scored = []
    for row in rows:
        base = relevance(row)
        bonus = (0.10 / titles[normalized(row.get('title'))]
                 + 0.08 / math.sqrt(providers[normalized(row.get('organization') or row.get('source'))])
                 + 0.07 / math.sqrt(kinds[row['kind']]))
        scored.append((row, base, bonus))
    return sorted(scored, key=lambda entry: -(entry[1] + entry[2]))


def match_details(row, interests=(), goals=(), skills=(), query=''):
    """Explain relevance using explicit catalog tags and title evidence only."""
    try:
        from .filter_rules import supported_interests, search_terms, searchable, term_matches
    except ImportError:
        from filter_rules import supported_interests, search_terms, searchable, term_matches
    p = row['personalization']
    matched = dict(interests=sorted(set(interests).intersection(supported_interests(p))),
                   goals=sorted(set(goals).intersection(row.get('career_goals', p.get('goals', [])))),
                   skills=sorted(set(skills).intersection(row.get('skills', []))))
    title = searchable(row.get('title', ''))
    terms = search_terms(query)
    title_hits = sum(term_matches(term, title) for term in terms)
    # Interest and goal evidence outranks generic transferable skill tags.
    score = len(matched['interests'])*4 + len(matched['goals'])*3 + len(matched['skills'])
    score += title_hits*6 + (4 if terms and searchable(query) in title else 0)
    return dict(**matched, title_terms=[term for term in terms if term_matches(term, title)], score=score)
