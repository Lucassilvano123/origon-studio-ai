import sqlite3, json
from datetime import datetime, timezone
from contextlib import contextmanager
from .config import DB_PATH

def now(): return datetime.now(timezone.utc).isoformat()
@contextmanager
def connect():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; conn.execute('PRAGMA foreign_keys=ON')
    try: yield conn; conn.commit()
    finally: conn.close()

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT DEFAULT 'Outros', description TEXT DEFAULT '', benefits TEXT DEFAULT '', audience TEXT DEFAULT '', source_url TEXT DEFAULT '', price TEXT DEFAULT '', status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL, name TEXT NOT NULL, platform TEXT DEFAULT 'shopee', mode TEXT DEFAULT 'assisted', duration INTEGER DEFAULT 15, versions INTEGER DEFAULT 3, language TEXT DEFAULT 'pt-BR', status TEXT DEFAULT 'draft', settings_json TEXT DEFAULT '{}', created_at TEXT, updated_at TEXT, FOREIGN KEY(product_id) REFERENCES products(id));
        CREATE TABLE IF NOT EXISTS versions(id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL, ordinal INTEGER, strategy TEXT, hook TEXT, script_json TEXT, creative_json TEXT, status TEXT DEFAULT 'draft', output_path TEXT DEFAULT '', created_at TEXT, updated_at TEXT, FOREIGN KEY(project_id) REFERENCES projects(id));
        CREATE TABLE IF NOT EXISTS batches(id INTEGER PRIMARY KEY, name TEXT NOT NULL, status TEXT DEFAULT 'draft', product_ids_json TEXT DEFAULT '[]', versions INTEGER DEFAULT 3, progress INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, batch_id INTEGER, project_id INTEGER, version_id INTEGER, status TEXT DEFAULT 'queued', progress INTEGER DEFAULT 0, message TEXT DEFAULT '', created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, entity_type TEXT, entity_id INTEGER, action TEXT, detail_json TEXT DEFAULT '{}', created_at TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS trash(id INTEGER PRIMARY KEY, entity_type TEXT, entity_id INTEGER, payload_json TEXT, deleted_at TEXT);
        """)

def rows(sql,args=()):
    with connect() as c: return [dict(x) for x in c.execute(sql,args).fetchall()]
def one(sql,args=()):
    with connect() as c:
        x=c.execute(sql,args).fetchone(); return dict(x) if x else None
def execute(sql,args=()):
    with connect() as c:
        cur=c.execute(sql,args); return cur.lastrowid

def log(entity_type, entity_id, action, detail=None):
    execute('INSERT INTO history(entity_type,entity_id,action,detail_json,created_at) VALUES(?,?,?,?,?)',(entity_type,entity_id,action,json.dumps(detail or {},ensure_ascii=False),now()))
