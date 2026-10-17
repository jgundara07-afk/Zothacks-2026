"""Evidence-based counters for the mountain regions; no inferred external outcomes."""
from calendar import monthrange
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

ZONE = ZoneInfo('America/Los_Angeles')
OUTCOMES = {
    'applied':'Submitted a job/internship application',
    'certification_completed':'Finished an online certification',
    'simulation_completed':'Finished a job simulation',
    'event_attended':'Attended the event',
    'portfolio_updated':'Added a project or certification to my resume/portfolio',
    'outreach_sent':'Sent a cold outreach message', 'alumni_connected':'Connected with a university alum',
    'coffee_chat':'Scheduled or attended a virtual coffee chat', 'peer_endorsed':'Endorsed a peer for a skill',
    'community_posted':'Posted in a professional community', 'volunteered':'Volunteered for an event/project',
    'thank_you_sent':'Sent a thank-you note', 'followed_five':'Followed 5 industry leaders or companies',
    'mentor_contacted':'Reached out for advice or mentorship', 'phone_free_walk':'Walked without a phone or music',
    'screens_off_30':'Stopped screen use 30 minutes before bed', 'boundary_set':'Declined or delayed a non-essential task',
    'focused_pomodoro':'Finished a distraction-free 25-minute Pomodoro', 'three_wins':'Wrote 3 wins for the week',
    'workday_audit':'Tracked my time for a whole workday', 'shortcut_five':'Used a new shortcut 5 times',
    'unsubscribed_five':'Unsubscribed from 5 newsletters', 'public_update':'Published a GitHub/public portfolio update',
    'industry_joined':'Joined an industry-specific job board or forum',
}


