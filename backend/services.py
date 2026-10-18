from collections import Counter, defaultdict, deque
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
try:
    from .achievements import achievements
    from .program_catalog import program_catalog, preparation_quests, available, distance_km
    from .preferences import PREFERENCES, INTEREST_GROUPS, RETIRED_INTERESTS
    from .filter_rules import supported_interests, validate_extra, matches_extra, matches_search, matches_locations, matches_choices
    from .user_context import context_match, context_relevance, first_step_limit
    from .ranking import rank_records, match_details
    from .neutral import is_neutral, fallback_info, sprinkle
    from .discovery import score, reason, group_neighbours, TIERS
    from .gemini_recommendation import generate_recommendation
except ImportError:
    from achievements import achievements
    from program_catalog import program_catalog, preparation_quests, available, distance_km
    from preferences import PREFERENCES, INTEREST_GROUPS, RETIRED_INTERESTS
    from filter_rules import supported_interests, validate_extra, matches_extra, matches_search, matches_locations, matches_choices
    from user_context import context_match, context_relevance, first_step_limit
    from ranking import rank_records, match_details
    from neutral import is_neutral, fallback_info, sprinkle
    from discovery import score, reason, group_neighbours, TIERS
    from gemini_recommendation import generate_recommendation

DAY_ZONE = ZoneInfo("America/Los_Angeles")

