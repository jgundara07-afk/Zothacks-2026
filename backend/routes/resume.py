import re
from flask import jsonify
try:
    from . import body
except ImportError:
    from routes import body

ROLES = {'Product designer':['Design','Research','Writing'], 'Software developer':['Coding','Research','Writing'], 'Community organizer':['Writing','Research','Design']}
ALIASES = {'Coding':['coding','python','javascript','react','programming','software','html','css','sql'], 'Design':['design','figma','wireframe','prototype','ux','ui'], 'Writing':['writing','wrote','written','copywriting','communication','documentation','editor'], 'Research':['research','analysis','analytics','survey','interview','data']}

def register(app, svc):
    db = svc.db
    @app.post('/resume-analysis')
    def resume_analysis():
        data = body('text')
        if not data['text'].strip() or len(data['text'])>30000:
            raise ValueError('Paste between 1 and 30,000 characters of resume text.')
        role = data.get('role','Software developer')
        if not isinstance(role,str) or role not in ROLES:
            raise ValueError('Choose a supported target role.')
        text = data['text'].lower()
        found = [skill for skill,words in ALIASES.items() if any(re.search(r'\b'+re.escape(word)+r'\b',text) for word in words)]
        gaps = [skill for skill in ROLES[role] if skill not in found]
        recommendations = [dict(opportunity_id=o['id'], skills=[t for t in o.get('skills',[]) if t in gaps]) for o in db.all('opportunities') if any(t in gaps for t in o.get('skills',[]))]
        return jsonify(role=role, found_skills=found, gaps=gaps, recommendations=recommendations, method='Local keyword matching against fictional role templates. Missing keywords are prompts to explore, not an assessment of your ability. Resume text is not stored.')
