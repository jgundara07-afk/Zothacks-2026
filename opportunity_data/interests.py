"""Conservative granular-interest evidence for the expanded choice catalog.

New choices match titles and structured amenities only, avoiding incidental
provider marketing text. Zero-match interests remain selectable without inventing
opportunities or implying all subtopics fit a broad legacy label.
"""
import json
import re
from pathlib import Path

CATALOG = json.loads((Path(__file__).resolve().parents[1] / 'shared' / 'interest_catalog.json').read_text(encoding='utf-8'))
LEGACY = set(CATALOG['groups'][0]['interests'])
ALIASES = {
    'Frontend development': r'front[ -]?end(?: development| engineering| developer)?',
    'Backend development': r'back[ -]?end(?: development| engineering| developer)?',
    'Full-stack development': r'full[ -]?stack(?: development| developer)?',
    'Web development': r'web develop\w*|html5?|css3?|javascript|django|flask',
    'Mobile app development': r'mobile (?:app(?:lication)? )?develop\w*|android|ios app',
    'iOS development': r'ios (?:app|develop\w*)|swift(?:ui)?|arkit',
    'Android development': r'android(?: develop\w*)?|kotlin',
    'Artificial intelligence': r'artificial intelligence|generative ai|(?-i:AI)',
    'Machine learning': r'machine learning|aprendizaje autom[aá]tico',
    'Deep learning': r'deep learning|neural networks?',
    'Generative AI': r'generative ai|genai|chatgpt|large language models?|llms?',
    'Natural language processing': r'natural language processing|(?-i:NLP)',
    'Data analytics': r'data analy\w*|tableau|power bi|power query',
    'Database engineering': r'database\w*|sql|mysql|postgresql|mongodb|redis',
    'Cloud computing': r'cloud|aws|azure|google cloud|gcp',
    'Ethical hacking': r'ethical hack\w*|penetration test\w*',
    'UI/UX design': r'ui/?ux|ux/?ui|user experience|user interface|figma',
    'API development': r'api (?:develop\w*|design)|rest apis?|graphql|fastapi',
    'Software testing': r'software test\w*|unit test\w*|test automation|selenium|cypress',
    'Resume building': r'resume\w*|résumé\w*|cover letters?',
    'Interview preparation': r'interview\w*',
    'Hiking': r'hik(?:e|es|ing)|trails?',
    'Networking': r'professional networking|networking (?:mixer|event|101)|business mixer',
    'Mentorship': r'mentor(?:ship|ing)?',
    'Volunteering': r'volunteer\w*',
    'Gardening': r'gardening|garden shift|garden(?:ing)? workshop',
    'Personal finance': r'personal financ\w*|financial literacy|budgeting',
}

def literal(label):
    return re.escape(label).replace(r'\ ', r'[\s-]+').replace(r'\-', r'[\s-]?')

PATTERNS = {label: re.compile(r'(?<!\w)(?:'+ALIASES.get(label,literal(label))+r')(?!\w)',re.I)
            for group in CATALOG['groups'][1:] for label in group['interests'] if label not in LEGACY}

def granular_matches(row):
    text = (row.get('title') or '')+' '+' '.join(row.get('amenities') or [])
    result={}
    for label,pattern in PATTERNS.items():
        match=pattern.search(text)
        if match: result[label]='Title/amenity evidence: '+match[0]
    if row.get('kind')=='Trail':result['Hiking']='Official mapped trail segment; route/access must be verified'
    return result
