"""Open-ended discovery ranking: the feed never empties and gets gradually farther from your choices.

Interests, goals and your situation never exclude anything. They decide order. A card matching any one of them
ranks above cards matching none, and matching more of them ranks higher still. The Filters sheet (effort, time,
type, place, search...) narrows the first stretch of the feed. When those cards run out, the feed keeps going
with the closest cards outside your filters, so there is always something next.

Tiers, nearest first:
  close    - an interest is named in the title or organization, or the card is tagged with it and fits a goal
  match    - tagged with or mentioning one of your interests, or fits one of your goals
  related  - shares an interest group with your choices (for example another design or startup topic)
  explore  - nothing in common yet; ordered so varied, approachable picks come first
"""
try:
    from .relevance import evidence, assess
    from .filter_rules import supported_interests
    from .preferences import INTEREST_GROUPS
except ImportError:
    from relevance import evidence, assess
    from filter_rules import supported_interests
    from preferences import INTEREST_GROUPS

TIERS = ('close', 'match', 'related', 'explore')


def group_neighbours(interests):
    """Every interest that shares a picker group with one of the chosen interests."""
    chosen = set(interests)
    near = set()
    for group in INTEREST_GROUPS:
        if group.get('name') == 'Original interests':
            continue
        members = set(group.get('interests', []))
        if members & chosen:
            near |= members
    return near - chosen


def score(row, interests, goals, skills, near, mode='any'):
    """(score, tier, lead) for one catalog row. Higher is closer; lead is the choice it matches best (for variety)."""
    p = row['personalization']
    tags = set(supported_interests(p))
    hits = evidence(row, interests) if interests else []
    named = [h for h in hits if h[1] in ('title', 'organization')]
    tag_hits = tags & set(interests)
    goal_hits = set(goals) & set(row.get('career_goals', []))
    near_hits = tags & near
    value = (6 * len({h[0] for h in named}) + 1.5 * len({h[0] for h in hits if h not in named})
             + 3 * len(tag_hits) + 2.5 * len(goal_hits) + 0.8 * len(set(skills) & set(row.get('skills', [])))
             + 1.0 * min(len(near_hits), 2))
    chosen = set(interests) | set(goals)
    if mode == 'all' and chosen and chosen <= ({h[0] for h in hits} | tag_hits | goal_hits):
        value += 4
    # Things you can act on now (roles, events, places) edge out another course at the same strength.
    kind = (row.get('kind') or '').lower()
    value += 0.6 if any(k in kind for k in ('intern', 'job', 'event', 'trail', 'park', 'sports')) else 0
    if named or (tag_hits and goal_hits):
        tier = 'close'
    elif tag_hits or goal_hits:
        tier = 'match'
    elif hits or near_hits:
        # A word in the description ("trail" in "audit trail") or a neighbouring topic is only related.
        tier = 'related'
    else:
        tier = 'explore'
    lead = named[0][0] if named else next(iter(sorted(tag_hits)), None) or next(iter(sorted(goal_hits)), None) or (hits[0][0] if hits else None)
    return value, tier, lead


def reason(row, tier, interests, goals, near, outside_filters=False):
    """One honest sentence about why this card is here, built only from data the card carries."""
    if row.get('general_task'):
        return 'A useful general step you can take today.'
    if tier in ('close', 'match') and (interests or goals):
        text = assess(row, interests, goals, set(interests) & set(supported_interests(row['personalization'])))['reason']
        tagged = sorted(set(interests) & set(supported_interests(row['personalization'])))
        if text.startswith('Related, not a direct match') and tagged:
            text = f'The source tags this {(row.get("kind") or "opportunity").lower()} with {" and ".join(tagged[:2])}.'
        if text.startswith('An exploratory') or text.startswith('Related, not a direct match') and not interests:
            fits = [g for g in goals if g in row.get('career_goals', [])]
            text = f'Fits your goal: {fits[0]}.' if fits else text
    elif tier == 'related':
        shared = sorted(set(supported_interests(row['personalization'])) & near)[:2]
        text = f'Close to what you picked: tagged {" and ".join(shared)}.' if shared else 'Close to what you picked.'
    else:
        text = 'Something new to explore; it does not match your choices yet.'
    if outside_filters:
        text = 'Beyond your filters. ' + text
    return text
