"""Read-only search over the portable collected catalog; independent of demo state."""
import gzip
import hashlib
import json
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path
from datetime import datetime, timezone
try:
    from .filter_rules import supported_interests, validate_extra, matches_extra, matches_search, matches_locations, matches_choices
    from .ranking import rank_records, match_details
    from .goal_matching import with_goal_matches, RULES
except ImportError:
    from filter_rules import supported_interests, validate_extra, matches_extra, matches_search, matches_locations, matches_choices
    from ranking import rank_records, match_details
    from goal_matching import with_goal_matches, RULES

CATALOG_DIRECTORY = Path(__file__).resolve().parent / "catalog"


def distance_km(lat, lon, coordinates):
    phi1, phi2 = math.radians(lat), math.radians(coordinates["latitude"])
    dphi = phi2 - phi1
    dlambda = math.radians(coordinates["longitude"] - lon)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(min(1, a)))


class CatalogReader:
    def __init__(self, rows, taxonomy):
        rows = [with_goal_matches(row) for row in rows]
        self.rows = rows
        self.taxonomy = {**taxonomy, "goals": list(dict.fromkeys(taxonomy["goals"] + list(RULES)))}
        self.by_id = {row["id"]: row for row in rows}
        if len(self.by_id) != len(rows):
            raise ValueError("Duplicate IDs in app catalog")
        self.search_text = {row["id"]: " ".join(str(row.get(key) or "") for key in ("title", "description", "organization", "location", "kind")).casefold() for row in rows}

    def query(self, *, interests=(), goals=(), challenge_levels=(), time_buckets=(), locations=(),
              commitment=None, q="", scope="opportunity", lat=None, lon=None, radius_km=25,
              include_past=False, source=None, kind=None, offset=0, limit=20,
              skills=(), experience=(), cost=(), prerequisites=(), duration_quality=(), schedule=(), max_minutes=None, match_mode='any'):
        extra = dict(experience=experience, cost=cost, prerequisites=prerequisites,
                     duration_quality=duration_quality, schedule=schedule, max_minutes=max_minutes)
        validate_extra(extra)
        matches_choices([], [], match_mode)
        for label, value, field in (("source", source, "source"), ("kind", kind, "kind")):
            if value and value not in {row[field] for row in self.rows}:
                raise ValueError("Unknown " + label + " filter")
        if any(value not in {skill for row in self.rows for skill in row.get("skills", [])} for value in skills):
            raise ValueError("Unknown skills filter")
        if scope not in {"opportunity", "first_step", "micro_step"}:
            raise ValueError("scope must be opportunity, first_step or micro_step")
        for key, values in (("interests", interests), ("goals", goals), ("challenge_levels", challenge_levels), ("time_buckets", time_buckets), ("location_preferences", locations)):
            if any(value not in self.taxonomy[key] for value in values):
                raise ValueError(f"Unknown {key}; use /catalog/options")
        if len(set(goals)) > self.taxonomy["max_selected_goals"]:
            raise ValueError("Choose up to 3 goals")
        if len(set(interests)) > self.taxonomy.get("max_selected_interests", 10):
            raise ValueError("Choose up to 10 interests")
        if commitment is not None and commitment not in self.taxonomy["commitment_preferences"]:
            raise ValueError("Unknown commitment preference")
        if not isinstance(q, str) or len(q) > 300:
            raise ValueError("Search text must be at most 300 characters")
        if not isinstance(offset, int) or offset < 0 or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("offset must be nonnegative; limit must be 1-100")
        if (lat is None) != (lon is None):
            raise ValueError("Supply both lat and lon")
        if lat is not None and (not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180):
            raise ValueError("Invalid latitude or longitude")
        if not math.isfinite(radius_km) or not 0 < radius_km <= 500:
            raise ValueError("radius_km must be greater than 0 and at most 500")
        if "Near me" in locations and lat is None:
            raise ValueError("Near me requires lat and lon; unknown locations do not count as nearby")
        terms = q.casefold().split()
        matches = []
        facets = {key: Counter() for key in ("interests", "goals", "challenge_levels", "time_buckets", "location_preferences")}
        for row in self.rows:
            if row["status"] == "cancelled":
                continue
            end = row.get("source_facts", {}).get("end")
            if isinstance(end, dict):
                end = end.get("utc")
            ended = False
            if isinstance(end, str):
                try:
                    parsed = datetime.fromisoformat(end.replace("Z", "+00:00"))
                    ended = parsed.tzinfo is not None and parsed < datetime.now(timezone.utc)
                except ValueError:
                    pass
            if not include_past and (row["status"] == "past" or ended):
                continue
            if source and row["source"] != source or kind and row["kind"] != kind:
                continue
            if not matches_search(row, q):
                continue
            p = row["personalization"]
            if not matches_choices(interests, supported_interests(p), match_mode):
                continue
            if not matches_choices(goals, p["goals"], match_mode):
                continue
            if skills and not set(skills).intersection(row.get("skills", [])):
                continue
            if not matches_extra(row, extra, scope):
                continue
            plan = p if scope == "opportunity" else p[scope]
            challenges = p["challenge_levels"] if scope == "opportunity" else [plan["challenge_level"]]
            times = p["time_buckets"] if scope == "opportunity" else [plan["time_bucket"]]
            selected_commitment = p["commitment"] if scope == "opportunity" else plan["commitment"]
            if challenge_levels and not set(challenge_levels).intersection(challenges):
                continue
            if time_buckets and not set(time_buckets).intersection(times):
                continue
            if commitment and commitment != "A mix of both" and commitment != selected_commitment:
                continue
            nearby = False
            km = None
            coordinates = row.get("coordinates")
            if lat is not None and coordinates is not None:
                km = distance_km(lat, lon, coordinates)
                nearby = km <= radius_km
            resolved_locations = p["location_preferences"] + (["Near me"] if nearby else [])
            if not matches_locations(locations, resolved_locations):
                continue
            facets["interests"].update(p["interests"])
            facets["goals"].update(p["goals"])
            facets["challenge_levels"].update(challenges)
            facets["time_buckets"].update(times)
            facets["location_preferences"].update(resolved_locations)
            matches.append((row, km, challenges, times, selected_commitment))
        by_id = {entry[0]['id']:entry for entry in matches}
        ranked = rank_records([entry[0] for entry in matches], lambda row: match_details(row, interests, goals, skills, q)['score'])
        page = []
        for row,base,bonus in ranked[offset:offset + limit]:
            row, km, challenges, times, selected_commitment = by_id[row['id']]
            page.append({**row, "match_details": match_details(row, interests, goals, skills, q), "ranking": {"relevance_score":base,"uniqueness_bonus":round(bonus,4)}, "match": {"scope": scope, "challenge_levels": challenges,
                        "time_buckets": times, "commitment": selected_commitment,
                        "distance_km": round(km, 2) if km is not None else None}})
        return {"opportunities": page, "total": len(matches), "offset": offset, "limit": limit,
                "facets": facets, "scope": scope}


@lru_cache(maxsize=1)
def _load(path, manifest_modified, data_modified):
    directory = Path(path)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    data = directory / "opportunities.json.gz"
    if hashlib.sha256(data.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Catalog checksum mismatch; regenerate the app export")
    with gzip.open(data, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload["schema_version"] != 1 or len(payload["opportunities"]) != manifest["record_count"]:
        raise ValueError("App catalog schema or count mismatch")
    return CatalogReader(payload["opportunities"], manifest["taxonomy"])


def load_catalog(directory=CATALOG_DIRECTORY):
    directory = Path(directory)
    return _load(str(directory), (directory / "manifest.json").stat().st_mtime_ns,
                 (directory / "opportunities.json.gz").stat().st_mtime_ns)
