"""Profile context: supported constraints only; never infers travel time or eligibility."""
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
try:
    from .filter_rules import matches_search, searchable, term_matches
except ImportError:
    from filter_rules import matches_search, searchable, term_matches

OPTIONS=json.loads((Path(__file__).resolve().parents[1]/'shared/user_context.json').read_text(encoding='utf-8'))
TEXT_FIELDS={'country','state','city','school'}
CHOICES={'situation','experience','availability','days','budget','transportation','travel','relocate'}

def validate_context(value):
    if not isinstance(value,dict) or set(value)-TEXT_FIELDS-CHOICES-{'formats'}:
        raise ValueError('Provide valid situation details as an object.')
    result={}
    for key in TEXT_FIELDS:
        text=value.get(key,'')
        if not isinstance(text,str) or len(text)>120:
            raise ValueError(key+' must be text under 120 characters.')
        result[key]=text.strip()
    for key in CHOICES:
        choice=value.get(key,'')
        if not isinstance(choice,str) or choice and choice not in OPTIONS[key]:
            raise ValueError('Choose a valid '+key+'.')
        result[key]=choice
    formats=value.get('formats',[])
    if not isinstance(formats,list) or any(not isinstance(v,str) or v not in OPTIONS['formats'] for v in formats):
        raise ValueError('Choose valid opportunity formats.')
    result['formats']=list(dict.fromkeys(formats))
    return result

def first_step_limit(context):
    return OPTIONS['first_step_minutes'].get(context.get('availability'))

def context_match(row, context, filters):
    p=row['personalization'];assessment=p.get('assessment',{})
    allowed={'Complete beginner':{'No experience','Beginner'},'Some experience':{'No experience','Beginner'},'Intermediate':{'No experience','Beginner','Intermediate'}}
    level=assessment.get('experience_level','Unknown')
    if not filters.get('experience') and context.get('experience') in allowed and level not in allowed[context['experience']] | {'Unknown'}:
        return False
    formats=context.get('formats',[])
    text=' '.join(str(row.get(k) or '') for k in ('title','location','mode'))
    online='Online / Remote' in p['location_preferences']
    hybrid='hybrid' in searchable(text).split()
    in_person=bool(set(p['location_preferences']).intersection({'On campus','In-person events','Near me'})) or bool(row.get('coordinates'))
    if formats and not any({'Online':online,'In-person':in_person,'Hybrid':hybrid}[v] for v in formats):
        return False
    cost=assessment.get('cost','Unknown')
    # Paid prices aren't normalized reliably: never guess a dollar amount.
    if context.get('budget') in {'Free only','Under $25','Under $100'} and cost!='Free':
        return False
    if context.get('travel')=='Local only' and context.get('city') and (not online or hybrid):
        if not matches_search({'location':row.get('location','')},context['city']):return False
    day_pref=context.get('days')
    if day_pref in {'Weekdays','Weekends'} and assessment.get('schedule_type')=='Scheduled':
        start=row.get('source_facts',{}).get('start')
        if isinstance(start,dict):start=start.get('utc')
        if isinstance(start,str):
            try:
                parsed=datetime.fromisoformat(start.replace('Z','+00:00'))
                if parsed.tzinfo:
                    weekend=parsed.astimezone(ZoneInfo('America/Los_Angeles')).weekday()>=5
                    if weekend != (day_pref=='Weekends'):return False
            except ValueError:pass
    return True

def context_relevance(row,context):
    reasons=[];score=0
    # Text evidence adds a small tie-break only, never a promise of eligibility.
    text=searchable(' '.join(str(row.get(k) or '') for k in ('title','location','organization')))
    for key,weight in [('city',.12),('state',.04),('country',.03),('school',.12)]:
        value=searchable(context.get(key,''))
        if value and all(term_matches(term,text) for term in value.split()):
            score+=weight;reasons.append('Mentions your '+key)
    situation=context.get('situation')
    patterns={'Student':['intern','student','undergraduate'],'Recent graduate':['graduate','entry level'],'Career changer':['career transition','career change'],'Freelancer / self-employed':['freelance','self employed'],'Unemployed / seeking work':['job search','resume','interview'],'Employed part-time':['part time'],'Employed full-time':['professional development','continuing education']}
    if any(searchable(term) in text for term in patterns.get(situation,[])):
        score+=.12;reasons.append('Relevant to your current situation')
    level=row['personalization'].get('assessment',{}).get('experience_level','Unknown')
    if context.get('experience') and level!='Unknown':
        score+=.08;reasons.append('Experience level is classified')
    return min(score,.49),reasons
