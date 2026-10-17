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
