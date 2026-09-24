"""Local SQLite storage for synthetic demo sessions only."""
import json
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
from contextlib import contextmanager


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, owner TEXT NOT NULL, created TEXT NOT NULL, case_json TEXT NOT NULL, result_json TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS appointments (id TEXT PRIMARY KEY, owner TEXT NOT NULL, assessment_id TEXT, facility_id TEXT NOT NULL, requested_for TEXT NOT NULL, reason TEXT NOT NULL, status TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL, updated TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS followups (id TEXT PRIMARY KEY, owner TEXT NOT NULL, assessment_id TEXT, task TEXT NOT NULL, due_at TEXT NOT NULL, status TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL, updated TEXT NOT NULL)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, owner, case, result):
        identifier = str(uuid4())
        created = datetime.now(timezone.utc).isoformat()
        # Free text may accidentally contain identifiers; do not persist it.
        safe_case = {k: v for k, v in case.items() if k in {"case_id", "age", "pregnancy_stage", "symptoms", "readings", "location", "provenance"}}
        with self.connect() as db:
            db.execute("INSERT INTO assessments VALUES (?, ?, ?, ?, ?)",
                       (identifier, owner, created, json.dumps(safe_case), json.dumps(result)))
        return {"id": identifier, "created": created, "case": safe_case, "result": result}

    def get(self, owner, identifier):
        with self.connect() as db:
            row = db.execute("SELECT id, created, case_json, result_json FROM assessments WHERE owner=? AND id=?", (owner, identifier)).fetchone()
        return self.decode(row) if row else None

    @staticmethod
    def decode(row):
        return {"id": row[0], "created": row[1], "case": json.loads(row[2]), "result": json.loads(row[3])}

    def history(self, owner):
        with self.connect() as db:
            rows = db.execute("SELECT id, created, case_json, result_json FROM assessments WHERE owner=? ORDER BY created DESC LIMIT 100", (owner,)).fetchall()
        return [self.decode(row) for row in rows]

    def consent(self, owner, identifier, facility_id):
        # Read/modify/write atomically; repeat consent is idempotent.
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT result_json FROM assessments WHERE owner=? AND id=?", (owner, identifier)).fetchone()
            if not row:
                raise LookupError("Assessment not found")
            result = json.loads(row[0])
            if result["referral"]["status"] == "not_prepared":
                raise ValueError("No referral is available for this assessment")
            if facility_id not in {f["facility_id"] for f in result["facilities"]}:
                raise ValueError("Select a facility matched to this assessment")
            if result["referral"]["status"] == "simulated" and result["referral"]["facility_id"] != facility_id:
                raise ValueError("This simulation already has a confirmed facility")
            result["referral"].update(status="simulated", sent=False, facility_id=facility_id)
            result["trace"][-1]["status"] = "simulated"
            db.execute("UPDATE assessments SET result_json=? WHERE owner=? AND id=?", (json.dumps(result), owner, identifier))
        return self.get(owner, identifier)

    def clear(self, owner):
        with self.connect() as db:
            db.execute("DELETE FROM assessments WHERE owner=?", (owner,))

    def create_appointment(self, owner, data):
        return self._create_coordination("appointments", owner, data, "requested")

    def create_followup(self, owner, data):
        return self._create_coordination("followups", owner, data, "open")

    def _create_coordination(self, table, owner, data, status):
        identifier = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if table == "appointments":
            values = (identifier, owner, data.get("assessment_id"), data["facility_id"], data["requested_for"], data["reason"], status, 0, now, now)
            columns = "id, owner, assessment_id, facility_id, requested_for, reason, status, acknowledged, created, updated"
        else:
            values = (identifier, owner, data.get("assessment_id"), data["task"], data["due_at"], status, 0, now, now)
            columns = "id, owner, assessment_id, task, due_at, status, acknowledged, created, updated"
        with self.connect() as db:
            db.execute(f"INSERT INTO {table} ({columns}) VALUES ({','.join('?' for _ in values)})", values)
        return self.get_coordination(table, owner, identifier)

    def get_coordination(self, table, owner, identifier):
        with self.connect() as db:
            row = db.execute(f"SELECT * FROM {table} WHERE owner=? AND id=?", (owner, identifier)).fetchone()
        return self._coordination_row(table, row) if row else None

    def list_coordination(self, table, owner=None):
        with self.connect() as db:
            query = f"SELECT * FROM {table}" + (" WHERE owner=?" if owner else "") + " ORDER BY created DESC"
            rows = db.execute(query, (owner,) if owner else ()).fetchall()
        return [self._coordination_row(table, row) for row in rows]

    def update_coordination(self, table, owner, identifier, status, acknowledged=False):
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute(f"UPDATE {table} SET status=?, acknowledged=?, updated=? WHERE owner=? AND id=?",
                       (status, int(acknowledged), now, owner, identifier))
        return self.get_coordination(table, owner, identifier)

    @staticmethod
    def _coordination_row(table, row):
        if table == "appointments":
            keys = ["id", "owner", "assessment_id", "facility_id", "requested_for", "reason", "status", "acknowledged", "created", "updated"]
        else:
            keys = ["id", "owner", "assessment_id", "task", "due_at", "status", "acknowledged", "created", "updated"]
        result = dict(zip(keys, row))
        result["acknowledged"] = bool(result["acknowledged"])
        return result
