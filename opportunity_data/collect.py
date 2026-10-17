"""Manual CLI: gather once, normalize, enrich and persist. No scheduler or refresh hook."""
import argparse
import json
import uuid
from pathlib import Path

from dotenv import load_dotenv

from .database import Catalog
from .enrich import enrich
from .http import Fetcher, utcnow
from .sources import ADAPTERS

ROOT = Path(__file__).resolve().parent


def main():
    load_dotenv(ROOT.parent / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="+", choices=ADAPTERS, default=[source for source in ADAPTERS if source != "anteater"])
    parser.add_argument("--max-pages", type=int, default=500, help="Per-source pagination safety budget")
    parser.add_argument("--muse-pages", type=int, default=400, help="Total category-page request budget, 20 rows/page; respect hourly caps across runs")
    parser.add_argument("--delay", type=float, default=0.25, help="Minimum seconds between requests")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--export", action="store_true", help="Also export the entire persistent catalog to JSON")
    args = parser.parse_args()
    if args.max_pages < 1 or args.muse_pages < 1 or args.delay < 0:
        parser.error("Page limits must be positive and delay nonnegative")
    args.data_dir.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    fetcher = Fetcher(args.data_dir / "raw" / run_id, args.delay)
    catalog = Catalog(args.data_dir / "opportunities.sqlite3")
    overrides = json.loads((ROOT / "editorial_overrides.json").read_text(encoding="utf-8"))
    report = {"id": run_id, "started_at": utcnow(), "automatic_refresh": False,
              "selection": "No UCI classes; direct checklist-topic Coursera courses; relevant Muse Entry Level and Internship roles; beneficial public ZotSpot/Eventbrite events and official City of Irvine recreation places",
              "sources": {}}
    for name in args.sources:
        count = 0
        excluded = 0
        errors = []
        print(f"Collecting {name} ...", flush=True)
        state = "complete"
        try:
            budget = min(args.max_pages, args.muse_pages) if name == "muse" else args.max_pages
            for facts in ADAPTERS[name](fetcher, budget):
                try:
                    retained = catalog.put(enrich(facts, overrides))
                    excluded += retained is False
                    count += 1
                    if count % 500 == 0:
                        print(f"  {name}: {count} records processed", flush=True)
                except (ValueError, KeyError, TypeError) as error:
                    errors.append({"source_id": str(facts.get("source_id")), "error": str(error)})
        except Exception as error:
            state = "partial" if count else "unavailable"
            errors.append({"error": str(error)})
        if errors and state == "complete":
            state = "partial"
        report["sources"][name] = {"status": state, "records_processed": count, "excluded_by_relevance": excluded, "errors": errors}
        print(f"{name}: {state}, {count} records, {len(errors)} errors", flush=True)
        # Persist progress even if a later source fails or the process is interrupted.
        report["counts"] = catalog.stats()
        (args.data_dir / "latest_run.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["finished_at"] = utcnow()
    report["requests"] = len(fetcher.receipts)
    report["counts"] = catalog.stats()
    catalog.save_run(report)
    (args.data_dir / "latest_run.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.export:
        catalog.export(args.data_dir / "opportunities.json")
    catalog.close()
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
