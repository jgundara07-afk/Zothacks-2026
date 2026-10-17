from collections import Counter, defaultdict, deque
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
try:
    from .program_catalog import program_catalog, preparation_quests, available, distance_km
    from .preferences import PREFERENCES, INTEREST_GROUPS
    from .filter_rules import supported_interests, validate_extra, matches_extra
    from .ranking import rank_records
    from .neutral import is_neutral, fallback_info
except ImportError:
    from program_catalog import program_catalog, preparation_quests, available, distance_km
    from preferences import PREFERENCES, INTEREST_GROUPS
    from filter_rules import supported_interests, validate_extra, matches_extra
    from ranking import rank_records
    from neutral import is_neutral, fallback_info

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
        return [{**q, 'completed': any(a['quest_id'] == q['id'] and (not q.get('daily') or self.completion_day(a) == self.today()) for a in done)} for q in quests]
    def feed_page(self, filters, offset, limit, related=False):
        """Match any choice within each group; rank relevance before a small diversity boost."""
        for field in ('interests', 'goals'):
            maximum = PREFERENCES['max_selected_interests'] if field == 'interests' else PREFERENCES['max_selected_goals']
            if len(set(filters.get(field, []))) > maximum:
                raise ValueError('Choose up to '+str(maximum)+' '+field)
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
            raise ValueError('offset must be nonnegative and limit must be 1–100')
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
            raise ValueError('Provide valid latitude, longitude and radius (0–500 km)')
        if 'Near me' in filters.get('locations', []) and lat is None:
            raise ValueError('Near me requires your location. Allow location access or choose another location filter.')
        matches = {}
        neutral = {}
        profile = self.profile() or {}
        interest_tags = set(filters.get('interests') or profile.get('interests', []))
        skill_tags = set(filters.get('skills') or profile.get('skills', []))
        goal_tags = set(filters.get('goals') or profile.get('goals', []))
        default_effort = (self.checkin() or {}).get('effort', 'small')
        for o in self.catalog.values():
            if not available(o, self.real_clock()): continue
            p = o['personalization']
            if filters.get('challenges') and not set(filters['challenges']).intersection(p['challenge_levels']): continue
            if filters.get('time') and not set(filters['time']).intersection(p['time_buckets']): continue
            if filters.get('skills') and not set(filters['skills']).intersection(o['skills']): continue
            if not matches_extra(o, filters): continue
            if filters.get('kind') and o['kind'] not in filters['kind']: continue
            if filters.get('source') and o['source'] not in filters['source']: continue
            if filters.get('q') and not all(t in ' '.join(str(o.get(k) or '') for k in ['title','description','organization','location']).casefold() for t in filters['q'].casefold().split()): continue
            venues = list(o['venues'])
            if lat is not None and o.get('coordinates') and distance_km(lat,lon,o['coordinates']) <= radius: venues.append('Near me')
            if 'Near me' in filters.get('locations', []) and 'Near me' not in venues: continue
            other_locations = set(filters.get('locations', [])) - {'Near me'}
            if other_locations and not other_locations.intersection(venues): continue
            commitment = filters.get('commitment', 'A mix of both')
            if commitment != 'A mix of both' and commitment != o['commitment']: continue
            candidates = [q for q in preparation_quests(o)
                if filters.get('step_size','Any') == 'Any' or q['size'] == filters['step_size']]
            if not candidates: continue
            chosen = min(candidates, key=lambda q:(q['effort'] != default_effort,q['minutes']))
            if is_neutral(o): neutral[o['id']] = (o,chosen,venues)
            if filters.get('interests') and not set(filters['interests']).intersection(supported_interests(p)): continue
            if filters.get('goals') and not set(filters['goals']).intersection(o['career_goals']): continue
            matches[o['id']] = (o,chosen,venues)
        using_fallback = bool(not matches and neutral and (filters.get('interests') or filters.get('goals')))
        if using_fallback: matches = neutral
        def relevance(o):
            if using_fallback: return 0
            return (len(interest_tags.intersection(supported_interests(o['personalization'])))
                    + len(skill_tags.intersection(o['skills']))
                    + len(goal_tags.intersection(o['career_goals'])))
        ranked = rank_records([entry[0] for entry in matches.values()], relevance)
        mixed = [matches[o['id']] for o,_,_ in ranked]
        ranking = {o['id']:dict(relevance_score=base, uniqueness_bonus=round(bonus,4)) for o,base,bonus in ranked}
        page = mixed[offset:offset+limit]
        cards = self.decorate([{**o, 'recommendation_type':'neutral' if using_fallback else 'matched', 'ranking':ranking[o['id']], 'venues':venues, 'minutes':q['minutes'], 'suggested_quest_id':q['id'], 'preparation_difficulty':q['difficulty'], 'size':q['size'], 'effort':q['effort']} for o,q,venues in page])
        if related:
            for card in cards:
                exact = interest_tags.intersection(supported_interests(card['personalization']))
                nearby = [g['name'] for g in INTEREST_GROUPS if g['name'] != 'Original interests' and set(g['interests']).intersection(interest_tags) and set(g['interests']).intersection(supported_interests(card['personalization']))]
                card['recommendation_reason'] = ('Matches '+', '.join(sorted(exact))) if exact else ('Related to your '+', '.join(nearby)+' interests') if nearby else 'An exploratory option; no direct interest match.'
        if using_fallback:
            cards = [{**o,'matching_tags':[]} for o in cards]
        return dict(opportunities=cards, quests=self.mark_quests(self.quests_for(cards)), total=len(mixed), offset=offset, limit=limit, has_more=offset+limit<len(mixed), data_mode='catalog', fallback=fallback_info(using_fallback,filters), kinds=sorted({o['kind'] for o in self.catalog.values()}))
    def today(self):
        return self.clock().astimezone(DAY_ZONE).date()
    def profile(self):
        p = self.db.get('profiles', 'demo')
        if p:
            p['goals'] = ['Internship' if g == 'Land a software engineering internship' else g for g in p.get('goals', [])]
            if p.get('goal') == 'Land a software engineering internship':
                p['goal'] = 'Internship'
        return p
    def activity(self, kind):
        return [a for a in self.db.all('activity') if a['kind'] == kind and a['profile_id'] == 'demo']
    def checkin(self):
        return next((a for a in self.activity('checkin') if a['date'] == self.today().isoformat()), None)
    def completion_day(self, a):
        return datetime.fromisoformat(a['completed_at']).astimezone(DAY_ZONE).date()
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
        return dict(demo_clock=self.demo_state(), streak=streak, longest_streak=best, active_today=self.today() in dates, today=self.today().isoformat(), timezone='America/Los_Angeles', points=sum((a['points'] for a in done)), completed_count=len(done), saved_count=len(self.activity('save')), completed_ids=[a['quest_id'] for a in done], activity=done)
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
