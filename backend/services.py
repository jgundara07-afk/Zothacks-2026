from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

DAY_ZONE = ZoneInfo("America/Los_Angeles")

class OneThing:
    """Shared reads for the single demo profile: profile, activity, today's check-in, progress, and the personalized feed."""
    def __init__(self, db, clock):
        self.db = db
        self.clock = clock
    def today(self):
        return self.clock().astimezone(DAY_ZONE).date()
    def profile(self):
        return next(iter(self.db.all('profiles')), None)
    def activity(self, kind):
        return [a for a in self.db.all('activity') if a['kind'] == kind and a['profile_id'] == 'demo']
    def checkin(self):
        return next((a for a in self.activity('checkin') if a['date'] == self.today().isoformat()), None)
    def completion_day(self, a):
        return datetime.fromisoformat(a['completed_at']).astimezone(DAY_ZONE).date()
    def progress(self):
        today = self.today()
        done = sorted(self.activity('completion'), key=lambda a:a['completed_at'], reverse=True)
        dates = {self.completion_day(a) for a in done}
        cursor = today if today in dates else today - timedelta(days=1)
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
        return dict(streak=streak, longest_streak=best, active_today=today in dates, today=today.isoformat(), timezone='America/Los_Angeles', points=sum(a['points'] for a in done), completed_count=len(done), saved_count=len(self.activity('save')), completed_ids=[a['quest_id'] for a in done], activity=done)
    def opportunities(self):
        p = self.profile() or {}
        tags = p.get('interests', []) + p.get('skills', [])
        saved = {a['opportunity_id'] for a in self.activity('save')}
        result = [{**o, 'matching_tags':[t for t in o['tags'] if t in tags], 'saved':o['id'] in saved} for o in self.db.all('opportunities')]
        effort = (self.checkin() or {}).get('effort')
        if effort:
            variants = {q['opportunity_id']: q for q in self.db.all('quests') if q.get('effort') == effort}
            result = [{**o, 'minutes': variants[o['id']]['minutes'], 'suggested_quest_id': variants[o['id']]['id'], 'effort':effort, 'difficulty':variants[o['id']]['difficulty']} for o in result]
        return sorted(result, key=lambda o:-len(o['matching_tags']))
