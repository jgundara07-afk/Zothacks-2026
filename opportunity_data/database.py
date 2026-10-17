"""Separate catalog database. Never mutates demo profiles, seeds or activity."""
import json
import sqlite3
from contextlib import closing


class Catalog:
    def __init__(self, path):
        self.path = path
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        with closing(self.connect()) as connection, connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY, source TEXT NOT NULL, source_id TEXT NOT NULL,
                source_url TEXT NOT NULL, title TEXT NOT NULL, kind TEXT NOT NULL,
                collected_at TEXT NOT NULL, document TEXT NOT NULL,
                UNIQUE(source, source_id), UNIQUE(source, source_url))''')
            connection.execute("CREATE INDEX IF NOT EXISTS source_idx ON opportunities(source)")
            connection.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, document TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path)

    def put(self, row):
        with self.connection as connection:
            existing = connection.execute(
                "SELECT id, document FROM opportunities WHERE source=? AND (source_id=? OR source_url=?)",
                (row["source"], row["source_id"], row["source_url"])).fetchone()
            if existing:
                old = json.loads(existing[1])
                # A brief detail page must not erase richer calendar/API facts.
                if row.get("collection_method") == "Public event HTML" and old.get("start"):
                    return
                row["id"] = existing[0]
                connection.execute("DELETE FROM opportunities WHERE id=?", (existing[0],))
            connection.execute("INSERT INTO opportunities VALUES (?,?,?,?,?,?,?,?)", (
                row["id"], row["source"], row["source_id"], row["source_url"], row["title"],
                row["kind"], row["provenance"]["collected_at"], json.dumps(row, ensure_ascii=False)))

    def stats(self):
        with closing(self.connect()) as connection:
            return dict(connection.execute("SELECT source, count(*) FROM opportunities GROUP BY source"))

    def export(self, path):
        with closing(self.connect()) as connection, open(path, "w", encoding="utf-8") as stream:
            stream.write('{"opportunities":[')
            for index, (document,) in enumerate(connection.execute("SELECT document FROM opportunities ORDER BY source,id")):
                stream.write(("," if index else "") + document)
            stream.write("]}\n")

    def save_run(self, report):
        with closing(self.connect()) as connection, connection:
            connection.execute("INSERT OR REPLACE INTO runs VALUES (?,?)", (report["id"], json.dumps(report)))

    def close(self):
        self.connection.close()
