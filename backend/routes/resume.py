from flask import jsonify, request
from collections import Counter
from datetime import timedelta
from io import BytesIO
import re
from pypdf import PdfReader
try:
    from . import body
    from ..preferences import PREFERENCES
except ImportError:
    from routes import body
    from preferences import PREFERENCES

class ResumePDFError(ValueError):
    pass

def register(app, svc):
    db = svc.db
    clock = svc.clock
    profile = svc.profile
    activity = svc.activity
    checkin = svc.checkin
    completion_day = svc.completion_day
    progress = svc.progress
    opportunities = svc.opportunities
    today = svc.today

    def analyze_resume(data):
        if not data['text'].strip() or len(data['text']) > 30000:
            raise ValueError('Paste between 1 and 30,000 characters of resume text.')
        roles = {'Product designer': ['Design', 'Research', 'Writing'], 'Software developer': ['Coding', 'Research', 'Writing'], 'Community organizer': ['Writing', 'Research', 'Design']}
        role = data.get('role', 'Software developer')
        if not isinstance(role, str) or role not in roles:
            raise ValueError('Choose a supported target role.')
        aliases = {'Coding': ['coding', 'python', 'javascript', 'react', 'programming', 'software', 'html', 'css', 'sql'], 'Design': ['design', 'figma', 'wireframe', 'prototype', 'ux', 'ui'], 'Writing': ['writing', 'wrote', 'written', 'copywriting', 'communication', 'documentation', 'editor'], 'Research': ['research', 'analysis', 'analytics', 'survey', 'interview', 'data']}
        text = data['text'].lower()
        found = [skill for skill, words in aliases.items() if any((re.search('\\b' + re.escape(word) + '\\b', text) for word in words))]
        gaps = [skill for skill in roles[role] if skill not in found]
        recommendations = [dict(opportunity_id=o['id'], skills=[t for t in o.get('skills', []) if t in gaps]) for o in db.all('opportunities') if any((t in gaps for t in o.get('skills', [])))]
        return jsonify(role=role, found_skills=found, gaps=gaps, recommendations=recommendations, method='Local keyword matching against fictional role templates. Missing keywords are prompts to explore, not an assessment of your ability. Resume text is not stored.')

    @app.post('/resume-analysis')
    def resume_analysis():
        return analyze_resume(body('text'))

    @app.post('/resume-analysis/pdf')
    def resume_pdf():
        upload = request.files.get('file')
        if upload is None or not upload.filename or (not upload.filename.lower().endswith('.pdf')):
            raise ValueError('Choose a PDF resume to upload.')
        content = upload.read(5 * 1024 * 1024 + 1)
        if len(content) > 5 * 1024 * 1024:
            return (jsonify(error='Upload a PDF under 5 MB.'), 413)
        if not content.startswith(b'%PDF-'):
            raise ValueError('This file is not a readable PDF. Choose a PDF or paste your resume text.')
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise ResumePDFError('This PDF is password-protected. Upload an unprotected copy or paste its text.')
            if len(reader.pages) > 20:
                raise ResumePDFError('Choose a PDF with 20 pages or fewer.')
            parts = []
            length = 0
            for page in reader.pages:
                stream = page.get_contents()
                if stream is not None and len(stream.get_data()) > 2 * 1024 * 1024:
                    raise ResumePDFError('This PDF page is too complex to read. Export a simpler copy or paste the text.')
                part = page.extract_text() or ''
                length += len(part)
                if length > 30000:
                    raise ResumePDFError('Keep resume text under 30,000 characters.')
                parts.append(part)
            text = '\n'.join(parts).strip()
        except ResumePDFError:
            raise
        except Exception:
            raise ResumePDFError('Could not read this PDF. Export a new PDF with selectable text, or paste your text.') from None
        if not text:
            raise ValueError('No selectable text was found. Scanned/image-only PDFs need OCR first; you can also paste resume text.')
        return analyze_resume(dict(text=text, role=request.form.get('role', 'Software developer')))
