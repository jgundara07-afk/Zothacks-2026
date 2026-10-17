"""Parse bounded workload evidence, preserve unknowns and label planning ranges."""
import re


def parse_workload(value):
    text = str(value or "").strip().lower().replace("–", "-").replace("—", "-")
    text = re.sub(r"(?<=\d),(?=\d)", ".", text)
    # Only convert supported units. Unsupported language/text remains unknown.
    text = re.sub(r"\b(heures?|horas?|stunden?|hrs?|hr)\b", "hours", text)
    text = re.sub(r"\b(minutos?|minuten?|mins?)\b", "minutes", text)
    text = re.sub(r"\b(semaines?|semanas?|wochen?)\b", "weeks", text)
    text = re.sub(r"\b(d[ií]as?|jours?|tage?)\b", "days", text)
    number = r"(\d+(?:\.\d+)?)(?:\s*(?:-|to|a)\s*(\d+(?:\.\d+)?))?"
    weeks = re.search(number + r"\s*weeks?", text)
    days = re.search(number + r"\s*days?", text)
    hours = re.search(number + r"\s*hours?", text)
    minutes = re.search(number + r"\s*minutes?", text)
    weekly = bool(re.search(r"/\s*(week|semana|semaine)|per week|a week|por semana|par semaine|pro woche|weekly", text))
    daily = bool(re.search(r"/\s*day|per day|a day", text))
    def bounds(match, factor=1):
        return (float(match[1]) * factor, float(match[2] or match[1]) * factor) if match else (0, 0)
    low_h, high_h = bounds(hours, 60)
    low_m, high_m = bounds(minutes)
    lower, upper = low_h + low_m, high_h + high_m
    if weekly and not weeks or daily and not days:
        return None  # Weekly effort without week count is not full duration.
    if not lower:
        return None
    if weeks and weekly:
        low, high = bounds(weeks)
        lower, upper = lower * low, upper * high
    elif days and daily:
        low, high = bounds(days)
        lower, upper = lower * low, upper * high
    if upper < lower or upper > 60 * 24 * 365 * 5:
        return None
    return lower, upper, bool(weeks or days), text


def estimate(row, bucket):
    def result(low, high, quality, basis, multi_day=False, scope="Full opportunity"):
        return {"minutes": low if low == high else None, "min_minutes": low, "max_minutes": high,
                "bucket": bucket(high, multi_day) if high is not None else "Multi-day",
                "estimated": quality in {"Estimated", "Unknown"}, "quality": quality,
                "basis": basis, "scope": scope}
    actual = row.get("duration", {}).get("total_minutes")
    if isinstance(actual, (int, float)) and actual > 0:
        return result(actual, actual, "Source reported", "Elapsed time between provider start/end; may include breaks or overnight time", actual >= 1440, "Event elapsed time")
    workload = row.get("workload")
    parsed = parse_workload(workload)
    if parsed:
        low, high, multi, _ = parsed
        return result(low, high, "Source reported" if low == high else "Source range", "Provider workload: " + str(workload) + "; range upper bound used for time filtering", multi, "Total learning effort")
    kind = row["kind"]
    if kind in {"Class", "Job", "Internship"}:
        return result(None, None, "Unknown", "Academic/employment commitment is multi-day; total effort not provided. Do not treat preparation minutes as completion time.")
    title = row.get("title", "")
    text = title + " " + (row.get("description") or "")
    if kind == "Online course":
        if re.search(r"\b(guided project|lab)\b", title, re.I) or re.search(r"^\s*this is a self.paced lab\b|^\s*in this (?:lab|guided project)\b", row.get("description") or "", re.I):
            return result(60, 180, "Estimated", "Authored planning range for a hands-on lab without parseable provider workload; verify before starting")
        if re.search(r"\b(advanced|specialization|professional certificate|capstone)\b", title, re.I):
            return result(1200, 3600, "Estimated", "Authored planning range for advanced/program-level learning; provider workload unverified", True)
        return result(300, 1200, "Estimated", "Authored 5–20 hour planning range for a course with missing/unsupported workload; not provider-verified", True)
    if kind == "Park":
        return result(15, 45, "Estimated", "Optional self-paced visit, excluding travel; not a scheduled activity")
    if kind == "Sports facility":
        return result(30, 90, "Estimated", "Self-paced recreation session, excluding travel and booking")
    if kind == "Trail":
        # GIS records are segments, so never infer route duration from segment miles.
        return result(30, 90, "Estimated", "Optional walking-session planning range; mapped segment is not a complete route, terrain/access unknown")
    return result(60, 120, "Estimated", "Authored event planning range; source did not provide a usable start/end pair")
