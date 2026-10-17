"""Conservative inclusion rules for the OneThing opportunity catalog.

Raw source records remain available locally for review. Only records that match
the app's stated interests/goals or have an explicit personal-benefit exception
are published to the app-readable catalog.
"""
import re

# Online courses need a topic in the title itself, not incidental promotional
# language or the former broad personal-growth fallback. Keep useful technical,
# career, design, finance, wellbeing and outdoor skills without a language quota.
COURSE_TITLE_TOPICS = re.compile(
    r"\b(software|programming|python|java|javascript|typescript|coding|algorithms?|"
    r"data|datos|donn[eé]es|dados|analytics|statistics|statistical|sql|mysql|postgresql|sqlite|mongodb|redis|tableau|power bi|power query|excel|"
    r"computer science|web development|app development|full.stack|front.end|back.end|"
    r"react|django|flask|html\d*|css\d*|sass|android|ios|git|github|devops|linux|"
    r"cloud|aws|azure|docker|kubernetes|terraform|cybersecurity|cyber security|"
    r"information security|network security|cloud security|ethical hacking|"
    r"cryptography|penetration testing|artificial intelligence|machine learning|"
    r"deep learning|neural networks?|generative|llms?|chatgpt|gemini|vertex|"
    r"computer vision|natural language processing|autogen|multi.agent|pytorch|tensorflow|foundation models|inteligencia artificial|"
    r"apprentissage automatique|ciencia de datos|"
    r"entrepreneur\w*|startups?|business model|product management|product manager|product design|"
    r"hackathons?|resume|résumé|interview\w*|job search|career development|"
    r"professional networking|mentorship|mentoring|leadership|people leader|public speaking|"
    r"personal finance|financial literacy|budgeting|investing|investment|stock market|technical analysis|trading signals|"
    r"productivity|personal growth|time management|mindfulness|wellbeing|"
    r"well.being|stress management|study skills|goal setting|"
    r"user experience|user interface|ux|ui|figma|graphic design|design thinking|"
    r"hiking|hike|wilderness|outdoor|fitness|sports|nutrition)\b|(?-i:\bAI\b)|\bc[+#]{1,2}(?!\w)", re.I)


TECHNICAL = re.compile(
    r"\b(software|programming|computer science|coding|python|java|javascript|"
    r"data science|data analytics|machine learning|artificial intelligence|"
    r"cyber.?security|web development|app development|user experience|ui/ux|"
    r"information technology|cloud computing|engineering|robotics|algorithm)\b", re.I)
CAREER_SKILLS = re.compile(
    r"\b(resume|résumé|interview|career|internship|job search|job fair|"
    r"professional development|networking|mentorship|leadership|portfolio|"
    r"entrepreneur|startup|small business|hackathon|public speaking)\b", re.I)
PERSONAL_GROWTH = re.compile(
    r"\b(productivity|time management|mindfulness|well.?being|wellness|"
    r"stress management|personal finance|financial literacy|budgeting|"
    r"communication skills|study skills|learning strategies|nutrition|fitness|"
    r"health promotion|confidence|goal setting|self.?improvement)\b", re.I)
OUTDOOR_OR_SPORT = re.compile(
    r"\b(hike|hiking|trail|trails|park|sports?|soccer|basketball|baseball|"
    r"volleyball|tennis|pickleball|badminton|swimming|fitness|athletic|"
    r"recreation|disc golf|ice rink|skating|running|cycling)\b", re.I)
UNRELATED_CAREER = re.compile(
    r"\b(physician|surgeon|nurse|nursing|medical|healthcare|health care|"
    r"medical assistant|registered nurse|"
    r"lpn|rn\b|anesthetist|dentist|pharmacist|therapist|veterinarian|"
    r"police officer|special agent|law enforcement|military|teaching expertise|"
    r"education expertise|psychology/counseling expertise|"
    r"cake decorator|produce associate|grocery associate|food market associate|"
    r"cafe associate|caf[eé] associate|tire center|backroom associate|"
    r"retail associate|cashier|warehouse associate|rotisserie|prepared food)\b", re.I)
EXCLUDED_TEST = re.compile(r"\b(test course|sample course|dummy course)\b", re.I)


def evidence_text(row):
    """Use title and description for topical relevance, without generic category leakage."""
    parts = [row.get("title", ""), row.get("description", ""), row.get("department", "")]
    parts.extend(row.get("categories", []) or [])
    parts.extend(row.get("amenities", []) or [])
    return " ".join(str(part or "") for part in parts)


