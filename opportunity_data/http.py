"""Bounded HTTP requests and reproducible, credential-free raw receipts."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

USER_AGENT = "OneThingCollector/0.1 (manual student opportunity catalog)"


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def public_url(url):
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query)
             if key.lower() not in {"api_key", "token", "access_token", "key"}]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


class Fetcher:
    def __init__(self, directory, delay=0.25):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.last_request = 0
        self.receipts = []

    def get(self, source, url, params=None, headers=None):
        for attempt in range(3):
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=(10, 60))
            except requests.RequestException:
                self.last_request = time.monotonic()
                if attempt == 2:
                    raise RuntimeError(f"Network request failed for {source}; check connectivity") from None
                time.sleep(2 ** attempt)
                continue
            self.last_request = time.monotonic()
            digest = hashlib.sha256(response.content).hexdigest()
            folder = self.directory / source
            folder.mkdir(exist_ok=True)
            path = folder / f"{digest}.raw"
            path.write_bytes(response.content)
            receipt = {"source": source, "url": public_url(response.url),
                       "collected_at": utcnow(), "status": response.status_code,
                       "sha256": digest, "raw_path": str(path.resolve()),
                       "content_type": response.headers.get("Content-Type")}
            self.receipts.append(receipt)
            with (self.directory / "receipts.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(receipt) + "\n")
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                retry = response.headers.get("Retry-After", "")
                # Never hammer a source that requests a long pause.
                if retry and (not retry.isdigit() or int(retry) > 60):
                    raise RuntimeError(f"{source} requested a later retry; stop and rerun manually")
                time.sleep(max(int(retry or 0), 2 ** (attempt + 1)))
                continue
            if response.status_code >= 400:
                raise RuntimeError(f"{source} returned HTTP {response.status_code}; see raw receipt")
            return response, receipt
        raise RuntimeError(f"{source} exhausted retries")
