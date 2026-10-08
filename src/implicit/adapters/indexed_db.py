"""Compile finite external DBs once; resolve serialized records from a versioned disk index."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Iterator, cast

from ..models import JSON, ResourceKey
from ..serialization import canonical


@dataclass(frozen=True, slots=True)
class Compilation:
    source_hash: str
    source_bytes: int
    record_bytes: int
    records: int
    index_bytes: int
    seconds: float


class IndexedDBSource:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._reader: sqlite3.Connection | None = None
        with closing(sqlite3.connect(Path(self.path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(records)")}
            if "checksum" not in columns:
                raise ValueError(
                    "legacy index has no integrity metadata; recompile from intact source to a new path"
                )
            row = db.execute("SELECT value FROM metadata WHERE key=?", ("compilation",)).fetchone()
        if row is None:
            raise ValueError("not an Implicit DB index")
        self.compilation = Compilation(**json.loads(row[0]))
        self.version = self.compilation.source_hash

    @contextmanager
    def read_session(self) -> Iterator[None]:
        """Reuse a read-only, thread-affine connection for a runtime or snapshot scope."""
        if self._reader is not None:
            # sqlite itself enforces thread ownership even for nested scopes.
            self._reader.execute("SELECT 1")
            yield
            return
        with closing(sqlite3.connect(Path(self.path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            self._reader = db
            try:
                yield
            finally:
                self._reader = None

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        with self.read_session():
            assert self._reader is not None
            yield self._reader

    @classmethod
    def compile(cls, source_path: str | Path, index_path: str | Path) -> IndexedDBSource:
        start = perf_counter()
        source_path, index_path = Path(source_path), Path(index_path)
        if source_path.resolve() == index_path.resolve():
            raise ValueError("index must not overwrite source")
        if index_path.exists():
            raise FileExistsError(f"use an existing index or a new path: {index_path}")
        index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = source_path.read_bytes()
        source_hash = hashlib.sha256(payload).hexdigest()
        data = json.loads(payload)
        if not isinstance(data, dict) or any(not isinstance(v, dict) for v in data.values()):
            raise ValueError("supported databases contain top-level record dictionaries")
        records = sum(len(v) for v in data.values())
        record_bytes = 0
        with closing(sqlite3.connect(index_path)) as db, db:
            db.executescript("""
                CREATE TABLE records (namespace TEXT, key TEXT, value TEXT NOT NULL, checksum TEXT NOT NULL,
                                      PRIMARY KEY(namespace,key));
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            for namespace, rows in data.items():
                for key, value in rows.items():
                    # Preserve insertion order: native tools may stop at the first matching row
                    # and serialize dictionaries in their original order.
                    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
                    record_bytes += len(serialized.encode("utf-8"))
                    checksum = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
                    db.execute(
                        "INSERT INTO records VALUES (?, ?, ?, ?)", (namespace, key, serialized, checksum)
                    )
            compilation = Compilation(
                source_hash, len(payload), record_bytes, records, 0, perf_counter() - start
            )
            db.execute("INSERT INTO metadata VALUES (?, ?)", ("compilation", canonical(compilation)))
        # Index metadata reports physical compilation cost including the input parse and writes.
        compilation = Compilation(
            source_hash,
            len(payload),
            record_bytes,
            records,
            index_path.stat().st_size,
            perf_counter() - start,
        )
        with closing(sqlite3.connect(index_path)) as db, db:
            db.execute("UPDATE metadata SET value=? WHERE key=?", (canonical(compilation), "compilation"))
        return cls(index_path)

    def load(self, resource: ResourceKey) -> JSON:
        return self.load_measured(resource)[0]

    def load_measured(self, resource: ResourceKey) -> tuple[JSON, int]:
        with self._connection() as db:
            row = db.execute(
                "SELECT value,checksum FROM records WHERE namespace=? AND key=?",
                (resource.namespace, resource.key),
            ).fetchone()
        if row is None:
            raise KeyError(resource.uri)
        if hashlib.sha256(row[0].encode("utf-8")).hexdigest() != row[1]:
            raise ValueError("indexed resource checksum mismatch")
        return cast(JSON, json.loads(row[0])), len(row[0].encode("utf-8"))

    def dependencies(self, resource: ResourceKey, value: JSON) -> Iterable[ResourceKey]:
        # Native tools discover the actual closure, including writes, scans and new IDs.
        return ()

    def namespaces(self) -> tuple[str, ...]:
        with self._connection() as db:
            return tuple(
                row[0] for row in db.execute("SELECT DISTINCT namespace FROM records ORDER BY namespace")
            )

    def keys(self, namespace: str) -> tuple[str, ...]:
        with self._connection() as db:
            return tuple(
                row[0]
                for row in db.execute(
                    "SELECT key FROM records WHERE namespace=? ORDER BY rowid", (namespace,)
                )
            )

    def contains(self, resource: ResourceKey) -> bool:
        with self._connection() as db:
            return (
                db.execute(
                    "SELECT 1 FROM records WHERE namespace=? AND key=?", (resource.namespace, resource.key)
                ).fetchone()
                is not None
            )
