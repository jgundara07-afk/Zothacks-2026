"""General wellbeing alternatives, never invented matches to career preferences."""
import re

PERSONAL_DEVELOPMENT = re.compile(
    r'\b(mindfulness|self.improvement|personal growth|time management|productivity|'
    r'habit building|goal setting|study skills|confidence building|'
    r'emotional intelligence|critical thinking|communication skills|stress management)\b', re.I)


def is_neutral(row):
    return bool(row.get('general_task')) or row.get('kind') == 'Park' or (
        row.get('kind') == 'Online course' and bool(PERSONAL_DEVELOPMENT.search(row.get('title', ''))))


def fallback_info(active, filters):
    return dict(active=active,
                reason='no_available_interest_goal_matches' if active else None,
                relaxed_filters=[key for key in ('interests','goals') if filters.get(key)] if active else [],
                message=('No current opportunities match your interests and goals with these filters. '
                         'Here are some general tasks, wellbeing and self-improvement alternatives that fit your other preferences.') if active else None)


def sprinkle(matched, general, every=7):
    """Insert at most one distinct general task after seven personalized items.

    Short result sets receive one task at the end. Applied before pagination,
    preserving deterministic offsets without repeating tasks already in results.
    """
    remaining=iter(general);result=[]
    for index,item in enumerate(matched,1):
        result.append(item)
        if index % every==0:
            task=next(remaining,None)
            if task is not None:result.append(task)
    if matched and len(matched)%every:
        task=next(remaining,None)
        if task is not None:result.append(task)
    return result