def expanded_progress(svc, rows, definitions, facts_for):
    metrics, values, earned = Counter(), Counter(), {}
    days, daily_days, weeks, skills, categories = set(), set(), set(), Counter(), Counter()
    by_week, by_day, lazy_filtered, cleaning = Counter(), Counter(), Counter(), defaultdict(set)
    saved, ever_saved, filtered_saved, dismissed, completed = set(), set(), set(), set(), set()
    saved_at, saved_categories, outcomes = {}, {}, defaultdict(set)
    monthly, archetypes = set(), {}
    escalation = 0
    required_categories = {o.get('kind') for o in svc.opportunities() if o.get('kind')}

    def observe(stamp):
        for badge in definitions:
            value = metrics[badge['metric']]
            values[badge['id']] = min(badge['target'], value)
            if value >= badge['target'] and badge['id'] not in earned:
                earned[badge['id']] = stamp

    def longest(sequence, delta):
        best = run = 0
        previous = None
        for item in sorted(sequence):
            run = run + 1 if previous is not None and item == previous + delta else 1
            best = max(best, run)
            previous = item
        return best

    def backlog_metrics():
        converted = completed & ever_saved
        metrics['save_total'] = len(ever_saved)
        metrics['converted'] = len(converted)
        metrics['conversion'] = int(100 * len(converted) / len(ever_saved)) if ever_saved else 0
        metrics['filtered_saves'] = len(filtered_saved)
        metrics['unsaves'] = len(dismissed)
        metrics['zero_inbox'] = int(bool(ever_saved) and not saved and ever_saved <= completed)
        metrics['save_categories'] = int(bool(required_categories) and required_categories <= set(saved_categories.values()))

    timeline = [(row['completed_at'], 'completion', row) for row in rows]
    histories = svc.activity('bookmark_history')
    for kind in ('bookmark_history', 'profile_update', 'recap', 'ui_event'):
        timeline.extend((row['recorded_at'], kind, row) for row in (histories if kind == 'bookmark_history' else svc.activity(kind)))
    historic_ids = {row['opportunity_id'] for row in histories if row['action'] == 'save'}
    for row in svc.activity('save'):
        if row['opportunity_id'] not in historic_ids:
            timeline.append((row.get('saved_at') or svc.clock().isoformat(), 'bookmark_history', {**row, 'action':'save'}))
    for stamp, kind, row in sorted(timeline, key=lambda entry: entry[0]):
        local = datetime.fromisoformat(stamp).astimezone(ZONE)
        day = local.date()
        if kind == 'bookmark_history':
            oid = row['opportunity_id']
            if row['action'] == 'save':
                saved.add(oid); ever_saved.add(oid); saved_at[oid] = stamp
                opportunity = svc.opportunity(oid) or {}
                saved_categories[oid] = row.get('category') or opportunity.get('kind')
                if row.get('filtered'): filtered_saved.add(oid)
            else:
                saved.discard(oid)
                cleaning[day].add(oid)
                if oid not in completed: dismissed.add(oid)
            metrics['clean_day'] = max(metrics['clean_day'], len(cleaning[day]))
            backlog_metrics()
        elif kind == 'profile_update':
            metrics['goal_changes'] += 1
        elif kind == 'ui_event':
            metrics[row['event']] += 1
        elif kind == 'recap':
            if row['period'] == 'month':
                month = row['month']
                y, m = map(int, month.split('-'))
                monthly.add(y*12+m)
                metrics['monthly_recaps'] = len(monthly)
                metrics['recap_run'] = longest(monthly, 1)
                if row['source'] == 'gemini':
                    archetypes[y*12+m] = row['archetype'].strip().casefold()
                    metrics['archetype_change'] = int(any(key-1 in archetypes and value != archetypes[key-1] for key,value in archetypes.items()))
            if row['period'] == 'year': metrics['yearly_recaps'] += 1
            if row['source'] == 'gemini': metrics['gemini_recaps'] += 1
        else:
            quest = svc.quest(row['quest_id']) or {}
            oid = row.get('opportunity_id') or quest.get('opportunity_id')
            opportunity = svc.opportunity(oid) or {}
            facts = facts_for(quest, opportunity)
            category = row.get('achievement_category') or facts['achievement_category']
            if category == 'Other': category = row.get('category', 'Other')
            tags = row.get('achievement_tags', facts['achievement_tags'])
            difficulty = row.get('difficulty', quest.get('difficulty','Easy'))
            completed.add(oid)
            metrics['quests'] += 1; metrics['points'] += row.get('points',0)
            metrics[difficulty.lower()] += 1
            metrics['logged_minutes'] += row.get('actual_minutes') or 0
            days.add(day); weeks.add(day-timedelta(days=day.weekday()))
            if row.get('daily', quest.get('daily', False)) or row.get('micro_goal'):
                daily_days.add(day)
            metrics['daily_streak'] = longest(daily_days, timedelta(days=1))
            metrics['weekly_run'] = longest(weeks, timedelta(weeks=1))
            by_week[day-timedelta(days=day.weekday())] += 1
            metrics['week_quests'] = max(by_week.values())
            by_day[day] += 1
            if day.weekday() >= 5: metrics['weekend_day'] = max(metrics['weekend_day'],by_day[day])
            if local.hour < 9 and row.get('micro_goal', facts['micro_goal']): metrics['early_micro'] += 1
            if local.hour < 4: metrics['night'] += 1
            if difficulty == 'Lazy' and row.get('lazy_filter'):
                lazy_filtered[day] += 1; metrics['lazy_filter_day'] = max(lazy_filtered.values())
            if difficulty == 'Challenging' and (row.get('actual_minutes') or 0) > row.get('minutes',quest.get('minutes',0)):
                metrics['overtime'] += 1
            if difficulty == ['Lazy','Easy','Hard','Challenging'][min(escalation,3)] and escalation < 4: escalation += 1
            metrics['escalation'] = escalation
            if difficulty in {'Hard','Challenging'}: metrics['hard_points'] += row.get('points',0)
            if category != 'Other': categories[category] += 1
            metrics['categories'] = len(categories); metrics['specialist'] = max(categories.values(),default=0)
            if opportunity.get('kind',row.get('category')) in {'Class','Classes'}: metrics['class'] += 1
            if 'networking' in tags: metrics['network'] += 1
            skills.update(set(row.get('skills', opportunity.get('skills',[]))))
            metrics['skills'] = len(skills); metrics['skill_repeat'] = max(skills.values(),default=0)
            skill_text=' '.join(row.get('skills', opportunity.get('skills',[])))
            if re.search(r'coding|programming|python|javascript|data|software|research|design|engineering|security',skill_text,re.I): metrics['technical'] += 1
            if re.search(r'writing|communication|leadership|teamwork|negotiation|listening|presentation',skill_text,re.I): metrics['soft'] += 1
            if row.get('goal_match') and row.get('skills'): metrics['goal_skill'] += 1
            task_number=row.get('task_number') or (opportunity.get('general_task') or {}).get('number')
            task_metrics={1:'presence',2:'resume_polish',5:'resume_polish',48:'ergonomic',47:'hydration',56:'zen',49:'screen_break',50:'clean_desk',51:'clean_desk',23:'pitch',6:'star',21:'salary',16:'job_alert',35:'prioritize'}
            if task_number in task_metrics: metrics[task_metrics[task_number]] += 1
            for outcome in row.get('outcomes',[]):
                source_kind=opportunity.get('kind',row.get('category'))
                if outcome == 'applied' and source_kind not in {'Job','Internship'}: continue
                if outcome == 'certification_completed' and source_kind not in {'Online course','Certification'}: continue
                if outcome == 'simulation_completed' and source_kind != 'Job simulation': continue
                if outcome == 'event_attended' and source_kind not in {'Local event','Networking','Networking event','Campus event','Club','Campus initiative'}: continue
                if outcome == 'focused_pomodoro' and (row.get('actual_minutes') or 0) < 25: continue
                outcomes[outcome].add(oid if outcome in {'certification_completed','event_attended'} else row['id'])
                metrics[outcome] = len(outcomes[outcome])
            earlier = row.get('saved_at') or saved_at.get(oid)
            if earlier:
                earlier_dt = datetime.fromisoformat(earlier).astimezone(ZONE)
                if local >= earlier_dt:
                    if local-earlier_dt > timedelta(days=7): metrics['old_week'] += 1
                    next_y=earlier_dt.year+(earlier_dt.month==12);next_m=earlier_dt.month%12+1
                    month_later=earlier_dt.replace(year=next_y,month=next_m,day=min(earlier_dt.day,monthrange(next_y,next_m)[1]))
                    if local > month_later: metrics['old_month'] += 1
                    if day == earlier_dt.date(): metrics['same_day'] += 1
                cleaning[day].add(oid)
                metrics['clean_day'] = max(metrics['clean_day'],len(cleaning[day]))
            backlog_metrics()
        observe(stamp)
    return values, earned
