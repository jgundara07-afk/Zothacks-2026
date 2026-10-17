"""Reapply editorial rules to stored facts offline, without fetching or refreshing."""
import argparse
import json
from pathlib import Path

from .database import Catalog
from .enrich import enrich

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--sources", nargs="+")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    path = args.data_dir / "opportunities.sqlite3"
    if not path.exists():
        parser.error("Collect a catalog first")
    catalog = Catalog(path)
    overrides = json.loads((ROOT / "editorial_overrides.json").read_text(encoding="utf-8"))
    # Materialize IDs/documents before writing, avoiding a long-lived reader lock.
    rows = catalog.connection.execute("SELECT document FROM opportunities").fetchall()
    count = 0
    for (document,) in rows:
        row = json.loads(document)
        if args.sources and row["source"] not in args.sources:
            continue
        catalog.put(enrich(row, overrides))
        count += 1
    if args.export:
        catalog.export(args.data_dir / "opportunities.json")
    catalog.close()
    print(f"Refined {count} stored records offline; no source requests made.")


if __name__ == "__main__":
    main()
