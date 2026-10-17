"""Assistant-authored, evidence-based effort estimates; no provider calls.

Difficulty measures learning/participation complexity, independently of duration.
We never allocate levels randomly or relabel records just to fill a quota.
"""
import re
import json
from pathlib import Path

VERSION = "onething-effort-v2"
LEVELS = ["Lazy", "Easy", "Medium", "Hard", "Challenging"]
FILTER_OPTIONS = json.loads((Path(__file__).resolve().parents[1] / "shared" / "catalog_filters.json").read_text(encoding="utf-8"))


def hit(pattern, text):
    match = re.search(pattern, text, re.I)
    return match[0] if match else None


def assess(row, duration):
    """Assign each record a level and explicit evidence; honor reviewed overrides."""
    if row.get('kind')=='General task' and row.get('general_task'):
        task=row['general_task'];requirements=task.get('requirements',[])
        return dict(version=VERSION,difficulty=task['difficulty'],difficulty_basis='User-supplied task difficulty; independent of duration',difficulty_is_estimate=True,
                    review_method='User-supplied general task with authored time and accessible alternatives',experience_level='No experience',experience_is_estimate=True,
                    experience_basis='Self-guided general activity; see requirements',prerequisite_status='Required' if requirements else 'None stated',prerequisite_basis='; '.join(requirements) or 'No specific prerequisite stated',
                    cost='Free',cost_basis='Self-guided activity using existing/free tools; paid subscriptions not required',duration_quality='Estimated',languages=['en'],
                    eligibility_text='; '.join(requirements) or None,eligibility_verified=False,registration_required=False,schedule_type='Self-paced')
    title = row.get("title", "")
    text = title + " " + (row.get("description") or "")
    kind = row["kind"]
    academic = row.get("course_level") or ""
    advanced = hit(r"\b(advanced|avanzad[oa]s?|avanc[eé]s?|avan[cç]ad[oa]s?|expert|doctoral|phd|dissertation|thesis|research scientist|"
                   r"reinforcement learning|distributed systems|deep learning|neural networks)\b", title)
    intro = hit(r"\b(introduction|introductory|introducci[oó]n|introdu[cç][aã]o|fundamentos|principiantes|d[eé]butants?|beginner|beginners|fundamentals|basics|"
                r"foundations|getting started|101|literacy|essentials)\b", title)
    applied = hit(r"\b(implement\w*|build\w*|develop\w*|"
                  r"programming|analysis|analytics|engineering|security|machine learning|"
                  r"algorithms?|optimiz\w*|deploy\w*|architecture|llms?|"
                  r"devops|linux|splunk|kubernetes|terraform|neural|cryptography)\b", title)
    guided = hit(r"\b(guided|step.by.step|self.paced lab|hands.on lab|walkthrough)\b", text)
    prerequisite = str(row.get("prerequisites") or "").strip()
    none_stated = hit(r"\b(no (?:prior |technical |programming )?(?:experience|knowledge|prerequisites)|"
                      r"no programming experience|no experience required|anyone can)\b", text)
    declared_requirement = hit(r"\b(?:learners should have|you should have|requires? (?:prior |basic |working )?knowledge of|"
                               r"prior experience (?:with|in)|prerequisites? include)\b[^.!?\n]{0,180}", text)
    if not prerequisite and declared_requirement and not none_stated:
        prerequisite = declared_requirement
    required = prerequisite and not re.fullmatch(r"(?:none|n/?a|no prerequisites)[.!]?", prerequisite, re.I)
    if required:
        pre_status, pre_basis = "Required", prerequisite
    elif none_stated or prerequisite:
        pre_status, pre_basis = "None stated", none_stated or prerequisite
    else:
        pre_status, pre_basis = "Unknown", "Provider did not explicitly report prerequisites"

    if kind == "Class":
        if "Graduate" in academic:
            difficulty, reason = ("Challenging", academic)
        elif "Upper" in academic:
            difficulty, reason = ("Hard", academic)
        elif intro and not required:
            difficulty, reason = "Easy", "Introductory lower-division course: " + intro
        else:
            difficulty, reason = "Medium", "Lower-division academic work; " + ("source prerequisites apply" if required else "prior knowledge not confirmed")
    elif kind in {"Job", "Internship"}:
        difficulty = "Challenging" if advanced else "Hard" if kind == "Job" else "Medium"
        reason = "Employment responsibilities, not application preparation; " + (advanced or "internship learning role" if kind == "Internship" else advanced or "professional job role")
    elif kind == "Trail":
        difficulty, reason = "Medium", "Planning estimate only: mapped segment distance is not whole-route difficulty; terrain/access unknown"
    elif kind in {"Park", "Sports facility"}:
        difficulty, reason = ("Lazy", "Optional self-paced park visit; no performance target") if kind == "Park" else ("Easy", "Self-paced recreation, intensity chosen by participant")
    elif kind in {"Campus event", "Networking event", "Club"}:
        if hit(r"\b(hackathon|competition|tournament)\b", title):
            difficulty, reason = "Hard", "Competitive participation named in title"
        elif hit(r"\b(workshop|training|practice|bootcamp)\b", title):
            difficulty, reason = "Medium" if applied else "Easy", "Active learning/practice event"
        else:
            difficulty, reason = "Lazy", "Attend/listen/connect without an assessed deliverable; eligibility still requires verification"
    elif advanced:
        difficulty, reason = "Challenging", "Advanced topic in title: " + advanced
    elif intro:
        difficulty, reason = ("Easy" if not applied else "Medium"), "Introductory title: " + intro + ("; applied technical practice" if applied else "")
    elif guided and not required:
        short = duration.get("max_minutes") is not None and duration["max_minutes"] <= 180
        difficulty, reason = ("Medium" if applied else "Lazy" if short else "Easy"), "Guided source activity: " + guided + ("; applied technical topic" if applied else "; bounded low-barrier session" if short else "; longer or unverified total effort")
    elif applied:
        difficulty, reason = "Hard", "Independent/applied technical topic: " + applied
    elif hit(r"\b(personal|communication|presentation|leadership|teamwork|writing|"
             r"wellness|mindfulness|nutrition|productivity|time management|"
             r"career|resume|interview|creativity|storytelling|english|language|"
             r"business|finance|marketing)\b", title) and not required:
        difficulty, reason = "Easy", "Accessible professional/personal skill development; no verified prerequisite barrier, level remains estimated"
    else:
        difficulty, reason = "Medium", "General learning activity; incomplete level information, conservative editorial estimate"
    editorial = row.get("editorial", {})
    if editorial.get("override_reason"):
        difficulty, reason = editorial["difficulty"], editorial["override_reason"]

    experience = "No experience" if none_stated else "Beginner" if intro and not required else "Advanced" if advanced or "Graduate" in academic else "Intermediate" if required or difficulty == "Hard" else "Unknown"
    if row.get("is_free") is True:
        cost, cost_basis = "Free", "Provider is_free=true"
    elif row.get("is_free") is False:
        cost, cost_basis = "Paid", "Provider is_free=false"
    else:
        cost, cost_basis = "Unknown", "No verified price; public listing/free preview does not prove free participation"
    return {"version": VERSION, "difficulty": difficulty, "difficulty_basis": reason,
            "difficulty_is_estimate": True, "review_method": "Assistant-authored per-record evidence rubric with explicit reviewed overrides; not individual manual review of every listing",
            "experience_level": experience, "experience_is_estimate": True,
            "experience_basis": none_stated or (intro if intro and not required else None) or advanced or academic or pre_basis,
            "prerequisite_status": pre_status, "prerequisite_basis": pre_basis,
            "cost": cost, "cost_basis": cost_basis,
            "duration_quality": duration.get("quality", "Estimated" if duration["estimated"] else "Source reported"),
            "languages": row.get("languages") or [],
            "eligibility_text": row.get("restrictions") or None,
            "eligibility_verified": False, "registration_required": None,
            "schedule_type": "Ongoing" if kind in {"Job", "Internship"} else "Academic term" if kind == "Class" else "Scheduled" if row.get("start") else "Self-paced" if kind in {"Online course", "Park", "Trail", "Sports facility"} else "Unknown"}
