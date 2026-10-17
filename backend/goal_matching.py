"""Conservative title-based goal tags; these are app classifications, not source claims."""
import re

RULES = {
    'Gain research experience': r'\bresearch\b|\blaboratory\b|\blab assistant\b',
    'Contribute to open source': r'open[ -]source|github contribution|contribut(?:e|ing) to',
    'Explore careers and discover my interests': r'career|job shadow|informational interview|industry exploration',
    'Excel academically': r'study skills|exam prep|academic|tutoring|note[ -]taking|study plan',
    'Give back and help others': r'volunteer|community service|nonprofit|social impact|mentoring|help others',
    'Improve my financial independence': r'personal finance|financial literacy|budget|saving money|financial independence|freelanc|part[ -]time',
    'Earn certifications and professional credentials': r'certificat|professional credential|\bcertified\b|\bcomptia\b|\baws\b.*\bexam\b',
    'Build real-world work experience': r'\bintern\b|internship|apprentice|freelanc|part[ -]time|work experience|job simulation|\bco[ -]op\b',
    'Grow my professional online presence': r'linkedin|personal brand|online portfolio|professional profile|portfolio website|personal website',
    'Compete and earn recognition': r'competition|hackathon|\bcontest\b|tournament|pitch challenge|competitive programming',
}

def with_goal_matches(row):
    matches = {goal: 'Title matches: '+match.group(0) for goal, pattern in RULES.items()
               if (match := re.search(pattern, row.get('title', ''), re.I))}
    p = row['personalization']
    return {**row, 'personalization': {**p, 'goals': list(dict.fromkeys(p.get('goals', []) + list(matches))),
                                      'inferred_goal_matches': matches}}
