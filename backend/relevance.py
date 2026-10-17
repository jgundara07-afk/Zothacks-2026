"""Evidence-based relevance: why a card fits this person, in words taken from the source data.

The catalog's interest tags are broad (many engineering internships carry "Entrepreneurship & Startups"), so tag
overlap alone surfaces weak matches. This module looks for each chosen interest in the opportunity's own title,
organization and description, sorts cards into three honest tiers, and writes a one-line reason:

  specific - the interest itself (or a close synonym) appears in the title, organization or description
  adjacent - only a catalog tag or a related interest group links it to the person
  general  - a general task or wellbeing step, offered as a useful action rather than a match

Nothing here invents qualifications or opportunities; every reason quotes data the card already carries.
"""
import re

# Close synonyms for interests people are likely to pick. Anything not listed falls back to its own name.
SYNONYMS = {
    'Product management': ['product manager', 'product management', 'product owner', 'associate product manager', 'product strategy', 'product strategist', r'\bAPM\b'],
    'Product design': ['product design', 'product designer'],
    'Entrepreneurship & Startups': ['startup', 'start-up', 'founder', 'entrepreneur', 'venture', 'pitch', 'accelerator', 'incubator'],
    'Entrepreneurship': ['entrepreneur', 'founder', 'startup', 'start-up'],
    'Startup building': ['startup', 'start-up', 'founder', 'build a company', 'launch a product'],
    'Startup accelerators': ['accelerator', 'incubator'],
    'Venture capital': ['venture capital', r'\bVC\b', 'ventures'],
    'Pitch competitions': ['pitch'],
    'Music production': [r'\bmusic\b', 'composer', 'composing', 'music composition', 'sound design', 'audio production', 'music production', 'music producer', 'producing music', 'beat making', 'beatmaking', 'ableton', 'logic pro', r'\bDAW\b', 'mixing and mastering', 'songwriting', 'recording studio'],
    'Music composition': ['music composition', 'composer', 'composing', 'songwriting'],
    'Audio engineering': ['audio engineer', 'audio engineering', 'sound engineer', 'mixing', 'mastering', 'audio production'],
    'Sound design': ['sound design', 'sound designer'],
    'DJing': [r'\bDJ\b', 'djing'],
    'Singing': ['singing', 'vocal', 'choir'],
    'Concerts': ['concert', 'live music'],
    'Content creation': ['content creation', 'content creator', 'creator', 'youtube', 'tiktok creator', 'social content'],
    'Creative writing': ['creative writing', 'fiction', 'poetry', 'storytelling', 'writing workshop', 'writers'],
    'Copywriting': ['copywriting', 'copywriter'],
    'Screenwriting': ['screenwriting', 'screenplay'],
    'Storytelling': ['storytelling', 'story'],
    'Filmmaking': ['filmmaking', 'film', 'cinema'],
    'Videography': ['videography', 'video production'],
    'Photography': ['photography', 'photographer'],
    'Podcasting': ['podcast'],
    'Design & UI/UX': ['ux', 'ui/ux', 'user experience', 'interaction design', 'figma', 'product design'],
    'UI/UX design': ['ux', 'ui/ux', 'user experience', 'figma'],
    'Graphic design': ['graphic design', 'graphic designer'],
    'Brand strategy': ['brand strategy', 'branding'],
    'Digital marketing': ['digital marketing', 'marketing'],
    'Growth marketing': ['growth marketing', 'growth'],
    'Software Engineering': ['software engineer', 'software engineering', 'software developer', 'developer'],
    'Data Science': ['data science', 'data scientist'],
    'AI & Machine Learning': ['machine learning', r'\bAI\b', 'artificial intelligence'],
    'Web & App Development': ['web development', 'app development', 'frontend', 'front-end', 'full-stack', 'full stack'],
    'Hike': ['hike', 'hiking', 'trail'],
    'Sports': ['sport', 'athletic', 'fitness'],
}

# Same word, different meaning: "Commissioning & Startup" of a power plant is not a startup company.
EXCLUDE = {name: re.compile(r'commissioning|power plant|construction|field engineer', re.I)
           for name in ('Entrepreneurship & Startups', 'Entrepreneurship', 'Startup building')}

# Opportunity kinds that serve a goal directly, so the reason can say so.
GOAL_KINDS = {
    'Internship': ['internship'],
    'Build real-world work experience': ['internship', 'job'],
    'Launch a startup or personal product': ['campus event', 'networking event'],
    'Find mentors and build a network': ['campus event', 'networking event'],
    'Learn a new technical skill': ['online course'],
    'Earn certifications and professional credentials': ['online course'],
    'Explore careers and discover my interests': ['campus event', 'online course'],
    'Build a strong project portfolio': ['online course'],
    'Progress toward an outdoor adventure goal': ['trail', 'park'],
}

_cache = {}


