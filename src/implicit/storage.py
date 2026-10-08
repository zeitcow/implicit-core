"""Append-only session journal; all lifecycle records are stored as typed event payloads."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing, contextmanager
from copy import deepcopy
from pathlib import Path
from typing import ContextManager, Iterator, Protocol

from .models import JSON, Event
from .serialization import canonical


class EventStore(Protocol):
    def create_session(self, session_id: str, manifest: JSON) -> None: ...
    def append(self, event: Event) -> None: ...
    def events(self, session_id: str, *, after_sequence: int = 0) -> tuple[Event, ...]: ...
    def manifest(self, session_id: str) -> JSON: ...
    def lease(self, session_id: str) -> ContextManager[None]: ...


class MemoryStore:
    def __init__(self) -> None:
        self._manifests: dict[str, JSON] = {}
        self._events: dict[str, list[Event]] = {}
        self._leases: set[str] = set()

    @contextmanager
    def lease(self, session_id: str) -> Iterator[None]:
        if session_id in self._leases:
            raise RuntimeError("session has an active runtime owner")
        self._leases.add(session_id)
        try:
            yield
        finally:
            self._leases.remove(session_id)

    def create_session(self, session_id: str, manifest: JSON) -> None:
        if session_id in self._manifests:
            raise ValueError("session already exists")
        self._manifests[session_id] = deepcopy(manifest)
        self._events[session_id] = []

    def append(self, event: Event) -> None:
        events = self._events[event.session_id]
        if event.sequence != len(events) + 1:
            raise ValueError("events must append in sequence")
        events.append(deepcopy(event))

    def events(self, session_id: str, *, after_sequence: int = 0) -> tuple[Event, ...]:
        if after_sequence < 0:
            raise ValueError("sequence cursor must be nonnegative")
        return tuple(deepcopy(self._events[session_id][after_sequence:]))

    def manifest(self, session_id: str) -> JSON:
        return deepcopy(self._manifests[session_id])


class SQLiteEventStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._writer: sqlite3.Connection | None = None
        if self.path == ":memory:":
            raise ValueError("use MemoryStore for memory storage")
        if Path(path).is_symlink():
            raise ValueError("journal file must not be a symlink")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=30)) as db, db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in {0, 1}:
                raise ValueError("unsupported journal schema; use a compatible release")
            # FULL durability, with WAL avoiding repeated main-file rollback-journal churn.
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS product_sessions (
                    id TEXT PRIMARY KEY, manifest TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS product_events (
                    session TEXT NOT NULL REFERENCES product_sessions(id),
                    sequence INTEGER NOT NULL, kind TEXT NOT NULL,
                    address TEXT, record TEXT NOT NULL,
                    PRIMARY KEY(session, sequence));
                CREATE INDEX IF NOT EXISTS product_event_address
                    ON product_events(session, address, kind);
            """)
            if version == 0:
                db.execute("BEGIN IMMEDIATE")
            columns = {row[1] for row in db.execute("PRAGMA table_info(product_sessions)")}
            if "last_sequence" not in columns:
                db.execute("ALTER TABLE product_sessions ADD COLUMN last_sequence INTEGER NOT NULL DEFAULT 0")
                db.execute("""UPDATE product_sessions SET last_sequence=(
                    SELECT COALESCE(MAX(sequence),0) FROM product_events WHERE session=product_sessions.id)
                """)
            # Schema 0 -> 1 is transactional. A failed migration leaves the old data intact.
            if version == 0:
                db.execute("ALTER TABLE product_sessions ADD COLUMN manifest_hash TEXT")
                db.execute("ALTER TABLE product_events ADD COLUMN record_hash TEXT")
                for sid, raw in db.execute("SELECT id,manifest FROM product_sessions").fetchall():
                    json.loads(raw)
                    db.execute("UPDATE product_sessions SET manifest_hash=? WHERE id=?", (_hash(raw), sid))
                for sid, sequence, raw in db.execute(
                    "SELECT session,sequence,record FROM product_events"
                ).fetchall():
                    record = json.loads(raw)
                    if record.get("session_id") != sid or record.get("sequence") != sequence:
                        raise ValueError("legacy journal identity mismatch; migration refused")
                    if record.get("schema_version", 1) not in {1, 2}:
                        raise ValueError("unsupported legacy event schema")
                    db.execute(
                        "UPDATE product_events SET record_hash=? WHERE session=? AND sequence=?",
                        (_hash(raw), sid, sequence),
                    )
                for sid, last in db.execute("SELECT id,last_sequence FROM product_sessions").fetchall():
                    count, maximum = db.execute(
                        "SELECT COUNT(*),COALESCE(MAX(sequence),0) FROM product_events WHERE session=?",
                        (sid,),
                    ).fetchone()
                    if count != last or maximum != last:
                        raise ValueError("legacy journal sequence gap; migration refused")
                db.execute("PRAGMA user_version=1")

    @contextmanager
    def lease(self, session_id: str) -> Iterator[None]:
        """OS-released advisory ownership across external calls, including process crashes."""
        suffix = hashlib.sha256(session_id.encode()).hexdigest()[:24]
        path = Path(self.path).resolve().with_name(Path(self.path).name + "." + suffix + ".lock")
        if path.is_symlink():
            raise ValueError("session lock must not be a symlink")
        with path.open("a+b") as lock:
            if path.stat().st_size == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[attr-defined]  # Unix-only API
            except OSError as exc:
                raise RuntimeError("session has an active runtime owner") from exc
            try:
                yield
            finally:
                lock.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]  # Unix-only API

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self._writer is not None:
            yield self._writer
        else:
            with closing(sqlite3.connect(self.path, timeout=30)) as db:
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("PRAGMA synchronous=FULL")
                yield db

    @contextmanager
    def write_session(self) -> Iterator[None]:
        """Reuse one thread-affine connection; every append still commits durably.

        No transaction is deferred until episode completion, including failure evidence.
        Idle stores own no connection, so Windows files can be moved after an operation.
        """
        if self._writer is not None:
            raise RuntimeError("overlapping SQLite write sessions are unsupported")
        with closing(sqlite3.connect(self.path, timeout=30)) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=FULL")
            self._writer = db
            try:
                yield
            finally:
                self._writer = None

    def create_session(self, session_id: str, manifest: JSON) -> None:
        with self._connection() as db, db:
            db.execute(
                "INSERT INTO product_sessions(id,manifest,manifest_hash) VALUES (?, ?, ?)",
                (session_id, canonical(manifest), _hash(canonical(manifest))),
            )

    def append(self, event: Event) -> None:
        with self._connection() as db, db:
            changed = db.execute(
                "UPDATE product_sessions SET last_sequence=? WHERE id=? AND last_sequence=?",
                (event.sequence, event.session_id, event.sequence - 1),
            ).rowcount
            if changed != 1:
                raise ValueError("events must append in sequence")
            db.execute(
                "INSERT INTO product_events(session,sequence,kind,address,record,record_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event.session_id,
                    event.sequence,
                    event.kind,
                    event.address,
                    canonical(event),
                    _hash(canonical(event)),
                ),
            )

    def events(self, session_id: str, *, after_sequence: int = 0) -> tuple[Event, ...]:
        if after_sequence < 0:
            raise ValueError("sequence cursor must be nonnegative")
        self.manifest(session_id)
        with self._connection() as db, db:
            # Keep sequence metadata and records in one WAL read snapshot.
            if not db.in_transaction:
                db.execute("BEGIN")
            last = db.execute(
                "SELECT last_sequence FROM product_sessions WHERE id=?", (session_id,)
            ).fetchone()[0]
            count, maximum = db.execute(
                "SELECT COUNT(*),COALESCE(MAX(sequence),0) FROM product_events WHERE session=?", (session_id,)
            ).fetchone()
            if count != last or maximum != last:
                raise ValueError("journal sequence gap or truncation")
            rows = db.execute(
                "SELECT record,record_hash,sequence,kind,address FROM product_events WHERE session=? AND sequence>? ORDER BY sequence",
                (session_id, after_sequence),
            ).fetchall()
        events = []
        for row in rows:
            if _hash(row[0]) != row[1]:
                raise ValueError("journal checksum mismatch")
            record = json.loads(row[0])
            if (
                record.get("session_id") != session_id
                or record.get("sequence") != row[2]
                or record.get("kind") != row[3]
                or record.get("address") != row[4]
            ):
                raise ValueError("journal record identity mismatch")
            record.setdefault("schema_version", 1)
            events.append(Event(**record))
        return tuple(events)

    def manifest(self, session_id: str) -> JSON:
        with self._connection() as db:
            row = db.execute(
                "SELECT manifest,manifest_hash FROM product_sessions WHERE id=?", (session_id,)
            ).fetchone()
        if row is None:
            raise KeyError(session_id)
        if _hash(row[0]) != row[1]:
            raise ValueError("journal manifest checksum mismatch")
        return json.loads(row[0])


def _hash(record: str) -> str:
    return hashlib.sha256(record.encode("utf-8")).hexdigest()
