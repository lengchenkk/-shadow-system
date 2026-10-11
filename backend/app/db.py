"""SQLite 存储层。"""
import json
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("SHADOW_DB", os.path.join(os.path.dirname(__file__), "..", "shadow.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '猎人',
    accepted INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    streak INTEGER NOT NULL DEFAULT 0,
    last_study_date TEXT,
    attr_points INTEGER NOT NULL DEFAULT 0,
    attrs TEXT NOT NULL DEFAULT '{"str":0,"agi":0,"int":0,"vit":0,"sen":0}',
    title TEXT,
    boost_date TEXT,
    penalty_pending INTEGER NOT NULL DEFAULT 0,
    shield_week TEXT,
    beru_week TEXT,
    last_tick_date TEXT,
    quests_completed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    cards TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    minutes INTEGER NOT NULL DEFAULT 0,
    problems INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    base_points INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    comment TEXT,
    breakdown TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS army (soldier_id TEXT PRIMARY KEY, count INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS daily_quests (
    date TEXT PRIMARY KEY,
    objectives TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS gates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rank TEXT NOT NULL,
    exam_date TEXT,
    cleared INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS gate_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gate_id INTEGER NOT NULL REFERENCES gates(id) ON DELETE CASCADE,
    idx INTEGER NOT NULL,
    name TEXT NOT NULL,
    is_boss INTEGER NOT NULL DEFAULT 0,
    cleared INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS chests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tier TEXT NOT NULL,
    source TEXT,
    opened INTEGER NOT NULL DEFAULT 0,
    content TEXT
);
CREATE TABLE IF NOT EXISTS achievements (id TEXT PRIMARY KEY, unlocked_at TEXT NOT NULL);
INSERT OR IGNORE INTO player (id) VALUES (1);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def tx():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init():
    with tx() as c:
        c.executescript(SCHEMA)


def get_setting(c, key, default=None):
    r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r["value"] if r else default


def set_setting(c, key, value):
    c.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def player(c):
    p = dict(c.execute("SELECT * FROM player WHERE id=1").fetchone())
    p["attrs"] = json.loads(p["attrs"])
    return p


def update_player(c, **fields):
    if "attrs" in fields and not isinstance(fields["attrs"], str):
        fields["attrs"] = json.dumps(fields["attrs"])
    sets = ", ".join(f"{k}=?" for k in fields)
    c.execute(f"UPDATE player SET {sets} WHERE id=1", tuple(fields.values()))
