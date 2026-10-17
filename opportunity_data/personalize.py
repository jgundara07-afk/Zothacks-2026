"""Versioned editorial categorization using the exact OneThing checklist labels."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

TAXONOMY = json.loads((Path(__file__).parent / "taxonomy.json").read_text(encoding="utf-8"))
RULES = {
    "Software Engineering": r"\b(software engineer\w*|software develop\w*|programming|computer science|python|java|c\+\+|coding|algorithms?|devops)\b",
    "AI & Machine Learning": r"\b(artificial intelligence|machine learning|deep learning|neural networks?|generative ai|llms?|large language models?|natural language processing|computer vision|chatgpt|gemini|vertex ai|inteligencia artificial|inteligência artificial|apprentissage automatique|aprendizaje autom[aá]tico)\b|(?-i:\bAI\b)",
    "Web & App Development": r"\b(web develop\w*|app develop\w*|mobile develop\w*|front.?end|back.?end|full.?stack|javascript|typescript|react|django|flask|html|css|android|ios develop\w*)\b",
    "Data Science": r"\b(data scien\w*|data analy\w*|data engineer\w*|statistics|statistical|big data|sql|tableau|power bi|pandas|dataflow|pub/sub|ciência de dados|ciencia de datos|analyse de données|análisis de datos)\b",
    "Cybersecurity": r"\b(cyber.?security|information security|application security|penetration test\w*|ethical hack\w*|cryptography|owasp|network security)\b",
    "Entrepreneurship & Startups": r"\b(entrepreneur\w*|startups?|start.up|founders?|venture capital|business launch|small business|product launch)\b",
    "Hackathons": r"\b(hackathons?|zothacks|hackuci|hack uci|hack nights?)\b",
    "Career Development": r"\b(career|internships?|resume|résumé|interview|job fair|job information|recruit\w*|professional development|job search)\b",
    "Networking & Mentorship": r"\b(networking|mentors?|mentorship|professional connections|informational interview|business mixer)\b",
    "Leadership": r"\b(leadership|team management|leading teams|team leader|lead a team|student leader|public speaking|organizational management)\b",
    "Personal Finance & Investing": r"\b(personal financ\w*|financial literacy|budgeting|investing|investment|retirement planning|wealth management|stock market|trading signals|technical analysis|fibonacci trading)\b",
    "Productivity & Personal Growth": r"\b(productivity|personal growth|time management|self.improvement|study skills|mindfulness|wellbeing|well.being|goal setting|learning strategies)\b",
    "Design & UI/UX": r"\b(ui/ux|ux|user experience|user interface|graphic design|product design|figma|wirefram\w*|interaction design|design thinking)\b",
    "Hike": r"\b(hike|hikes|hiking|hikers?|trail|trails|backpacking|trekking|outdoor adventure)\b",
    "Sports": r"\b(sports?|soccer|basketball|baseball|volleyball|tennis|pickleball|badminton|athletic\w*|swimming|fitness|softball|disc golf|ice rink|skating)\b",
}
TECHNICAL = {"Software Engineering", "AI & Machine Learning", "Web & App Development", "Data Science", "Cybersecurity", "Design & UI/UX"}


def bucket(minutes, multi_day=False):
    if multi_day or minutes >= 1440:
        return "Multi-day"
    for limit, label in [(5, "Under 5 min"), (15, "5–15 min"), (30, "15–30 min"), (60, "30–60 min"), (180, "1–3 hours")]:
        if minutes < limit:
            return label
    return "3+ hours"


def length(row):
    """Prefer known event duration. Unknown values use labeled planning estimates."""
    actual = row.get("duration", {}).get("total_minutes")
    if actual is not None and actual > 0:
        return {"minutes": actual, "bucket": bucket(actual), "estimated": False,
                "basis": "Difference between source start and end timestamps"}
    workload = str(row.get("workload") or "")
    # Only an unambiguous, single-session English hour/minute expression is converted.
    if workload and re.fullmatch(r"\s*(?:\d+(?:\.\d+)?\s*hours?\s*)?(?:\d+\s*minutes?\s*)?", workload, re.I):
        hours = re.search(r"(\d+(?:\.\d+)?)\s*hours?", workload, re.I)
        mins = re.search(r"(\d+)\s*minutes?", workload, re.I)
        total = (float(hours[1]) * 60 if hours else 0) + (int(mins[1]) if mins else 0)
        if total:
            return {"minutes": total, "bucket": bucket(total), "estimated": False,
                    "basis": "Provider-reported single-session workload: " + workload}
    if row["kind"] in {"Class", "Job", "Internship", "Online course"}:
        # A course may be shorter; this is explicitly an estimate, not fabricated workload.
        return {"minutes": None, "bucket": "Multi-day", "estimated": True,
                "basis": "Planning assumption for education/employment when exact total effort is unavailable; source workload: " + (workload or "unknown")}
    minutes = 60 if row["kind"] == "Trail" else 45 if row["kind"] in {"Park", "Sports facility"} else 90
    return {"minutes": minutes, "bucket": bucket(minutes), "estimated": True,
            "basis": "OneThing planning estimate for one visit/session; not provider-reported duration"}


def classify(row):
    text = " ".join(str(row.get(key) or "") for key in ("title", "description", "department"))
    text += " " + " ".join(row.get("categories", []) + row.get("amenities", []))
    interests, evidence = [], {}
    for label, pattern in RULES.items():
        match = re.search(pattern, text, re.I)
        if match:
            interests.append(label)
            evidence[label] = match[0]
    kind = row["kind"]
    if kind in {"Job", "Internship", "Networking event"} and "Career Development" not in interests:
        interests.append("Career Development")
        evidence["Career Development"] = "Employment/networking source category"
    if kind == "Trail" and "Hike" not in interests:
        interests.append("Hike")
        evidence["Hike"] = "Official City of Irvine mapped public-trail layer"
    if kind == "Sports facility" and "Sports" not in interests:
        interests.append("Sports")
        evidence["Sports"] = "Official City of Irvine recreation facility"
    if not interests:
        interests = ["Productivity & Personal Growth"]
        evidence[interests[0]] = "Broad personal exploration fallback; no specific checklist topic detected"
    interests.sort(key=TAXONOMY["interests"].index)
    goals = []
    def goal(index, condition):
        if condition:
            goals.append(TAXONOMY["goals"][index])
    technical = bool(TECHNICAL.intersection(interests))
    goal(0, "Software Engineering" in interests and kind in {"Job", "Internship", "Class", "Online course"})
    goal(1, technical and (kind in {"Class", "Online course"} or bool(re.search(r"\b(project|portfolio|hackathon)\b", text, re.I))))
    goal(2, technical and kind not in {"Park", "Trail", "Sports facility"})
    goal(3, "Hackathons" in interests)
    goal(4, technical and kind in {"Campus event", "Club"} and bool(re.search(r"\b(club|student organization|student society)\b", text, re.I)))
    goal(5, "Networking & Mentorship" in interests or kind == "Networking event")
    goal(6, "Entrepreneurship & Startups" in interests or "Web & App Development" in interests and kind in {"Class", "Online course"})
    goal(7, kind in {"Job", "Internship"} or bool(re.search(r"\b(resume|résumé|interview|career fair|job fair)\b", text, re.I)))
    goal(8, "Leadership" in interests)
    goal(9, "Hike" in interests or kind in {"Trail", "Park"})
    if kind in {"Trail", "Park", "Sports facility"}:
        challenge, challenge_basis = "Medium", "Estimated effort for a self-paced outdoor/recreation visit; terrain and accessibility unknown"
    elif row.get("course_level") and "Lower" in row["course_level"]:
        challenge, challenge_basis = "Medium", "Estimated relative effort for lower-division academic work"
    elif re.search(r"\b(intermediate|moderate)\b", row.get("title", ""), re.I):
        challenge, challenge_basis = "Medium", "Intermediate/moderate title wording"
    else:
        challenge, challenge_basis = row["editorial"]["difficulty"], row["editorial"]["difficulty_basis"]
    duration = length(row)
    mode = row.get("mode")
    locations = []
    location_basis = []
    if mode == "Online":
        locations.append("Online / Remote")
        location_basis.append("Source delivery-mode or explicit remote location")
    location_text = str(row.get("location") or "")
    explicit_campus = bool(re.search(r"\b(uci|uc irvine|university of california.? irvine|student center|student services|aldrich|langson|anteater recreation|engineering hall)\b", location_text, re.I))
    if row["source"] == "anteater" and mode != "Online" or explicit_campus and mode != "Online":
        locations.append("On campus")
        location_basis.append("UCI catalog affiliation or explicit campus venue; class delivery must be checked")
    physical_event = kind in {"Campus event", "Networking event"} and mode == "Local"
    if kind == "Campus event" and mode is None and location_text and not re.search(r"sign in|private|tbd|to be|online|zoom|https?://", location_text, re.I):
        physical_event = True
    if physical_event:
        locations.append("In-person events")
        location_basis.append("Source reports a physical event")
    # Near me is calculated at query time from real coordinates, never attached globally.
    commitment = TAXONOMY["commitment_preferences"][1 if duration["bucket"] == "Multi-day" or kind in {"Job", "Internship", "Class"} else 0]
    first = row["editorial"]["first_step_minutes"]
    return {"taxonomy_version": TAXONOMY["version"], "interests": interests, "goals": goals,
            "challenge_levels": [challenge], "time_buckets": [duration["bucket"]],
            "location_preferences": locations, "commitment": commitment,
            "first_step": {"minutes": first, "time_bucket": bucket(first),
                           "challenge_level": "Lazy" if first < 5 else "Easy" if first <= 15 else "Medium",
                           "commitment": TAXONOMY["commitment_preferences"][0]},
            "micro_step": {"minutes": 2, "time_bucket": "Under 5 min", "challenge_level": "Lazy",
                           "commitment": TAXONOMY["commitment_preferences"][0],
                           "action": "Open the source, check whether this opportunity suits you, and write one question or next step."},
            "duration": duration, "classification": {"method": "Assistant-authored evidence rules; estimates require source verification",
                "interest_evidence": evidence, "fallback": "fallback" in next(iter(evidence.values()), "").lower(),
                "goal_basis": "Inferred relevance to the listed topics and opportunity type; not promised outcomes",
                "challenge_is_estimate": True, "challenge_basis": challenge_basis,
                "location_basis": location_basis, "location_is_inferred": "On campus" in locations}}


def status(row, now=None):
    now = now or datetime.now(timezone.utc)
    end = row.get("end")
    if isinstance(end, dict):
        end = end.get("utc")
    if isinstance(end, str) and "T" in end:
        try:
            date = datetime.fromisoformat(end)
            if date.tzinfo and date < now:
                return "past"
        except ValueError:
            pass
    if row.get("source_open_flag") == 0:
        return "access_unconfirmed"
    return "verify_at_source"
