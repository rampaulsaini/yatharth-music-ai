"""Durable resilience primitives for Yatharth Music AI.

The module deliberately uses only the Python standard library so it can run in
free/local/production environments without introducing another service.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("YATHARTH_STATE_DB", Path(__file__).with_name("data") / "yatharth_state.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_lock = threading.RLock()

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_state() -> None:
    with _lock, _connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
          task_id TEXT PRIMARY KEY,
          client_id TEXT NOT NULL,
          request_json TEXT NOT NULL,
          status TEXT NOT NULL,
          progress INTEGER NOT NULL DEFAULT 0,
          audio_url TEXT,
          metadata_json TEXT NOT NULL DEFAULT '{}',
          error TEXT,
          created REAL NOT NULL,
          updated REAL NOT NULL,
          engine_task_id TEXT,
          engine_file TEXT,
          engine_provider TEXT,
          attempts INTEGER NOT NULL DEFAULT 0,
          next_attempt REAL NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status_next ON tasks(status, next_attempt);
        try:
            db.execute("ALTER TABLE tasks ADD COLUMN engine_provider TEXT")
        except sqlite3.OperationalError:
            pass
        CREATE TABLE IF NOT EXISTS provider_health (
          provider TEXT PRIMARY KEY,
          ok INTEGER NOT NULL DEFAULT 0,
          last_check REAL NOT NULL DEFAULT 0,
          failures INTEGER NOT NULL DEFAULT 0,
          last_error TEXT
        );
        """)

def save_task(task: Any) -> None:
    now = time.time()
    with _lock, _connect() as db:
        db.execute(
          """INSERT INTO tasks(task_id,client_id,request_json,status,progress,audio_url,metadata_json,error,created,updated,engine_task_id,engine_file,engine_provider,attempts,next_attempt)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
             ON CONFLICT(task_id) DO UPDATE SET client_id=excluded.client_id,request_json=excluded.request_json,status=excluded.status,
             progress=excluded.progress,audio_url=excluded.audio_url,metadata_json=excluded.metadata_json,error=excluded.error,
             updated=excluded.updated,engine_task_id=excluded.engine_task_id,engine_file=excluded.engine_file,engine_provider=excluded.engine_provider,attempts=excluded.attempts,next_attempt=excluded.next_attempt""",
          (task.id, task.client_id, task.request.model_dump_json(), task.status, task.progress, task.audio_url,
           json.dumps(task.metadata, ensure_ascii=False), task.error, task.created, now, task.engine_task_id,
           task.engine_file, getattr(task, "attempts", 0), getattr(task, "next_attempt", 0)),
        )

def load_tasks() -> list[dict[str, Any]]:
    init_state()
    with _lock, _connect() as db:
        rows = db.execute("SELECT * FROM tasks ORDER BY created DESC").fetchall()
    return [dict(row) for row in rows]

def delete_task(task_id: str) -> None:
    with _lock, _connect() as db:
        db.execute("DELETE FROM tasks WHERE task_id=?", (task_id,))

def mark_provider(provider: str, ok: bool, error: str | None = None) -> None:
    with _lock, _connect() as db:
        db.execute(
          """INSERT INTO provider_health(provider,ok,last_check,failures,last_error) VALUES(?,?,?,?,?)
             ON CONFLICT(provider) DO UPDATE SET ok=excluded.ok,last_check=excluded.last_check,
             failures=CASE WHEN excluded.ok=1 THEN 0 ELSE provider_health.failures+1 END,last_error=excluded.last_error""",
          (provider, int(ok), time.time(), 0 if ok else 1, error),
        )

def provider_snapshot(provider: str = "ace-step") -> dict[str, Any]:
    init_state()
    with _lock, _connect() as db:
        row = db.execute("SELECT * FROM provider_health WHERE provider=?", (provider,)).fetchone()
    return dict(row) if row else {"provider": provider, "ok": False, "last_check": 0, "failures": 0, "last_error": "never_checked"}

def recover_inflight() -> int:
    """Make interrupted processing jobs eligible for retry after a process restart."""
    init_state()
    now = time.time()
    with _lock, _connect() as db:
        cur = db.execute(
          "UPDATE tasks SET status='queued', error='Recovered after service restart', updated=?, next_attempt=? WHERE status IN ('processing','waiting_engine')",
          (now, now),
        )
    return cur.rowcount
