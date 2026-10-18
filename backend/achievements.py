from flask import g
"""Activity-backed, permanent achievement unlocks for each account."""
import re
import json
from pathlib import Path
from collections import Counter
from datetime import timedelta
try:
    from .achievement_expansion import expanded_progress
except ImportError:
    from achievement_expansion import expanded_progress

BADGES = [
    ('first-step', 'Firstlight Peak', 1, 'Complete your very first quest.', "The journey to the peak begins with a single click. You're officially on the board."),
    ('one-percent', 'Consistency Ridge', 7, 'Complete a daily micro-goal on 7 consecutive days.', "Compound interest in action. You've proven that consistency beats intensity every time."),
    ('couch-bound', 'Restful Rise', 5, 'Complete 5 Lazy quests.', "Who says you can't build a career in sweatpants? Proof that low-effort is still effort."),
    ('heavy-lifter', 'Boulder Summit', 1, 'Complete your first Locked-in quest.', "You didn't just step out of your comfort zone—you leaped. Respect the grind."),
    ('algorithm-whisperer', 'Signal Spire', 3, 'Complete 3 resume optimization or LinkedIn quests.', 'Your keywords are optimized, and your metrics are quantified. The ATS screening bots are shaking.'),
    ('touch-grass', 'Verdant Heights', 1, 'Complete a Wellness or Desk Ergonomics quest.', 'You remembered you inhabit a physical body. Your eyes, spine, and cortisol levels thank you.'),
    ('renaissance', 'Prism Range', 5, 'Complete quests in 5 different opportunity categories.', 'A master of the pivot. You are building a well-rounded toolkit.'),
    ('visionary', 'Dreamer’s Lookout', 10, 'Keep 10 saved opportunities with no completed quests in your backlog.', 'You have a grand plan. Now, you just have to actually do them.'),
    ('warm-intro', 'Kindred Peak', 3, 'Complete quests for 3 different Networking or Community opportunities.', 'You braved the awkward silences and expanded your orbit. Your future self will thank you for this network.'),
    ('base-camp', 'Base Camp Alpha', 1000, 'Accumulate 1,000 total points.', 'The air is getting thinner, but the view is getting better. Welcome to the big leagues.'),
]

EXPANSION = json.loads(Path(__file__).with_name('achievement_catalog.json').read_text(encoding='utf-8'))
METADATA = {badge['id']: badge for badge in EXPANSION}
BADGES += [(b['id'],b['name'],b['target'],b['criteria'],b['flavor']) for b in EXPANSION]


def completion_facts(quest, opportunity):
    task = opportunity.get('general_task') or {}
    category = task.get('category') or opportunity.get('kind') or 'Other'
    text = ' '.join(str(value or '') for value in (quest.get('title'), task.get('description'), opportunity.get('title')))
    tags = []
    if re.search(r'\b(?:resume|résumé|linkedin)\b|professional headline', text, re.I):
        tags.append('resume-linkedin')
    if re.search(r'wellness|desk ergonomics|wellbeing|well-being', category, re.I):
        tags.append('wellness')
    if re.search(r'networking|community|club|campus initiative', category, re.I):
        tags.append('networking')
    return dict(achievement_category=category, achievement_tags=tags, task_number=task.get('number'), daily=bool(quest.get('daily')),
                micro_goal=bool(quest.get('daily') and 0 < quest.get('minutes', 0) <= 5))


def achievements(svc):
    records = sorted(svc.activity('completion'), key=lambda row: row['completed_at'])
    counters = Counter()
    categories, micro_days, completed_opportunities, networked_opportunities = set(), set(), set(), set()
    earned = {}
    targets = {key: target for key, _, target, _, _ in BADGES}
    for row in records:
        quest = svc.quest(row['quest_id']) or {}
        opportunity_id = row.get('opportunity_id') or quest.get('opportunity_id')
        opportunity = svc.opportunity(opportunity_id) or {}
        facts = completion_facts({**quest, 'title': row.get('title') or quest.get('title')}, opportunity or {'kind': row.get('category', 'Other')})
        category = row.get('achievement_category') or facts['achievement_category']
        # Recorded categories still support legacy activities if their source disappears.
        if category == 'Other': category = row.get('category', 'Other')
        tags = row.get('achievement_tags', facts['achievement_tags'])
        if category != 'Other': categories.add(category)
        completed_opportunities.add(opportunity_id)
        counters['first-step'] += 1
        counters['couch-bound'] += row.get('difficulty', quest.get('difficulty')) == 'Lazy'
        counters['heavy-lifter'] += row.get('difficulty', quest.get('difficulty')) == 'Challenging'
        counters['algorithm-whisperer'] += 'resume-linkedin' in tags
        counters['touch-grass'] += 'wellness' in tags
        if 'networking' in tags:
            networked_opportunities.add(opportunity_id or row['quest_id'])
        counters['warm-intro'] = len(networked_opportunities)
        counters['base-camp'] += row.get('points', 0)
        counters['renaissance'] = len(categories)
        if row.get('micro_goal', facts['micro_goal']):
            day = svc.completion_day(row)
            micro_days.add(day)
            run, cursor = 0, day
            while cursor in micro_days:
                run += 1
                cursor -= timedelta(days=1)
            counters['one-percent'] = max(counters['one-percent'], run)
        for key, target in targets.items():
            if counters[key] >= target and key not in earned:
                earned[key] = row['completed_at']
    counters['visionary'] = len({row['opportunity_id'] for row in svc.activity('save')} - completed_opportunities)
    if counters['visionary'] >= 10:
        earned['visionary'] = svc.clock().isoformat()
    more_counts, more_earned = expanded_progress(svc, records, EXPANSION, completion_facts)
    counters.update(more_counts)
    earned.update(more_earned)
    saved = {row['badge_id']: row for row in svc.activity('achievement')}
    for key, timestamp in earned.items():
        if key not in saved:
            record = dict(id='achievement:' + g.user_id + ':' + key, kind='achievement', profile_id=g.user_id, badge_id=key, earned_at=timestamp)
            svc.db.put('activity', record, once=True)
            saved[key] = record
    return [dict(id=key, name=name, number=number, target=target, criteria=criteria, flavor=flavor,
                 region=METADATA.get(key,{}).get('region','foundations'),
                 tracking_hint=METADATA.get(key,{}).get('tracking_hint',''),
                 progress=min(counters[key], target), unlocked=key in saved,
                 earned_at=saved[key]['earned_at'] if key in saved else None)
            for number, (key, name, target, criteria, flavor) in enumerate(BADGES,1)]
