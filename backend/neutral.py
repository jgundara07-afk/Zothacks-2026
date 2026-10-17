"""General wellbeing alternatives, never invented matches to career preferences."""
import re

PERSONAL_DEVELOPMENT = re.compile(
    r'\b(mindfulness|self.improvement|personal growth|time management|productivity|'
    r'habit building|goal setting|study skills|confidence building|'
    r'emotional intelligence|critical thinking|communication skills|stress management)\b', re.I)


def is_neutral(row):
    return row.get('kind') == 'Park' or (
        row.get('kind') == 'Online course' and bool(PERSONAL_DEVELOPMENT.search(row.get('title', ''))))


def fallback_info(active, filters):
    return dict(active=active,
                reason='no_available_interest_goal_matches' if active else None,
                relaxed_filters=[key for key in ('interests','goals') if filters.get(key)] if active else [],
                message=('No current opportunities match your interests and goals with these filters. '
                         'Here are some general wellbeing and self-improvement alternatives that fit your other preferences.') if active else None)
