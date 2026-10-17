"""Audit the stored catalog and write a consolidated report; never contacts sources."""
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    path = ROOT / "data" / "opportunities.sqlite3"
    if not path.exists():
        raise SystemExit("Collect a catalog first")
    connection = sqlite3.connect(path)
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    counts = dict(connection.execute("SELECT source,count(*) FROM opportunities GROUP BY source"))
    problems = []
    timing = Counter()
    reviewed = 0
    for record_id, document in connection.execute("SELECT id,document FROM opportunities"):
        row = json.loads(document)
        editorial = row.get("editorial", {})
        if not row.get("title") or not row.get("source_url", "").startswith("https://"):
            problems.append({"id": record_id, "issue": "Missing title or source URL"})
        if editorial.get("difficulty") not in {"Lazy", "Easy", "Medium", "Hard", "Challenging"}:
            problems.append({"id": record_id, "issue": "Invalid difficulty"})
        if not editorial.get("difficulty_is_estimate") or not editorial.get("first_step_minutes_is_estimate"):
            problems.append({"id": record_id, "issue": "Unlabeled estimate"})
        if not row.get("provenance", {}).get("collected_at"):
            problems.append({"id": record_id, "issue": "Missing collection timestamp"})
        if row.get("sample") is not False:
            problems.append({"id": record_id, "issue": "Unexpected fictional sample in real-source catalog"})
        if row.get("event_timing_at_collection"):
            timing[row["event_timing_at_collection"]] += 1
        reviewed += bool(editorial.get("override_reason"))
    source_reports = {}
    runs = [json.loads(document) for (document,) in connection.execute("SELECT document FROM runs")]
    for run in sorted(runs, key=lambda r: r["started_at"]):
        for source, report in run["sources"].items():
            source_reports[source] = dict(report, run_id=run["id"], collected_at=run.get("finished_at"))
            if report["errors"] and report["status"] == "complete":
                source_reports[source]["status"] = "partial"
    export_path = ROOT / "data" / "opportunities.json"
    exported = None
    if export_path.exists():
        with export_path.open(encoding="utf-8") as stream:
            exported = len(json.load(stream)["opportunities"])
        if exported != sum(counts.values()):
            problems.append({"issue": "JSON export count differs from database"})
    report = {"audited_at": datetime.now(timezone.utc).isoformat(),
              "database": "opportunity_data/data/opportunities.sqlite3",
              "json_export": "opportunity_data/data/opportunities.json",
              "total_opportunities": sum(counts.values()), "by_source": counts,
              "export_count": exported, "sqlite_integrity": integrity,
              "validation_issues": problems, "individually_reviewed_estimates": reviewed,
              "event_timing_at_collection": dict(timing), "automatic_refresh": False,
              "latest_source_runs": source_reports,
              "limitations": ["Catalog records are snapshots, not guaranteed available opportunities",
                              "Muse is a bounded category snapshot; global pagination is capped",
                              "Anteater records without titles are excluded",
                              "Eventbrite covers manually discovered public IDs, not global search",
                              "Most difficulty/skill/first-step fields use an authored estimation rubric",
                              "Existing demo feed is not connected to this separate catalog"]}
    output = ROOT / "reports" / "collection-summary.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    connection.close()
    print(json.dumps(report, indent=2))
    if problems or integrity != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
