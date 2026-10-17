"""Validate and publish a portable compressed JSON catalog, not the fictional seed."""
import gzip
import hashlib
import json
import os
import math
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .personalize import TAXONOMY, status
from .relevance import inclusion

ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT.parent / "backend" / "catalog"


def validate(row):
    p = row["personalization"]
    if p.get("taxonomy_version") != TAXONOMY["version"]:
        raise ValueError(f"{row['id']}: stale taxonomy; run offline refine first")
    for key in ("interests", "goals", "challenge_levels", "time_buckets", "location_preferences"):
        values = p[key]
        if not isinstance(values, list) or len(values) != len(set(values)) or any(value not in TAXONOMY[key] for value in values):
            raise ValueError(f"{row['id']}: invalid {key}")
        if key in {"interests", "challenge_levels", "time_buckets"} and not values:
            raise ValueError(f"{row['id']}: empty {key}")
    if p["commitment"] not in TAXONOMY["commitment_preferences"][:2]:
        raise ValueError(f"{row['id']}: invalid commitment")
    if "Near me" in p["location_preferences"]:
        raise ValueError("Near me must be calculated from user coordinates")
    for scope in ("first_step", "micro_step"):
        step = p[scope]
        if step["time_bucket"] not in TAXONOMY["time_buckets"] or step["challenge_level"] not in TAXONOMY["challenge_levels"]:
            raise ValueError(f"{row['id']}: invalid {scope} filters")
        if step["commitment"] not in TAXONOMY["commitment_preferences"][:2] or not isinstance(step["minutes"], (int, float)) or not 0 < step["minutes"] <= 120:
            raise ValueError(f"{row['id']}: invalid {scope} plan")
    coords = row.get("coordinates")
    if coords is not None:
        lat, lon = coords["latitude"], coords["longitude"]
        if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError(f"{row['id']}: invalid geographic coordinates")
    if not row.get("title") or not row["source_url"].startswith("https://"):
        raise ValueError("Missing title or source URL")


def project(row, now):
    validate(row)
    p = row["personalization"]
    # Card fields match the app's naming; estimates and full source facts stay explicit.
    return {"id": row["id"], "title": row["title"], "description": (row.get("description") or "")[:1600],
            "description_truncated": len(row.get("description") or "") > 1600,
            "organization": row.get("organization"), "source": row["source"],
            "source_id": row["source_id"], "source_url": row["source_url"], "kind": row["kind"],
            "sample": False, "tags": p["interests"], "goals": p["goals"],
            "skills": row["editorial"]["inferred_skills"], "minutes": p["first_step"]["minutes"],
            "difficulty": p["challenge_levels"][0], "mode": row.get("mode"),
            "color": {"anteater": "yellow", "coursera": "pink", "muse": "blue", "irvine": "green"}.get(row["source"], "green"),
            "location": row.get("location"), "city": row.get("city"), "coordinates": row.get("coordinates"),
            "personalization": p, "suggested_first_step": row["editorial"]["suggested_first_step"],
            "availability": row.get("availability"), "status": status(row, now),
            "source_facts": {key: row[key] for key in ("start", "end", "workload", "units", "prerequisites", "restrictions", "terms", "course_level", "levels", "categories", "languages", "amenities", "miles", "resource_type", "attribution", "official_website", "ticket_availability", "is_free") if key in row},
            "collected_at": row["provenance"]["collected_at"]}


def publish(database=ROOT / "data" / "opportunities.sqlite3", destination=DESTINATION):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    output = destination / "opportunities.json.gz"
    temporary = destination / "opportunities.json.gz.tmp"
    counts = Counter()
    coverage = {key: Counter() for key in ("interests", "goals", "challenge_levels", "time_buckets", "location_preferences")}
    fallback_count = 0
    no_goals = 0
    coordinates_count = 0
    step_coverage = {scope: {"challenge_levels": Counter(), "time_buckets": Counter()} for scope in ("first_step", "micro_step")}
    ids = set()
    samples = []
    sample_sources = Counter()
    included_counts = Counter()
    excluded_counts = Counter()
    exclusion_reasons = Counter()
    connection = sqlite3.connect(database)
    try:
        with temporary.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
            compressed.write(b'{"schema_version":1,"opportunities":[')
            output_index = 0
            for (document,) in connection.execute("SELECT document FROM opportunities ORDER BY source,id"):
                source_row = json.loads(document)
                keep, reason = inclusion(source_row)
                if not keep:
                    excluded_counts[source_row["source"]] += 1
                    exclusion_reasons[reason] += 1
                    continue
                row = project(source_row, now)
                if row["id"] in ids:
                    raise ValueError("Duplicate opportunity ID")
                ids.add(row["id"])
                counts[row["source"]] += 1
                included_counts[row["source"]] += 1
                if sample_sources[row["source"]] < 2:
                    samples.append(row)
                    sample_sources[row["source"]] += 1
                for key in coverage:
                    coverage[key].update(row["personalization"][key])
                fallback_count += row["personalization"]["classification"]["fallback"]
                no_goals += not row["goals"]
                coordinates_count += row.get("coordinates") is not None
                for scope, groups in step_coverage.items():
                    plan = row["personalization"][scope]
                    groups["challenge_levels"].update([plan["challenge_level"]])
                    groups["time_buckets"].update([plan["time_bucket"]])
                encoded = json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                compressed.write((b"," if output_index else b"") + encoded)
                output_index += 1
            compressed.write(b"]}")
        # Read back the full artifact before publishing it.
        with gzip.open(temporary, "rt", encoding="utf-8") as stream:
            payload = json.load(stream)
        if len(payload["opportunities"]) != len(ids):
            raise ValueError("Export read-back count mismatch")
        manifest = {"schema_version": 1, "generated_at": now.isoformat(), "file": output.name,
                    "record_count": len(ids), "by_source": dict(counts), "taxonomy": TAXONOMY,
                    "curation": {"policy_version": "one-thing-relevance-v1",
                                 "included_from_source_counts": dict(included_counts),
                                 "excluded_from_source_counts": dict(excluded_counts),
                                 "exclusion_reasons": dict(exclusion_reasons),
                                 "note": "The app catalog excludes records without evidence of a checklist interest, goal, personal-growth benefit, club/community value, or outdoor/recreation benefit. Raw collected records remain in the local source database."},
                    "coverage": coverage, "broad_fallback_records": fallback_count,
                    "records_without_supported_checklist_goals": no_goals,
                    "coordinate_records": coordinates_count, "step_coverage": step_coverage,
                    "sha256": hashlib.sha256(temporary.read_bytes()).hexdigest(),
                    "bytes": temporary.stat().st_size,
                    "notes": ["Editorial classifications are estimates, not provider-verified facts",
                              "No applicable goal is represented by an empty goals array",
                              "Near me requires user coordinates and excludes records without coordinates",
                              "Time and challenge filters distinguish opportunity vs first_step vs micro_step",
                              "Past events are excluded by the catalog reader unless explicitly requested"]}
        manifest_path = destination / "manifest.json"
        manifest_temporary = manifest_path.with_suffix(".json.tmp")
        manifest_temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, output)
        os.replace(manifest_temporary, manifest_path)
        (destination / "sample.json").write_text(json.dumps({"note": "Small preview, not the full catalog", "opportunities": samples}, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest
    finally:
        connection.close()
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    result = publish()
    print(json.dumps({key: result[key] for key in ("record_count", "by_source", "bytes", "broad_fallback_records")}, indent=2))
