"""Offline Core safety tests; no protected datasets or provider calls."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from implicit import Implicit
from implicit.accounting import Accounting
from implicit.adapters.toy import components
from implicit.completion import CompletionTransaction
from implicit.content import DirectoryContentStore, payload_hash
from implicit.materialization import PagedState
from implicit.models import (
    Address,
    Event,
    Execution,
    LogicalExperience,
    MaterializationPlan,
    Region,
    ResourceKey,
    VerificationResult,
)
from implicit.residency import ResidencyCache
from implicit.storage import MemoryStore, SQLiteEventStore


def test_same_source_version_different_experiences_do_not_share_pages():
    class Source:
        version = "shared"

        def __init__(self, value):
            self.value = value

        def load(self, key):
            return {"value": self.value}

        def dependencies(self, key, value):
            return ()

    cache = ResidencyCache(10000)
    for coordinate in ("a", "b", "a"):
        exp = LogicalExperience(Address("world", "1", coordinate, Region("world", "all")), "read")
        pager = PagedState(
            MaterializationPlan(exp, (), "shared"),
            Source(coordinate),
            cache,
            Accounting(),
            lambda *args: None,
        )
        assert pager.read(ResourceKey("data", "same")) == {"value": coordinate}
        pager.finish()


@pytest.mark.parametrize("position", range(1, 61))
@pytest.mark.parametrize("after", [False, True])
@pytest.mark.parametrize("persistent", [False, True])
def test_every_journal_boundary_fails_without_reexecution(tmp_path, position, after, persistent):
    base = SQLiteEventStore(tmp_path / "journal.db") if persistent else MemoryStore()

    class Interrupted:
        calls = 0

        def append(self, event):
            self.calls += 1
            if self.calls == position and not after:
                raise OSError("simulated disk-full")
            base.append(event)
            if self.calls == position and after:
                raise OSError("simulated process loss after commit")

        def __getattr__(self, name):
            return getattr(base, name)

    from implicit import LocalTransport
    from implicit.engine import Engine

    agent, environment, evaluator = components()
    native_calls = []
    original = environment.execute

    def execute(*args):
        native_calls.append(1)
        return original(*args)

    environment.execute = execute
    engine = Engine(store=Interrupted())
    session = Implicit(transport=LocalTransport(engine)).connect(
        agent=agent, environment=environment, evaluator=evaluator
    )
    try:
        result = session.explore(episodes=1)
        assert len(result.episodes) == 1
    except OSError:
        with pytest.raises(RuntimeError, match="recovery"):
            session.explore(episodes=1)
    assert len(native_calls) <= 1
    records = base.events(session.session_id)
    assert [e.sequence for e in records] == list(range(1, len(records) + 1))


@pytest.mark.parametrize("mode", ["record", "manifest", "truncate", "sequence", "future"])
def test_corrupt_journal_refuses_success(tmp_path, mode):
    p = tmp_path / "journal.db"
    store = SQLiteEventStore(p)
    store.create_session("s", {})
    store.append(Event("s", 1, "example", {}))
    with sqlite3.connect(p) as db:
        if mode == "record":
            db.execute("UPDATE product_events SET record='{}'")
        elif mode == "manifest":
            db.execute("UPDATE product_sessions SET manifest='[]'")
        elif mode == "truncate":
            db.execute("DELETE FROM product_events")
        elif mode == "sequence":
            db.execute("UPDATE product_events SET sequence=2")
        else:
            db.execute("PRAGMA user_version=999")
    with pytest.raises(ValueError):
        SQLiteEventStore(p).events("s")


def test_legacy_migration_is_atomic_and_retryable(tmp_path):
    p = tmp_path / "legacy.db"
    with sqlite3.connect(p) as db:
        db.executescript(
            "CREATE TABLE product_sessions(id TEXT PRIMARY KEY,manifest TEXT NOT NULL); CREATE TABLE product_events(session TEXT,sequence INTEGER,kind TEXT,address TEXT,record TEXT,PRIMARY KEY(session,sequence));"
        )
        db.execute("INSERT INTO product_sessions VALUES ('s','{}')")
        db.execute("INSERT INTO product_events VALUES ('s',1,'old',NULL,'invalid')")
    with pytest.raises(ValueError):
        SQLiteEventStore(p)
    with sqlite3.connect(p) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 0
        assert "manifest_hash" not in {r[1] for r in db.execute("PRAGMA table_info(product_sessions)")}
        raw = json.dumps({"session_id": "s", "sequence": 1, "kind": "old", "payload": {}})
        db.execute("UPDATE product_events SET record=?", (raw,))
    assert SQLiteEventStore(p).events("s")[0].schema_version == 1
    assert SQLiteEventStore(p).events("s")[0].kind == "old"


@pytest.mark.parametrize("index", range(64))
def test_completion_recovery_never_calls_native_execution(tmp_path, index):
    store = SQLiteEventStore(tmp_path / "complete.db")
    exp = LogicalExperience(Address("world", "1", str(index), Region("world", "all")), "read")
    transaction = CompletionTransaction(store, "receipt", {"case": index})
    transaction.prepare(exp, Execution(exp.address, {"writes": 1}))

    def failure(*args):
        raise PermissionError("interrupted evaluator")

    with pytest.raises(PermissionError):
        transaction.verify(failure)
    rebound = CompletionTransaction(SQLiteEventStore(tmp_path / "complete.db"), "receipt", {"case": index})
    assert rebound.verify(lambda *args: VerificationResult(1, True, "fixture")).passed
    with pytest.raises(ValueError, match="immutable"):
        rebound.verify(lambda *args: None)


def test_concurrent_separate_sessions_shared_database(tmp_path):
    p = tmp_path / "concurrent.db"
    SQLiteEventStore(p)

    def work(seed):
        agent, env, evaluator = components()
        session = Implicit(database=p).connect(agent=agent, environment=env, evaluator=evaluator)
        result = session.explore(episodes=10, seed=seed)
        session.close()
        assert len(result.episodes) == 10
        return session.session_id

    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(work, range(16)))
    assert len(set(ids)) == 16
    for sid in ids:
        events = SQLiteEventStore(p).events(sid)
        assert all(e.session_id == sid for e in events)


def test_content_paths_and_hashes_refuse_malicious_input(tmp_path):
    store = DirectoryContentStore(tmp_path / "content")
    for digest in ("../../secret", "/absolute", "a" * 31, "z" * 32):
        with pytest.raises(ValueError):
            store.get(digest)
    data = b'{"safe":1}'
    digest = payload_hash(data)
    assert store.put(digest, data)
    (tmp_path / "content" / (digest + ".json")).write_bytes(b"corrupt")
    with pytest.raises(ValueError):
        store.get(digest)


def test_adapter_exception_secret_is_not_recorded():
    agent, environment, evaluator = components()

    def fail(*args):
        raise RuntimeError("secret-value-should-never-be-recorded")

    environment.execute = fail
    session = Implicit().connect(agent=agent, environment=environment, evaluator=evaluator)
    with pytest.raises(RuntimeError):
        session.explore(episodes=1)
    assert "secret-value-should-never-be-recorded" not in repr(session.events())


def test_corrupt_index_is_rejected_and_source_is_preserved(tmp_path):
    from implicit.adapters.indexed_db import IndexedDBSource

    source = tmp_path / "source.json"
    source.write_text('{"rows":{"one":{"value":1}}}', encoding="utf8")
    index = tmp_path / "index.db"
    compiled = IndexedDBSource.compile(source, index)
    assert compiled.load(ResourceKey("rows", "one")) == {"value": 1}
    with sqlite3.connect(index) as db:
        db.execute("UPDATE records SET value='{}'")
    with pytest.raises(ValueError, match="checksum"):
        compiled.load(ResourceKey("rows", "one"))
    assert source.read_text() == '{"rows":{"one":{"value":1}}}'


def test_symlink_content_cannot_read_outside_directory(tmp_path):
    import os

    data = b'{"safe":1}'
    digest = payload_hash(data)
    outside = tmp_path / "outside.json"
    outside.write_bytes(data)
    store = DirectoryContentStore(tmp_path / "content")
    target = tmp_path / "content" / (digest + ".json")
    try:
        os.symlink(outside, target)
    except OSError:
        pytest.skip("OS denies symlink creation; Linux CI covers this case")
    with pytest.raises(ValueError, match="symlink"):
        store.get(digest)


@pytest.mark.parametrize(
    "mode", ["source_exception", "opaque", "missing", "cycle", "adapter_exception", "malformed", "serialize"]
)
def test_adapter_lifecycle_failures_never_complete(mode):
    agent, environment, evaluator = components()
    original_source = environment.source
    if mode in {"adapter_exception", "malformed", "serialize"}:

        def execute(*args):
            if mode == "adapter_exception":
                raise PermissionError("resource denied")
            if mode == "malformed":
                return None
            return Execution(args[1].address, {"opaque": object()})

        environment.execute = execute
    else:

        def source(exp):
            value = original_source(exp)

            def load(key):
                if mode == "source_exception":
                    raise OSError("partial source failure")
                if mode == "missing":
                    raise KeyError(key)
                if mode == "opaque":
                    return object()
                return {}

            value.load = load
            if mode == "cycle":
                value.dependencies = lambda key, value: (key,)
            return value

        environment.source = source
    session = Implicit().connect(agent=agent, environment=environment, evaluator=evaluator)
    with pytest.raises((OSError, TypeError, KeyError, ValueError, AttributeError)):
        session.explore(episodes=1)
    assert not any(e.kind == "episode" for e in session.events())
    with pytest.raises(RuntimeError, match="recovery"):
        session.explore(episodes=1)
