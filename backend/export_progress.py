"""Export the configured shared demo's progress; never changes activity or seeds data."""
import argparse
import json
from pathlib import Path
try:
    from .app import create_app
except ImportError:
    from app import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='data/progress.json')
    parser.add_argument('--date', help='Analytics anchor in YYYY-MM-DD; does not change demo clock')
    args = parser.parse_args()
    # Catalog mode avoids rewriting sample seed records during a read-only export.
    app = create_app(data_mode='catalog')
    response = app.test_client().get('/progress/data', query_string={'date': args.date} if args.date else {})
    if response.status_code != 200:
        parser.error(response.json.get('error', 'Export failed'))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(response.json, indent=2) + '\n', encoding='utf-8')
    print(f'Progress exported to {output}')


if __name__ == '__main__':
    main()
