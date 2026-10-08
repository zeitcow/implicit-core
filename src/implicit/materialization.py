"""Progressive dependency paging. A runtime can fault and resume in the same call stack."""

from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Callable

from .accounting import Accounting
from .content import ContentStore, payload_hash
from .interfaces import ResourceSource
from .models import (
    JSON,
    MaterializationEvent,
    MaterializationPlan,
    MaterializedExperience,
    ResidencyEvent,
    ResourceKey,
)
from .residency import ResidencyCache
from .serialization import canonical


class MissingStateError(KeyError):
    """An actual absent source record, distinct from a successfully resolved page fault."""


class DependencyCycleError(ValueError):
    pass


class PagedState:
    def __init__(
        self,
        plan: MaterializationPlan,
        source: ResourceSource,
        cache: ResidencyCache,
        accounting: Accounting,
        emit: Callable[[str, object], None],
        content_store: ContentStore | None = None,
    ) -> None:
        if plan.source_version != source.version:
            raise ValueError("materialization plan/source version mismatch")
        self.plan = plan
        self.source = source
        self.cache = cache
        self.accounting = accounting
        self.emit = emit
        self.content_store = content_store
        self.phase = "initial"
        self.seeds: dict[str, int] = {}
        self._finished = False
        self._deleted: set[ResourceKey] = set()
        self._values: dict[ResourceKey, JSON] = {}
        self._pristine: dict[ResourceKey, JSON] = {}
        self._resolving: set[ResourceKey] = set()
        self._events: list[MaterializationEvent] = []
        self._sizes: dict[ResourceKey, int] = {}

    def _cache_key(self, key: ResourceKey) -> str:
        return canonical(
            (
                self.plan.experience.address.universe,
                self.plan.experience.address.version,
                self.plan.experience.address.coordinate,
                self.plan.source_version,
                key,
            )
        )

    def _residency_event(self, event: ResidencyEvent) -> None:
        self.emit("residency", event)

    def read(self, key: ResourceKey) -> JSON:
        if self.source.version != self.plan.source_version:
            raise ValueError("source version changed during episode")
        if key in self._deleted:
            raise MissingStateError(key.uri)
        self.accounting.add("state_requests")
        if key in self._resolving:
            raise DependencyCycleError(f"cyclic state dependency: {key.uri}")
        if key in self._values:
            self.accounting.add("resident_hits")
            return self._values[key]
        if self.phase != "initial":
            self.accounting.add("page_faults")
            self.emit("page_fault", {"resource": key, "phase": self.phase})
        self._resolving.add(key)
        start = perf_counter()
        try:
            hit, value = self.cache.get(self._cache_key(key), self.accounting, self._residency_event)
            if not hit:
                self.accounting.add("source_loads")
                try:
                    with self.accounting.time("source_load"):
                        value = deepcopy(self.source.load(key))
                        if self.source.version != self.plan.source_version:
                            raise ValueError("source version changed during load")
                finally:
                    self.accounting.cost("materialization", None)
                self.emit(
                    "residency",
                    ResidencyEvent(
                        self._cache_key(key), "rematerialize", 0, "not resident; resolve from source"
                    ),
                )
            # Validate source values at the adapter boundary; refuse opaque handles.
            payload = canonical(value).encode("utf-8")
            size = len(payload)
            digest = payload_hash(payload)
            pristine = deepcopy(value)
            if key not in self._sizes:
                self.accounting.add("unique_resources_resolved")
                self.accounting.add("runtime_working_set_bytes", size)
            self._sizes[key] = size
            self.accounting.add("runtime_cache_served_bytes" if hit else "runtime_source_loaded_bytes", size)
            if not hit:
                self.accounting.add("newly_materialized_bytes", size)
                self.accounting.add("newly_materialized_resources")
            self.accounting.add("resources_materialized")
            self.accounting.add("materialized_bytes", size)
            if self.phase != "initial":
                self.accounting.add("progressive_bytes", size)
            self._pristine[key] = pristine
            event = MaterializationEvent(
                self.plan.experience.address,
                key,
                digest,
                size,
                perf_counter() - start,
                hit,
                self.phase,
                self.source.version,
            )
            self._events.append(event)
            if self.content_store is not None:
                with self.accounting.time("content_persistence"):
                    written = self.content_store.put(digest, payload)
                self.accounting.add("retained_content_bytes", size if written else 0)
            self.emit(
                "materialization", {"measurement": event, "content_retained": self.content_store is not None}
            )
            # Record provenance even if resolving a later dependency fails.
            for dependency in self.source.dependencies(key, value):
                self.read(dependency)
            self._values[key] = value
            return value
        except MissingStateError:
            raise
        except KeyError as exc:
            self.accounting.add("missing_state_faults")
            self.emit(
                "missing_state", {"resource": key, "error": "resource unavailable", "phase": self.phase}
            )
            raise MissingStateError(key.uri) from exc
        finally:
            self._resolving.remove(key)
            # Nested inclusive timings remain in events; central load time is exclusive at source.
            self.accounting.add("page_resolution_seconds", perf_counter() - start)

    def write(self, key: ResourceKey, value: JSON) -> None:
        """Create or replace an episode-local resource; pristine cache stays unchanged."""
        payload = canonical(value)
        self.emit("state_write", {"resource": key, "value": value})
        self._values[key] = deepcopy(value)
        self._deleted.discard(key)
        self.accounting.add("mutation_bytes", len(payload.encode("utf-8")))

    def delete(self, key: ResourceKey) -> None:
        self.emit("state_delete", {"resource": key})
        self._values.pop(key, None)
        self._deleted.add(key)

    def initialize(self) -> None:
        with self.accounting.time("materialization"):
            for key in self.plan.initial:
                self.read(key)

    def snapshot(self) -> MaterializedExperience:
        return MaterializedExperience(self.plan, tuple(self._events), sum(self._sizes.values()))

    def finish(self) -> None:
        if self._finished:
            return
        self._finished = True
        with self.accounting.time("residency"):
            for key, value in self._pristine.items():
                self.cache.retain(self._cache_key(key), value, self.accounting, self._residency_event)
        self.accounting.values["resident_working_set_bytes"] = self.snapshot().resident_bytes
        self.accounting.values["peak_resident_working_set_bytes"] = max(
            self.snapshot().resident_bytes, self.accounting.values["peak_resident_working_set_bytes"]
        )
        self.accounting.values["cache_resident_bytes"] = self.cache.used_bytes
        self.accounting.values["cache_peak_bytes"] = self.cache.peak_bytes
        self.emit(
            "residency_summary",
            {
                "working_set_bytes": self.snapshot().resident_bytes,
                "cache_bytes": self.cache.used_bytes,
                "cache_peak_bytes": self.cache.peak_bytes,
            },
        )
