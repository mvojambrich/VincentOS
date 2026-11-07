"""SQLite storage with ordered, hash-linked telemetry events.

Hash links make accidental modification detectable in this local reference
runtime. They do not make a local SQLite database tamper-proof.
"""

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class RuntimeStore:
    def __init__(self, database_path: str | None = None) -> None:
        self.path = Path(database_path or os.getenv("VINCENTOS_DB_PATH", "data/vincentos.db"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _add_column_if_missing(connection: sqlite3.Connection, table: str, definition: str) -> None:
        name = definition.split()[0]
        existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
        if name not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS contexts (
                    context_id TEXT PRIMARY KEY, node_id TEXT NOT NULL, input_payload TEXT NOT NULL,
                    metadata_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    runtime_state TEXT NOT NULL DEFAULT 'ACTIVE'
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, context_id TEXT NOT NULL, stage TEXT NOT NULL,
                    data_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(context_id) REFERENCES contexts(context_id)
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, context_id TEXT, event TEXT NOT NULL,
                    detail_json TEXT NOT NULL, timestamp TEXT NOT NULL,
                    event_id TEXT, sequence_number INTEGER, actor TEXT, reason TEXT,
                    previous_hash TEXT, event_hash TEXT
                );
            """)
            self._add_column_if_missing(connection, "contexts", "runtime_state TEXT NOT NULL DEFAULT 'ACTIVE'")
            for definition in ("event_id TEXT", "sequence_number INTEGER", "actor TEXT", "reason TEXT", "previous_hash TEXT", "event_hash TEXT"):
                self._add_column_if_missing(connection, "audit_events", definition)

    def create_context(self, context: Dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute("INSERT INTO contexts (context_id, node_id, input_payload, metadata_json, created_at) VALUES (?, ?, ?, ?, ?)", (context["context_id"], context["node_id"], context["input_payload"], json.dumps(context["metadata"]), context["created_at"]))

    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM contexts WHERE context_id = ?", (context_id,)).fetchone()
            if row is None:
                return None
            snapshots = connection.execute("SELECT stage, data_json FROM snapshots WHERE context_id = ? ORDER BY id", (context_id,)).fetchall()
        return {"context_id": row["context_id"], "node_id": row["node_id"], "input_payload": row["input_payload"], "metadata": json.loads(row["metadata_json"]), "created_at": row["created_at"], "runtime_state": row["runtime_state"], "snapshots": [{"stage": item["stage"], "data": json.loads(item["data_json"])} for item in snapshots]}

    def add_snapshot(self, context_id: str, stage: str, data: Dict[str, Any], created_at: str) -> None:
        with self._connect() as connection:
            connection.execute("INSERT INTO snapshots (context_id, stage, data_json, created_at) VALUES (?, ?, ?, ?)", (context_id, stage, json.dumps(data), created_at))

    def set_runtime_state(self, context_id: str, state: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE contexts SET runtime_state = ? WHERE context_id = ?", (state, context_id))

    @staticmethod
    def _redact(payload: Dict[str, Any]) -> Dict[str, Any]:
        secret_keys = {"password", "secret", "token", "api_key"}
        return {key: "[REDACTED]" if key.lower() in secret_keys else value for key, value in payload.items()}

    def add_audit_event(self, context_id: str | None, event: str, detail: Dict[str, Any], timestamp: str, actor: str = "runtime", reason: str = "") -> Dict[str, Any]:
        safe_detail = self._redact(detail)
        with self._connect() as connection:
            previous = connection.execute("SELECT event_hash, sequence_number FROM audit_events ORDER BY id DESC LIMIT 1").fetchone()
            previous_hash = previous["event_hash"] if previous and previous["event_hash"] else "GENESIS"
            sequence = (previous["sequence_number"] or 0) + 1 if previous else 1
            event_id = f"evt-{uuid4()}"
            envelope = {"event_id": event_id, "sequence_number": sequence, "context_id": context_id, "event": event, "actor": actor, "reason": reason, "timestamp": timestamp, "detail": safe_detail, "previous_hash": previous_hash}
            event_hash = hashlib.sha256(json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            connection.execute("INSERT INTO audit_events (context_id, event, detail_json, timestamp, event_id, sequence_number, actor, reason, previous_hash, event_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (context_id, event, json.dumps(safe_detail), timestamp, event_id, sequence, actor, reason, previous_hash, event_hash))
        return {**envelope, "event_hash": event_hash}

    def audit_events(self, context_id: str | None = None) -> List[Dict[str, Any]]:
        query, params = "SELECT context_id, event, detail_json, timestamp, event_id, sequence_number, actor, reason, previous_hash, event_hash FROM audit_events", ()
        if context_id:
            query += " WHERE context_id = ?"
            params = (context_id,)
        query += " ORDER BY id"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [{"context_id": row["context_id"], "event": row["event"], "detail": json.loads(row["detail_json"]), "timestamp": row["timestamp"], "event_id": row["event_id"], "sequence_number": row["sequence_number"], "actor": row["actor"], "reason": row["reason"], "previous_hash": row["previous_hash"], "event_hash": row["event_hash"]} for row in rows]

