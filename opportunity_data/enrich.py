"""Authored OneThing rubric: estimates are never represented as source facts."""
import hashlib
import re
from datetime import datetime
from .personalize import classify

RUBRIC_VERSION = "one-thing-editorial-v1"
SKILLS = {
    "Coding": r"\b(python|programming|software|javascript|coding|computer science|java|c\+\+)\b",
    "Data analysis": r"\b(data|statistics|analytics|machine learning|statistical)\b",
    "Design": r"\b(design|ux|ui|creative|visual|art)\b",
    "Writing": r"\b(writing|write|literature|journalism|communication)\b",
    "Research": r"\b(research|experiment|laboratory|science|scientific)\b",
    "Business": r"\b(business|finance|accounting|marketing|management|sales)\b",
    "Community": r"\b(community|volunteer|social|service|networking)\b",
    "Sustainability": r"\b(environment|sustainability|ecology|climate|garden)\b",
}


def enrich(facts, overrides=None):
    row = dict(facts)
    if not row.get("title") or not row.get("source_id") or not row.get("source_url", "").startswith("https://"):
        raise ValueError("Missing title, source ID or HTTPS source URL")
    row["id"] = row["source"] + "-" + hashlib.sha256(row["source_id"].encode()).hexdigest()[:20]
    row["sample"] = False
    text = (row["title"] + " " + (row.get("description") or "")).lower()
    skills = [skill for skill, pattern in SKILLS.items() if re.search(pattern, text)]
    level = (row.get("course_level") or "").lower()
    if row["kind"] == "Class":
        difficulty = "Challenging" if "graduate" in level else "Hard" if "upper" in level else "Easy"
        minutes, action = 15, "Read the prerequisites and outline one topic you want to learn."
        basis = "UCI catalog course level; relative academic effort, not an eligibility assessment"
    elif row["kind"] in {"Job", "Internship"}:
        difficulty, minutes = "Hard", 20
        action = "Read the requirements and draft one evidence-backed resume bullet for this role."
        basis = "Application preparation typically involves tailoring materials; estimated by OneThing"
    elif row["kind"] == "Online course":
        difficulty = "Challenging" if re.search(r"\b(advanced|deep learning|graduate)\b", row["title"].lower()) else "Easy"
        if difficulty == "Easy" and re.search(r"\b(machine learning|neural|predictive|calculus|linear algebra|algorithms)\b", row["title"].lower()):
            difficulty = "Hard"
        minutes, action = 10, "Review the syllabus and choose one lesson to try."
        basis = "Title keyword rubric; provider difficulty was not supplied by this catalog endpoint"
    elif row["kind"] in {"Trail", "Park", "Sports facility"}:
        difficulty, minutes = "Medium", 10
        action = "Check official access and hours, choose a suitable route or activity, and make a short preparation plan."
        basis = "Estimated planning effort only; terrain, accessibility, closures and physical difficulty are not assessed"
    else:
        difficulty, minutes = "Easy", 5
        action = "Review the event, check eligibility, and write one question to bring."
        basis = "Low-effort event preparation; event participation may take substantially longer"
    row["editorial"] = {
        "rubric_version": RUBRIC_VERSION, "author": "OneThing assistant-authored rubric",
        "difficulty": difficulty, "difficulty_is_estimate": True, "difficulty_basis": basis,
        "suggested_first_step": action, "first_step_minutes": minutes,
        "first_step_minutes_is_estimate": True, "inferred_skills": skills,
        "skills_basis": "Keyword matches in title and description; not provider-verified",
        "suggested_goals": ["Build my skills", "Explore my interests"],
        "length_note": "First-step time is not total course, job, internship or event duration",
    }
    # Total workload remains the exact provider text; missing lengths are explicitly unknown.
    row["duration"] = {"source_workload_text": row.get("workload"),
                       "source_start": row.get("start"), "source_end": row.get("end"),
                       "total_minutes": None,
                       "note": "See source workload or dates; total minutes not inferred"}
    start = row.get("start")
    end = row.get("end")
    if isinstance(start, dict):
        start = start.get("utc")
    if isinstance(end, dict):
        end = end.get("utc")
    if isinstance(start, str) and isinstance(end, str) and "T" in start and "T" in end:
        try:
            start_time = datetime.fromisoformat(start)
            end_time = datetime.fromisoformat(end)
            minutes = (end_time - start_time).total_seconds() / 60
            if minutes >= 0:
                row["duration"]["total_minutes"] = minutes
                row["duration"]["note"] = "Calculated from source start/end; not an editorial estimate"
            collected = datetime.fromisoformat(row["provenance"]["collected_at"])
            if end_time.tzinfo is not None:
                row["event_timing_at_collection"] = "past" if end_time < collected else "upcoming_or_in_progress"
        except (ValueError, TypeError):
            pass  # Keep original source dates; no guessed conversion.
    if overrides and row["id"] in overrides:
        override = overrides[row["id"]]
        if not override.get("reason"):
            raise ValueError("Editorial overrides require a reason")
        for key in ("difficulty", "first_step_minutes", "suggested_first_step", "inferred_skills"):
            if key in override:
                row["editorial"][key] = override[key]
        row["editorial"]["override_reason"] = override["reason"]
    editorial = row["editorial"]
    if editorial["difficulty"] not in {"Lazy", "Easy", "Medium", "Hard", "Challenging"}:
        raise ValueError("Invalid editorial difficulty")
    if type(editorial["first_step_minutes"]) is not int or not 1 <= editorial["first_step_minutes"] <= 120:
        raise ValueError("First-step estimate must be 1-120 integer minutes")
    if not isinstance(editorial["inferred_skills"], list) or any(not isinstance(s, str) for s in editorial["inferred_skills"]):
        raise ValueError("Editorial skills must be a list of strings")
    row["personalization"] = classify(row)
    return row