class OneThing:
    """Reads and personalization for the persistent demo profile."""
    def __init__(self, db, clock, data_mode='sample'):
        self.db = db
        self.real_clock = clock
        self.clock = self.demo_now
        self.data_mode = data_mode
        self.catalog = program_catalog() if data_mode == 'catalog' else None
    def demo_state(self):
        saved = (self.db.get('activity', 'demo-clock') or {}) if getattr(self, 'demo_enabled', True) else {}
        real = self.real_clock().astimezone(DAY_ZONE)
        return dict(enabled=getattr(self, 'demo_enabled', True), today=saved.get('date') or real.date().isoformat(), real_today=real.date().isoformat(), simulated=bool(saved.get('date')), timezone='America/Los_Angeles')
    def demo_now(self):
        real = self.real_clock().astimezone(DAY_ZONE)
        state = self.demo_state()
        if not state['enabled'] or not state['simulated']:
            return real
        target = datetime.fromisoformat(state['today'])
        return target.replace(hour=real.hour, minute=real.minute, second=real.second, tzinfo=DAY_ZONE)
    def opportunity_rows(self):
        return list(self.catalog.values()) if self.catalog is not None else self.db.all('opportunities')
    def opportunity(self, opportunity_id):
        if self.catalog is not None and opportunity_id in self.catalog:
            return self.catalog[opportunity_id]
        # Old sample saves and completed quests remain readable after switching modes.
        return self.db.get('opportunities', opportunity_id)
    def quest(self, quest_id):
        if self.catalog is not None and '::' in quest_id:
            o = self.catalog.get(quest_id.rsplit('::', 1)[0])
            return next((q for q in preparation_quests(o) if q['id'] == quest_id), None) if o else None
        return self.db.get('quests', quest_id)
    def quests_for(self, rows):
        if self.catalog is None:
            ids = {o['id'] for o in rows}
            return [q for q in self.db.all('quests') if q['opportunity_id'] in ids]
        result = []
        for o in rows:
            if o['id'] in self.catalog:
                result.extend(preparation_quests(o))
            else:
                result.extend(q for q in self.db.all('quests') if q['opportunity_id'] == o['id'])
        return result
    def decorate(self, rows):
        p = self.profile() or {}
        tags = p.get('interests', []) + p.get('skills', [])
        saved = {a['opportunity_id'] for a in self.activity('save')}
        return [{**o, 'matching_tags': list(dict.fromkeys(t for t in o.get('topics', []) + o.get('tags', []) + o.get('skills', []) if t in tags)), 'saved': o['id'] in saved} for o in rows]
    def saved_opportunities(self):
        rows = [self.opportunity(a['opportunity_id']) for a in self.activity('save')]
        return self.decorate([o for o in rows if o])
    def mark_quests(self, quests):
        done = self.activity('completion')
        current_day = self.today()
        all_done = {a['quest_id'] for a in done}
        daily_done = {a['quest_id'] for a in done if self.completion_day(a) == current_day}
        return [{**q, 'completed': q['id'] in (daily_done if q.get('daily') else all_done)} for q in quests]
    def feed_page(self, filters, offset, limit, related=False):
        """Match any choice within each group; rank relevance before a small diversity boost."""
        for field in ('interests', 'goals'):
            maximum = PREFERENCES['max_selected_interests'] if field == 'interests' else PREFERENCES['max_selected_goals']
            if len(set(filters.get(field, []))) > maximum:
                raise ValueError('Choose up to '+str(maximum)+' '+field)
        match_mode = filters.get('match_mode', 'any')
        matches_choices([], [], match_mode)
        sort = filters.get('sort', 'relevance')
        if sort not in {'relevance','shortest','points'}:
            raise ValueError('sort must be relevance, shortest, or points')
        for flag in ('hide_saved', 'hide_completed'):
            if filters.get(flag, 'false') not in {'true','false'}:
                raise ValueError(flag+' must be true or false')
        if self.catalog is None:
            rows = self.opportunities()
            return dict(opportunities=rows, quests=self.mark_quests(self.db.all('quests')), total=len(rows), offset=0, limit=len(rows), has_more=False, data_mode='sample')
        import math
        validate_extra(filters)
        for field in ('kind', 'skills', 'source'):
            known = {value for row in self.catalog.values() for value in (row.get('skills', []) if field == 'skills' else [row[field]])}
            if any(value not in known for value in filters.get(field, [])):
                raise ValueError('Unknown '+field+' filter')
        if len(filters.get('q', '')) > 300:
            raise ValueError('Search text must be at most 300 characters')
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError('offset must be nonnegative and limit must be 1â€“100')
        for field, option in [('interests','interests'),('goals','goals'),('challenges','challenges'),('time','time'),('locations','locations')]:
            if any(v not in PREFERENCES[option] for v in filters.get(field, [])):
                raise ValueError('Unknown '+field+' filter')
        if filters.get('commitment', 'A mix of both') not in PREFERENCES['commitments']:
            raise ValueError('Unknown commitment filter')
        if filters.get('step_size', 'Any') not in {'Any','Small','Medium','Big'}:
            raise ValueError('Unknown step size')
        lat,lon = filters.get('lat'),filters.get('lon')
        radius = filters.get('radius_km', 25)
        if (lat is None) != (lon is None) or (lat is not None and (not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180)) or not math.isfinite(radius) or not 0 < radius <= 500:
            raise ValueError('Provide valid latitude, longitude and radius (0â€“500 km)')
        if 'Near me' in filters.get('locations', []) and lat is None:
            raise ValueError('Near me requires your location. Allow location access or choose another location filter.')
        profile = self.profile() or {}
        context = profile.get('context', {})
        step_limit = first_step_limit(context)
        interest_tags = [i for i in (filters.get('interests') or profile.get('interests', [])) if i not in RETIRED_INTERESTS]
        skill_tags = list(filters.get('skills') or profile.get('skills', []))
        goal_tags = list(filters.get('goals') or profile.get('goals', []))
        near = group_neighbours(interest_tags)
        default_effort = (self.checkin() or {}).get('effort')
        saved_ids = {a['opportunity_id'] for a in self.activity('save')} if filters.get('hide_saved') == 'true' else set()
        # Completed work never returns to the feed: a single quest hides its opportunity, and a project
        # (ordered helper quests) stays only until every step is done, showing its next unfinished step.
        done_quests = {a['quest_id'] for a in self.activity('completion')}

        import json as _json
        cache_key = _json.dumps(['demo', {k: v for k, v in filters.items() if k not in ('offset', 'limit')}, interest_tags, goal_tags, skill_tags,
                                 context, sorted(done_quests), sorted(saved_ids), default_effort, str(self.today()), lat, lon, radius], sort_keys=True, default=str)
        cached = getattr(self, '_stream_cache', {}).get(cache_key)
        if cached is None:
            stream, matched_count = self._build_stream(filters, interest_tags, goal_tags, skill_tags, near, context, step_limit, default_effort, saved_ids, done_quests, lat, lon, radius, match_mode, sort)
            self._stream_cache = {**getattr(self, '_stream_cache', {}), cache_key: (stream, matched_count)}
            if len(self._stream_cache) > 24:
                self._stream_cache = dict(list(self._stream_cache.items())[-24:])
        else:
            stream, matched_count = cached
        page = stream[offset:offset+limit]
        cards = self.decorate([{**o, 'recommendation_type': 'neutral' if o.get('general_task') else 'matched',
                                'placement': 'sprinkled' if o.get('general_task') else 'beyond_filters' if beyond else 'matched',
                                'match_tier': 'general' if o.get('general_task') else tier, 'beyond_filters': beyond,
                                'match_reason': reason(o, tier, interest_tags, goal_tags, near, beyond),
                                'ranking': dict(relevance_score=round(value, 3)),
                                'venues': venues, 'minutes': q['minutes'], 'suggested_quest_id': q['id'], 'preparation_difficulty': q['difficulty'],
                                'size': q['size'], 'effort': q['effort']} for (o, q, venues), tier, value, beyond in page])
        for card in cards:
            card['context_reasons'] = context_relevance(card, context)[1]
            card['first_step_limit'] = step_limit
            card['match_details'] = match_details(card, interest_tags, goal_tags, skill_tags, filters.get('q', '')) if card['recommendation_type'] != 'neutral' else dict(interests=[], goals=[], skills=[], title_terms=[], score=0)
            card['matching_tags'] = [] if card['recommendation_type'] == 'neutral' else list(dict.fromkeys(card['match_details']['interests'] + card['match_details']['goals'] + card['match_details']['skills']))
        # Nothing truly close inside your filters: the feed still scrolls (nearest first), and on the first page a
        # self-guided Gemini idea based on your choices may join it.
        no_close = bool(interest_tags or goal_tags) and not any(item[1] in ('close', 'match') and not item[3] for item in stream)
        fallback = fallback_info(no_close, filters)
        if no_close:
            fallback['message'] = 'Nothing matches every choice exactly yet, so here are the closest options, getting farther as you scroll.'
            if offset == 0 and not related:
                choices = {key: value for key, value in filters.items() if key not in {'lat', 'lon', 'radius_km'} and value not in (None, '', [], {})}
                recommendation = generate_recommendation(choices)
                if recommendation:
                    fallback.update(reason='gemini_personalized_suggestion', recommendation=recommendation)
        if related:
            for card in cards:
                exact = set(interest_tags).intersection(supported_interests(card['personalization']))
                nearby = [g['name'] for g in INTEREST_GROUPS if g['name'] != 'Original interests' and set(g['interests']).intersection(interest_tags) and set(g['interests']).intersection(supported_interests(card['personalization']))]
                card['recommendation_reason'] = ('Matches '+', '.join(sorted(exact))) if exact else ('Related to your '+', '.join(nearby)+' interests') if nearby else 'An exploratory option; no direct interest match.'
        return dict(opportunities=cards, quests=self.mark_quests(self.quests_for(cards)), total=len(stream), offset=offset, limit=limit,
                    has_more=offset+limit < len(stream), data_mode='catalog', context_applied=bool(any(context.values())),
                    context_notes=(['Budget amount data is incomplete; showing confirmed free options only.'] if context.get('budget') in {'Under $25','Under $100'} else []) + (['Preferred event days use Pacific time when a scheduled date is known.'] if context.get('days') in {'Weekdays','Weekends'} else []),
                    matched_count=matched_count, fallback=fallback, kinds=sorted({o['kind'] for o in self.catalog.values()}))
    def _build_stream(self, filters, interest_tags, goal_tags, skill_tags, near, context, step_limit, default_effort, saved_ids, done_quests, lat, lon, radius, match_mode, sort):
        """Every eligible card in feed order: in-filter tiers, general tasks sprinkled, then the closest cards beyond the filters."""
        def within_filters(o, p, venues):
            """The Filters sheet narrows the first stretch of the feed; interests, goals and situation never exclude."""
            if filters.get('challenges') and not set(filters['challenges']).intersection(p['challenge_levels']): return False
            if filters.get('time') and not set(filters['time']).intersection(p['time_buckets']): return False
            if filters.get('skills') and not set(filters['skills']).intersection(o['skills']): return False
            if not matches_extra(o, filters): return False
            if filters.get('kind') and o['kind'] not in filters['kind']: return False
            if filters.get('source') and o['source'] not in filters['source']: return False
            if not matches_search(o, filters.get('q', '')): return False
            if not matches_locations(filters.get('locations', []), venues): return False
            commitment = filters.get('commitment', 'A mix of both')
            return commitment == 'A mix of both' or commitment == o['commitment']

        inside, outside, general = [], [], []
        for o in self.catalog.values():
            if o['id'] in saved_ids: continue
            if not available(o, self.real_clock()): continue
            p = o['personalization']
            venues = list(o['venues'])
            if lat is not None and o.get('coordinates') and distance_km(lat,lon,o['coordinates']) <= radius: venues.append('Near me')
            quests = preparation_quests(o)
            if any(q['id'] in done_quests for q in quests) and not any(q.get('project') for q in quests): continue
            if quests[0].get('project'):
                quests = [next((q for q in quests if q['id'] not in done_quests), None)] if quests else []
                if quests == [None]: continue
            # an explicit step size narrows the first stretch; your availability only prefers steps that fit it
            sized = [q for q in quests if filters.get('step_size','Any') == 'Any' or q['size'] == filters['step_size']]
            fitting = [q for q in sized if step_limit is None or q['minutes'] <= step_limit]
            candidates = fitting or sized or quests
            # With no effort set, use the opportunity's suggested first step (a mix of sizes, see program_catalog).
            chosen = next((q for q in candidates if q.get('suggested')), None) if not default_effort and filters.get('step_size','Any') == 'Any' else None
            chosen = chosen or min(candidates, key=lambda q: ((q['effort'] != default_effort) if default_effort else (q['difficulty'] not in p['challenge_levels']), q['minutes']))
            entry = (o, chosen, venues)
            if o.get('general_task'):
                if within_filters(o, p, venues): general.append(entry)
                continue
            value, tier, lead = score(o, interest_tags, goal_tags, skill_tags, near, match_mode)
            # Your situation (budget, format, travel, days, availability) is a preference, never a gate: cards that
            # fit it move up, the rest still appear.
            value += context_relevance(o, context)[0] + (1.0 if context_match(o, context, filters) else 0) + (0.4 if fitting else 0)
            (inside if sized and within_filters(o, p, venues) else outside).append((entry, value, tier, lead))

        interest_set = set(interest_tags)
        def order(pool):
            """Your choices take turns: each matched interest or goal contributes its nearest cards in rotation
            (tier, then score, with roles/events/outings/courses alternating). Related picks follow, then the rest.
            Repeated titles (the same trail mapped in several segments) collapse to one card."""
            by_id = {e[0][0]['id']: e for e in pool}
            ranked = rank_records([e[0][0] for e in pool], lambda o: by_id[o['id']][1])
            rank = {t: i for i, t in enumerate(TIERS)}
            items = sorted(((by_id[o['id']], base, bonus) for o, base, bonus in ranked), key=lambda it: rank[it[0][2]])
            seen, unique = set(), []
            for it in items:
                title = ' '.join((it[0][0][0].get('title') or '').lower().split())
                if title in seen: continue
                seen.add(title); unique.append(it)
            def kind_group(it):
                k = (it[0][0][0].get('kind') or '').lower()
                return 'role' if ('intern' in k or 'job' in k) else 'event' if 'event' in k else 'outing' if any(w in k for w in ('trail','park','sports')) else 'course'
            def round_robin(groups):
                queues, out = [q for q in groups if q], []
                while queues:
                    for q in list(queues):
                        out.append(q.pop(0))
                        if not q: queues.remove(q)
                return out
            def by(items, key):
                groups = {}
                for it in items: groups.setdefault(key(it), []).append(it)
                return list(groups.values())
            # every chosen interest or goal gets a queue; one with only description mentions still takes turns
            matched = [it for it in unique if it[0][3] is not None and it[0][2] in ('close', 'match', 'related')]
            queues = []
            for group in by(matched, lambda it: it[0][3]):
                # nearest tier first inside each choice; types alternate within a tier
                q = [x for t in ('close', 'match', 'related') for x in round_robin(by([it for it in group if it[0][2] == t], kind_group))]
                # interests get two turns for each goal-only turn
                queues.append((q, 2 if group[0][0][3] in interest_set else 1))
            out = []
            while any(q for q, _ in queues):
                for q, turns in queues:
                    for _ in range(turns):
                        if q: out.append(q.pop(0))
            rest = [round_robin(by([it for it in unique if it[0][2] == t and it[0][3] is None], kind_group)) for t in ('related', 'explore')]
            return out + rest[0] + rest[1]

        ordered_inside, ordered_outside = order(inside), order(outside)
        task_ranked = sorted(general, key=lambda e: (bool(e[0]['general_task'].get('requirements')), e[0]['general_task']['minutes'], e[0]['general_task']['number']))
        stream = [(item[0][0], item[0][2], item[1], False) for item in ordered_inside]
        tasks = [(t, 'explore', 0, False) for t in task_ranked]
        stream = sprinkle(stream, tasks) if stream else tasks
        if sort != 'relevance':
            # an explicit sort orders everything inside the filters, sprinkled tasks included
            stream.sort(key=lambda item: (item[0][1]['minutes'] if sort == 'shortest' else -item[0][1]['points'], -item[2]))
        stream += [(item[0][0], item[0][2], item[1], True) for item in ordered_outside]
        return stream, len(ordered_inside)
    def today(self):
        return self.clock().astimezone(DAY_ZONE).date()
    def profile(self):
        p = self.db.get('profiles', 'demo')
        if p:
            p['goals'] = ['Internship' if g == 'Land a software engineering internship' else g for g in p.get('goals', [])]
            p['interests'] = [i for i in p.get('interests', []) if i not in RETIRED_INTERESTS]
            if p.get('goal') == 'Land a software engineering internship':
                p['goal'] = 'Internship'
        return p
    def activity(self, kind):
        return [a for a in self.db.all('activity') if a['kind'] == kind and a['profile_id'] == 'demo']
    def checkin(self):
        return next((a for a in self.activity('checkin') if a['date'] == self.today().isoformat()), None)
    def completion_day(self, a):
        return datetime.fromisoformat(a['completed_at']).astimezone(DAY_ZONE).date()
    def achievements(self):
        return achievements(self)
    def progress(self):
        done = sorted(self.activity('completion'), key=lambda a: a['completed_at'], reverse=True)
        dates = {self.completion_day(a) for a in done}
        cursor = self.today() if self.today() in dates else self.today() - timedelta(days=1)
        streak = 0
        while cursor in dates:
            streak += 1
            cursor -= timedelta(days=1)
        best = run = 0
        previous = None
        for date in sorted(dates):
            run = run + 1 if previous and date == previous + timedelta(days=1) else 1
            best = max(best, run)
            previous = date
        return dict(achievements=self.achievements(), demo_clock=self.demo_state(), streak=streak, longest_streak=best, active_today=self.today() in dates, today=self.today().isoformat(), timezone='America/Los_Angeles', points=sum((a['points'] for a in done)), completed_count=len(done), saved_count=len(self.activity('save')), completed_ids=[a['quest_id'] for a in done], activity=done)
    def opportunities(self):
        if self.catalog is not None:
            return self.decorate([o for o in self.catalog.values() if available(o,self.real_clock())])
        p = self.profile() or {}
        tags = p.get('interests', []) + p.get('skills', [])
        saved = {a['opportunity_id'] for a in self.activity('save')}
        result = [{**o, 'matching_tags': list(dict.fromkeys((t for t in o.get('topics', []) + o['tags'] if t in tags))), 'saved': o['id'] in saved} for o in self.db.all('opportunities')]
        effort = (self.checkin() or {}).get('effort')
        if effort:
            variants = {q['opportunity_id']: q for q in self.db.all('quests') if q.get('effort') == effort and q.get('difficulty') != 'Challenging'}
            result = [{**o, 'minutes': variants[o['id']]['minutes'], 'suggested_quest_id': variants[o['id']]['id'], 'effort': effort, 'difficulty': variants[o['id']]['difficulty'], 'size': variants[o['id']]['size']} for o in result]
        scores = defaultdict(lambda: defaultdict(deque))
        for o in result:
            scores[len(o['matching_tags'])][o['kind']].append(o)
        mixed = []
        for score in sorted(scores, reverse=True):
            groups = scores[score]
            while any(groups.values()):
                for group in groups.values():
                    if group:
                        mixed.append(group.popleft())
        return mixed
