import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from pymongo import MongoClient, UpdateOne

ROOT = Path(__file__).resolve().parent

class Store:
    """Document storage: MongoDB when a URI is given, otherwise a local SQLite file with the same collections."""
    def __init__(self, uri=None, path=None):
        self.mongo = None
        if uri:
            self.mongo = MongoClient(uri, serverSelectionTimeoutMS=3000)[os.getenv('MONGO_DB', 'one_thing')]
            self.mongo.command('ping')
        else:
            self.path = str(path or ROOT / 'demo.sqlite3')
            with self.connection() as con:
                con.execute('CREATE TABLE IF NOT EXISTS documents (collection TEXT, id TEXT, data TEXT, PRIMARY KEY(collection,id))')
    @contextmanager
    def connection(self):
        con = sqlite3.connect(self.path, timeout=10)
        try:
            with con:
                yield con
        finally:
            con.close()
    def all(self, collection):
        if self.mongo is not None:
            return list(self.mongo[collection].find({}, {'_id': 0}))
        with self.connection() as con:
            return [json.loads(row[0]) for row in con.execute('SELECT data FROM documents WHERE collection=?', (collection,))]
    def get(self, collection, document_id):
        if self.mongo is not None:
            return self.mongo[collection].find_one({'_id': document_id}, {'_id': 0})
        with self.connection() as con:
            row = con.execute('SELECT data FROM documents WHERE collection=? AND id=?', (collection, document_id)).fetchone()
            return json.loads(row[0]) if row else None
    def put_many(self, collection, documents):
        if self.mongo is not None:
            if documents:
                self.mongo[collection].bulk_write([UpdateOne({'_id':doc['id']}, {'$set':doc}, upsert=True) for doc in documents])
        else:
            with self.connection() as con:
                con.executemany('INSERT OR REPLACE INTO documents VALUES (?,?,?)',
                                [(collection,doc['id'],json.dumps(doc)) for doc in documents])
    def put(self, collection, doc, once=False):
        if self.mongo is not None:
            result = self.mongo[collection].update_one({'_id':doc['id']}, {'$setOnInsert' if once else '$set':doc}, upsert=True)
            return result.upserted_id is not None
        with self.connection() as con:
            sql = 'INSERT OR IGNORE' if once else 'INSERT OR REPLACE'
            return con.execute(f'{sql} INTO documents VALUES (?,?,?)', (collection,doc['id'],json.dumps(doc))).rowcount == 1

    def delete(self, collection, document_id):
        if self.mongo is not None:
            self.mongo[collection].delete_one({'_id': document_id})
        else:
            with self.connection() as con:
                con.execute('DELETE FROM documents WHERE collection=? AND id=?', (collection, document_id))