def _pattern(interest):
    if interest not in _cache:
        terms = SYNONYMS.get(interest) or [interest.replace('&', 'and')]
        parts = [t if t.startswith(r'\b') else r'\b' + re.escape(t) for t in terms]
        _cache[interest] = re.compile('(' + '|'.join(parts) + ')', re.I)
    return _cache[interest]


def evidence(row, interests):
    """[(interest, where, matched text)] for each chosen interest found in the row's own text."""
    fields = (('title', row.get('title') or ''), ('organization', row.get('organization') or ''), ('description', (row.get('description') or '')[:1200]))
    hits = []
    for interest in interests or []:
        if interest in EXCLUDE and EXCLUDE[interest].search(' '.join(text for _, text in fields)):
            continue
        for where, text in fields:
            m = _pattern(interest).search(text)
            if m:
                hits.append((interest, where, m.group(0)))
                break
    return hits


def _goal_fit(row, goals):
    kind = (row.get('kind') or '').lower()
    return [g for g in goals or [] if any(k in kind for k in GOAL_KINDS.get(g, []))]


def _article(word):
    return 'an' if word[:1].lower() in 'aeiou' else 'a'


def assess(row, interests, goals, tag_overlap, nearby_groups=()):
    """Tier, score, primary interest and a plain-language reason for one card."""
    if row.get('general_task') or row.get('recommendation_type') == 'neutral':
        return dict(tier='general', score=0.0, interest=None, reason='A useful general step you can take today, not a match to your interests.')
    hits = evidence(row, interests)
    fits = _goal_fit(row, goals)
    kind = (row.get('kind') or 'opportunity').lower()
    org = (row.get('organization') or '').split(' (')[0].strip()
    at = f' at {org}' if org and len(org) < 40 else ''
    # Each matched word counts once, however many chosen interests share it ("startup" for three startup interests).
    seen, score = set(), 0.0
    for _, where, found in hits:
        if found.lower() in seen:
            continue
        seen.add(found.lower())
        score += 3 if where == 'title' else 2 if where == 'organization' else 1
    # Specific means the interest is in the title or organization; a description mention alone is only related.
    strong = any(where in ('title', 'organization') for _, where, _ in hits)
    # Real opportunities you can act on (roles, events) rank above courses at the same strength.
    score += (1.2 if any(k in kind for k in ('intern', 'job')) else 1.0 if 'event' in kind else 0) + 0.6 * len(fits) + 0.2 * len(tag_overlap)
    if hits and strong:
        interest, where, found = max(hits, key=lambda h: (h[1] == 'title', h[1] == 'organization'))
        found = found.strip()
        if where == 'title':
            lead = f'{_article(found).capitalize()} {found.lower()} {kind}{at}' if found.lower() not in kind else f'{_article(kind).capitalize()} {kind}{at}'
        else:
            lead = f'This {kind}{at} mentions {found.lower()}'
        reason = f'{lead}, matching your interest in {interest}'
        others = [h[0] for h in hits if h[0] != interest]
        if others:
            reason += f' and {others[0]}'
        if fits:
            reason += f'. It also fits your goal: {fits[0]}'
        return dict(tier='specific', score=score, interest=interest, reason=reason + '.')
    if hits:
        interest, _, found = hits[0]
        reason = f'Related: this {kind}{at} mentions {found.strip().lower()} in its description ({interest}).'
        return dict(tier='adjacent', score=score, interest=interest, reason=reason + (f' It fits your goal: {fits[0]}.' if fits else ''))
    if tag_overlap or nearby_groups:
        linked = sorted(tag_overlap)[:2] or list(nearby_groups)[:1]
        reason = f'Related, not a direct match: the source tags this {kind} with {" and ".join(linked)}.'
        return dict(tier='adjacent', score=0.5 * len(tag_overlap) + 0.4 * len(fits), interest=linked[0] if linked else None,
                    reason=reason + (f' It fits your goal: {fits[0]}.' if fits else ''))
    return dict(tier='adjacent', score=0.1, interest=None, reason=f'An exploratory {kind}; no direct link to your interests.')


def _rotate(ids, info):
    """Within a tier, take turns across interests (and kinds) so one interest can't fill the feed."""
    groups = {}
    for i in ids:
        groups.setdefault((info[i].get('interest'), info[i].get('kind_group')), []).append(i)
    order, queues = [], list(groups.values())
    while queues:
        for q in list(queues):
            order.append(q.pop(0))
            if not q:
                queues.remove(q)
    return order


def mix(ids_by_tier, info=None, pattern=('specific', 'specific', 'adjacent')):
    """Interleave tiers (two specific, then one adjacent), rotating interests within each tier."""
    queues = {tier: (_rotate(ids, info) if info else list(ids)) for tier, ids in ids_by_tier.items()}
    out = []
    while any(queues.values()):
        for tier in pattern:
            source = queues.get(tier) or next((q for q in queues.values() if q), None)
            if source:
                out.append(source.pop(0))
    return out