def inclusion(row):
    """Return (keep, reason); conservative around jobs and broad academic catalogs."""
    kind = row.get("kind", "")
    text = evidence_text(row)

    if row.get("source") == "anteater":
        return False, "uci_classes_removed_by_request"

    if EXCLUDED_TEST.search(text):
        return False, "test_or_placeholder_record"

    if kind == "Online course":
        match = COURSE_TITLE_TOPICS.search(row.get("title", ""))
        if match:
            return True, "online_course_direct_checklist_title_topic"
        return False, "online_course_without_direct_checklist_title_topic"

    # The explicit user-requested personal-benefit exception: outdoor access and
    # sports/recreation facilities remain useful even without career relevance.
    if kind in {"Park", "Trail", "Sports facility"}:
        return True, "personal_wellbeing_or_recreation"

    if kind in {"Job", "Internship"}:
        # A job's generic career value alone is too broad. Keep roles tied to
        # the app's technical/design/business/leadership interests; omit unrelated
        # professions (including physician roles) even if weak tags match.
        if UNRELATED_CAREER.search(row.get("title", "")):
            return False, "unrelated_profession_or_general_labor"
        title = row.get("title", "")
        role_evidence = re.search(
                r"\b(software|data|cybersecurity|web|app|product|business|"
                r"financial|accounting|marketing|entrepreneur|founder|ux|user experience|"
                r"graphic|research|engineering|engineer|analyst|designer|developer|"
                r"programmer|scientist|technical|technology|it\b|systems|automation|"
                r"mechanical|electrical|civil|environmental|industrial|operations|"
                r"supply chain|project controls|quality|six sigma|sales development)\b", title, re.I)
        if role_evidence:
            return True, "role_matches_selected_career_or_skill_topics"
        return False, "job_or_internship_without_relevant_role_evidence"

    # Classes and online courses must have a recognizable subject, career skill,
    # or personal-growth benefit. The generic fallback tag itself is not evidence.
    if kind in {"Class", "Online course"}:
        if TECHNICAL.search(text) or CAREER_SKILLS.search(text) or PERSONAL_GROWTH.search(text) or re.search(r"\b(english|writing|communication|art|design|leadership|finance|business|entrepreneurship|management|psychology|wellness|health|nutrition|sustainability|climate|environment|ecology|statistics|research|public speaking|language|foreign language)\b", text, re.I):
            return True, "learning_or_personal_growth_topic"
        # Course catalogs often omit a description but provide an authoritative
        # department. Use the department as the subject label, not classifier tags.
        department = str(row.get("department") or "")
        if re.search(r"\b(computer|informatics|information|engineering|data|analytics|business|finance|accounting|economics|marketing|design|art|psychology|education|communication|writing|english|public health|environment|ecology|statistics|mathematics|management|entrepreneur|cyber|game design|film and media)\b", department, re.I):
            return True, "course_in_relevant_academic_department"
        if row.get("source") == "coursera" and row.get("personalization", {}).get("interests", []) != ["Productivity & Personal Growth"]:
            return True, "coursera_specific_checklist_topic"
        # Design can appear as ordinary wording: require a concrete design term.
        if re.search(r"\b(design|graphic arts|visual design|user experience|ux/ui)\b", text, re.I):
            return True, "design_or_creative_skill_topic"
        return False, "course_without_supported_checklist_topic"

    # Campus and networking events may be worthwhile for clubs, belonging,
    # leadership, volunteering, recreation and personal development as well as careers.
    if kind in {"Campus event", "Networking event", "Club"}:
        if TECHNICAL.search(text) or CAREER_SKILLS.search(text) or PERSONAL_GROWTH.search(text) or OUTDOOR_OR_SPORT.search(text):
            return True, "event_or_club_supports_skills_network_wellbeing_or_growth"
        if re.search(r"\b(club|student organization|student society|volunteer|community|"
                     r"garden|gardening|mentor|workshop|support group)\b", text, re.I):
            return True, "club_community_volunteering_or_personal_development"
        if row.get("source") == "zotspot" and row.get("personalization", {}).get("interests", []) != ["Productivity & Personal Growth"]:
            return True, "campus_event_specific_checklist_topic"
        return False, "event_without_supported_benefit_or_topic"

    # Keep explicitly topic-tagged records of any future recognized kind.
    tags = set(row.get("personalization", {}).get("interests", []))
    if tags - {"Productivity & Personal Growth"}:
        return True, "specific_checklist_topic"
    return False, "no_supported_checklist_topic"
