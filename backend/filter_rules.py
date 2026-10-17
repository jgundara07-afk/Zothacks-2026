"""Shared strict predicates for both collected-catalog search APIs."""
import json
import math
from pathlib import Path

OPTIONS = json.loads((Path(__file__).resolve().parents[1] / "shared" / "catalog_filters.json").read_text(encoding="utf-8"))
EXTRA_FILTERS = {
    "experience": ("experience_level", "experience_levels"),
    "cost": ("cost", "costs"),
    "prerequisites": ("prerequisite_status", "prerequisite_statuses"),
    "duration_quality": ("duration_quality", "duration_qualities"),
    "schedule": ("schedule_type", "schedules"),
}


def supported_interests(personalization):
    if "filter_interests" in personalization:
        return personalization["filter_interests"]
    return [] if personalization.get("classification", {}).get("fallback") else personalization["interests"]


def validate_extra(filters):
    for key, (_, option) in EXTRA_FILTERS.items():
        if any(value not in OPTIONS[option] for value in filters.get(key, [])):
            raise ValueError("Unknown " + key + " filter")
    max_minutes = filters.get("max_minutes")
    if max_minutes is not None and (not math.isfinite(max_minutes) or max_minutes <= 0):
        raise ValueError("max_minutes must be finite and greater than zero")


def matches_extra(row, filters, scope="opportunity"):
    p = row["personalization"]
    assessment = p.get("assessment", {})
    for key, (field, _) in EXTRA_FILTERS.items():
        if filters.get(key) and assessment.get(field, "Unknown") not in filters[key]:
            return False
    if filters.get("max_minutes") is not None:
        maximum = p.get("duration", {}).get("max_minutes") if scope == "opportunity" else p[scope]["minutes"]
        if maximum is None or maximum > filters["max_minutes"]:
            return False
    return True
