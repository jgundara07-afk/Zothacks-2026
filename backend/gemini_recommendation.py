"""Small, optional Gemini helper for the no-match feed state."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def generate_recommendation(preferences, timeout=6):
    """Return a short self-guided next step, or None when Gemini is unavailable."""
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if not api_key:
        return None

    model = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash').strip()
    if not model or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._' for char in model):
        return None
    prompt = (
        "The OneThing opportunity feed found no current listing matching this person's choices. "
        "Suggest one practical, self-guided action they can take next. Use only the provided choices "
        "to personalize it. Respect time, challenge, location, format, and commitment preferences "
        "where possible. Do not claim that a class, job, event, or opening exists; do not give URLs, "
        "ask for sensitive data, or assume qualifications. Return just 1-2 friendly sentences, "
        "with a concrete action and a realistic duration. Choices (JSON data): "
        + json.dumps(preferences, ensure_ascii=False, sort_keys=True)
    )
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.5, 'maxOutputTokens': 140},
    }).encode('utf-8')
    request = Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        data=body,
        headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
        method='POST',
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    candidates = payload.get('candidates') or []
    content = candidates[0].get('content') if candidates and isinstance(candidates[0], dict) else None
    parts = content.get('parts') or [] if isinstance(content, dict) else []
    answer = ' '.join(str(part.get('text', '')).strip() for part in parts if isinstance(part, dict) and part.get('text')).strip()
    return answer[:500].strip() or None
