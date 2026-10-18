"""Server-side Supabase session verification and OneThing email policy."""
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_DOMAINS = frozenset({
    'gmail.com', 'outlook.com', 'hotmail.com', 'live.com', 'yahoo.com',
    'icloud.com', 'me.com', 'mac.com', 'proton.me', 'protonmail.com', 'uci.edu',
})
EMAIL_PATTERN = re.compile(r"^([A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)$")
DOMAIN_ERROR = ('Use a Gmail, Outlook/Hotmail/Live, Yahoo, iCloud, Proton, '
                'or UC Irvine email address.')


def normalize_email(value):
    if not isinstance(value, str):
        raise ValueError('Enter a valid email address.')
    value = value.strip()
    if len(value) > 254 or not EMAIL_PATTERN.fullmatch(value):
        raise ValueError('Enter a valid email address.')
    local, domain = value.rsplit('@', 1)
    if (len(local) > 64 or local.startswith('.') or local.endswith('.') or '..' in local
            or any(label.startswith('-') or label.endswith('-') for label in domain.split('.'))):
        raise ValueError('Enter a valid email address.')
    domain = domain.lower()
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(DOMAIN_ERROR)
    return local + '@' + domain


class AuthUnavailable(Exception):
    pass


def supabase_settings():
    """Project URL and public key. Both are public, so the frontend's VITE_ copies are accepted as a fallback;
    a deployment that set only the browser values (e.g. on Render) still verifies sessions."""
    base = (os.getenv('SUPABASE_URL') or os.getenv('VITE_SUPABASE_URL') or '').strip().rstrip('/')
    key = (os.getenv('SUPABASE_PUBLISHABLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
           or os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY') or '').strip()
    return base, key


def verify_supabase_token(token):
    """Ask Supabase Auth to validate the current access token."""
    base, key = supabase_settings()
    if not base or not key:
        raise AuthUnavailable('Authentication is not configured on the server.')
    parsed = urlparse(base)
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in {'localhost', '127.0.0.1'}):
        raise AuthUnavailable('SUPABASE_URL must use HTTPS, except for a local Supabase stack.')
    request = Request(base + '/auth/v1/user', headers={
        'apikey': key, 'Authorization': 'Bearer ' + token,
        'Accept': 'application/json',
    })
    try:
        with urlopen(request, timeout=8) as response:
            return json.load(response)
    except HTTPError as error:
        if 400 <= error.code < 500 and error.code != 429:
            return None
        raise AuthUnavailable('Authentication is temporarily unavailable.') from error
    except (URLError, TimeoutError, ValueError) as error:
        raise AuthUnavailable('Authentication is temporarily unavailable.') from error
