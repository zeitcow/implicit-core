"""Local engine composition. Runtime semantics and authoritative evaluation live in adapters."""

from __future__ import annotations

import sys
import threading
import uuid
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from itertools import islice
from time import perf_counter

from .accounting import Accounting
from .content import ContentStore, payload_hash
from .faults import FaultExtractor
from .interfaces import Allocator, Environment, Evaluator, ExternalLearner, SearchStrategy
from .learning import LearningState
from .materialization import PagedState
from .models import (
    Address,
    AgentUpdate,
    EpisodeResult,
    Event,
    ExperienceFault,
    ExploreConfig,
    ExploreResult,
    LogicalExperience,
    VerificationResult,
)
from .recovery import restore, seed_streams, strategy_record
from .residency import LRUPolicy, ResidencyCache, ResidencyPolicy
from .selection import OrderedSearch, OrderedSelector
from .serialization import canonical, json_value
from .storage import EventStore, MemoryStore


def _update_price(value: AgentUpdate | float | None) -> float | None:
    return value.cost_usd if isinstance(value, AgentUpdate) else value


class EngineSession:
    def __init__(
        self,
        *,
        session_id: str,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        learner: ExternalLearner | None,
        store: EventStore,
        search: SearchStrategy,
        allocator: Allocator,
        cache_bytes: int,
        content_store: ContentStore | None = None,
        agent_version: str | None = None,
        residency_policy: ResidencyPolicy | None = None,
    ) -> None:
        self.session_id = session_id
        self.agent = agent
        self.environment = environment
        self.evaluator = evaluator
        self.learner = learner
        self.store = store
        self.search = search
        self.allocator = allocator
        self.cache = ResidencyCache(cache_bytes, policy=residency_policy)
        self.state = LearningState()
        self.accounting = Accounting()
        self.sequence = 0
        self.attempts = 0
        self._running = False
        self.agent_version = agent_version or f"local:{session_id}:initial"
        self.agent_versions = {self.agent_version}
        self.owner_thread = threading.get_ident()
        self.universe_identity = (environment.universe.identity, environment.universe.version)
        self.episode_id: str | None = None
        self.stage = "idle"
        self._persistence_failed = False
        self._broken = False
        self.reconciled: set[str] = set()
        self.episode_metrics: dict[str, dict[str, int | float]] = {}
        self.content_store = content_store

    def _apply_update(self, update: AgentUpdate) -> None:
        if (
            update.expected_previous_version is not None
            and update.expected_previous_version != self.agent_version
        ):
            raise ValueError("checkpoint predecessor mismatch")
        if update.version in self.agent_versions:
            raise ValueError("replacement must declare a new agent version")
        self.emit(
            "agent_update",
            {
                "previous_version": self.agent_version,
                "version": update.version,
                "checkpoint": update.checkpoint,
                "cost_usd": update.cost_usd,
                "provenance": update.provenance,
                "agent_type": type(update.agent).__qualname__,
            },
        )
        self.agent = update.agent
        self.agent_version = update.version
        self.agent_versions.add(update.version)

    def apply_update(self, update: AgentUpdate) -> None:
        with self.store.lease(self.session_id):
            self._manual_update(update)

    def _manual_update(self, update: AgentUpdate) -> None:
        self._check_owner()
        if self._running:
            raise RuntimeError("cannot replace agent during explore")
        self._apply_update(update)
        self.accounting.cost("external_update", update.cost_usd)
        self.accounting.add("external_updates")
        self.emit("metrics", self.accounting.snapshot())

    def _check_owner(self) -> None:
        if threading.get_ident() != self.owner_thread:
            raise RuntimeError("sessions are thread-affine")
        if self._broken:
            raise RuntimeError("session requires recovery/rebinding after failure")
        if (self.environment.universe.identity, self.environment.universe.version) != self.universe_identity:
            raise ValueError("bound Universe identity/version changed")

    def transition(self, stage: str) -> None:
        self.stage = stage
        self.emit(
            "lifecycle",
            {"stage": stage, "agent_version": self.agent_version, "metrics": self.accounting.snapshot()},
        )

    def emit(
        self, kind: str, payload: object, address: Address | None = None, parent: int | None = None
    ) -> Event:
        data = json_value(payload)
        if kind == "allocation" and isinstance(data, dict):
            observations = data.get("observation_ids")
            if isinstance(observations, list):
                data["observation_ids"] = observations[-32:]
                data["observation_count"] = len(observations)
                data["observations_through_sequence"] = self.sequence
        if kind == "execution" and self.content_store is not None:
            artifact = canonical(data).encode("utf-8")
            if len(artifact) > 65536:
                digest = payload_hash(artifact)
                with self.accounting.time("content_persistence"):
                    written = self.content_store.put(digest, artifact)
                self.accounting.add("retained_artifact_bytes", len(artifact) if written else 0)
                data = {"artifact_hash": digest, "serialized_bytes": len(artifact), "format": "execution-v2"}
        event = Event(
            self.session_id,
            self.sequence + 1,
            kind,
            data,
            address.uri if address else None,
            parent,
            episode_id=self.episode_id,
        )
        try:
            with self.accounting.time("persistence"):
                self.store.append(event)
        except Exception:
            self._broken = True
            self._persistence_failed = True
            raise
        self.sequence = event.sequence
        self.accounting.add("events")
        self.accounting.add("journal_bytes", len(canonical(event).encode("utf-8")))
        return event

    def _episode(self, config: ExploreConfig) -> EpisodeResult | None:
        runtime_start = perf_counter()
        snapshots_before = self.accounting.values.get("snapshot_seconds", 0)
        universe = self.environment.universe
        self.episode_id = f"{self.session_id}:{self.attempts}"
        episode_version = self.agent_version
        before = self.accounting.snapshot()
        seeds = seed_streams(config.seed, self.attempts)
        seed = config.seed + self.attempts  # Preserve proposal trajectory; other streams are independent.
        seeds["proposal"] = seed
        self.attempts += 1
        self.emit(
            "attempt",
            {"attempts": self.attempts, "seeds": seeds, "seed_protocol": 2, "agent_version": episode_version},
        )
        self.transition("candidate")
        with self.accounting.time("search"):
            parent = self.emit(
                "search",
                {
                    "seed": seed,
                    "regions": config.regions,
                    "excluded_count": len(self.state.visited),
                    "observation_count": len(self.state.observations),
                },
            )
            proposals = universe.propose(
                regions=config.regions,
                seed=seed,
                limit=config.candidate_pool,
                excluded=frozenset(self.state.visited),
            )
            probes = []
            seen: set[str] = set()
            for address in islice(proposals, config.candidate_pool):
                self.accounting.add("candidates_considered")
                if address.universe != universe.identity or address.version != universe.version:
                    raise ValueError("Universe proposed an address outside its versioned space")
                if address.uri in seen or address.uri in self.state.visited:
                    continue
                seen.add(address.uri)
                self.accounting.add("regions_searched")
                self.accounting.add("probes")
                self.stage = "probing"
                probe = self.accounting.invoke("probe", lambda: universe.probe(address), lambda p: p.cost_usd)
                if probe.experience.address != address:
                    raise ValueError("probe/address mismatch")
                self.emit("probe", probe, address, parent.sequence)
                probes.append(probe)
            self.stage = "searching"
            candidates = self.search.rank(tuple(probes), self.state)
            if any(c.probe not in probes for c in candidates):
                raise ValueError("search returned an unprobed candidate")
            self.emit("search_result", candidates, parent=parent.sequence)
        if not candidates:
            self.transition("complete")
            self.emit("exhausted", {"reason": "no candidates in bounded proposal window"})
            return None
        self.stage = "allocating"
        with self.accounting.time("allocation"):
            decision = self.allocator.select(candidates, self.state, seed=seeds["allocation"])
        if decision.selected not in candidates:
            raise ValueError("allocator selected an unprobed candidate")
        self.transition("selected")
        experience = decision.selected.experience
        address = experience.address
        selected_event = self.emit("allocation", decision, address, parent.sequence)
        self.accounting.add("experiences_selected")
        self.stage = "planning"
        with self.accounting.time("planning"):
            plan = self.environment.plan(experience)
            source = self.environment.source(experience)
        if plan.experience != experience:
            raise ValueError("materialization plan refers to a different experience")
        self.emit("materialization_plan", plan, address, selected_event.sequence)
        self.transition("planned")
        if plan.full_logical_bytes is not None:
            self.accounting.add("full_logical_bytes", plan.full_logical_bytes)
        if plan.full_logical_records is not None:
            self.accounting.add("full_logical_records", plan.full_logical_records)

        def emit_page(kind: str, value: object) -> None:
            self.emit(kind, value, address, selected_event.sequence)

        pager = PagedState(plan, source, self.cache, self.accounting, emit_page, self.content_store)
        pager.seeds = seeds
        self.accounting.add("experiences_materialized")
        try:
            self.transition("materializing")
            pager.initialize()
            pager.phase = "execution"
            self.transition("executing")
            self.accounting.add("executions")
            execution = self.accounting.invoke(
                "execution",
                lambda: self.environment.execute(self.agent, experience, pager),
                lambda e: e.cost_usd,
            )
            if execution.address != address:
                raise ValueError("execution/address mismatch")
            execute_event = self.emit("execution", execution, address, selected_event.sequence)
            self.accounting.add(
                "runtime_only_seconds",
                max(
                    0,
                    perf_counter()
                    - runtime_start
                    - (self.accounting.values.get("snapshot_seconds", 0) - snapshots_before),
                ),
            )
            pager.phase = "verification"
            self.transition("verifying")
            self.accounting.add("verifications")
            verification = self.accounting.invoke(
                "verification",
                lambda: self.evaluator.verify(experience, execution, pager),
                lambda v: v.cost_usd,
            )
            verify_event = self.emit("verification", verification, address, execute_event.sequence)
            self.accounting.reward(verification.reward)
            self.accounting.add("successes", int(verification.passed))
            observation_id = f"{self.session_id}:{verify_event.sequence}"
            self.transition("fault_extraction")
            with self.accounting.time("fault_extraction"):
                faults = FaultExtractor().extract(
                    experience, execution, verification, self.state, observation_id=observation_id
                )
            for fault in faults:
                self.accounting.add("faults_discovered")
                self.emit("fault", fault, address, verify_event.sequence)
            self.transition("learning")
            # Commit verified intelligence before any fallible external training call.
            self.emit(
                "observation",
                {"experience": experience, "observation_id": observation_id, "cost_usd": execution.cost_usd},
                address,
                verify_event.sequence,
            )
            learning = self.state.observe(
                experience, verification, faults, execution.cost_usd, observation_id, self.learner is not None
            )
            with self.accounting.time("learning"):
                update_cost = None
                learner = self.learner
                if learner is not None:
                    updated = self.accounting.invoke(
                        "external_update",
                        lambda: learner.update(experience, execution, verification),
                        _update_price,
                    )
                    if isinstance(updated, AgentUpdate):
                        self._apply_update(updated)
                        update_cost = updated.cost_usd
                    else:
                        update_cost = updated
                        self._apply_update(
                            AgentUpdate(
                                self.agent,
                                f"local:{self.session_id}:inplace:{self.attempts}",
                                updated,
                                provenance=("unverified in-place runtime mutation",),
                            )
                        )
                    self.accounting.add("external_updates")
            learning = replace(learning, update_cost_usd=update_cost)
            self.accounting.add("coverage_observations")
            self.emit("learning", learning, address, verify_event.sequence)
            self.transition("residency")
            pager.finish()
            metrics = {key: value - before.get(key, 0) for key, value in self.accounting.snapshot().items()}
            result = EpisodeResult(
                decision,
                pager.snapshot(),
                execution,
                verification,
                faults,
                learning,
                episode_version,
                self.episode_id,
                metrics,
            )
            self.episode_metrics[self.episode_id] = {
                k: v for k, v in metrics.items() if k.endswith("_cost_usd")
            }
            self.emit(
                "episode",
                {
                    "metrics": metrics,
                    "execution_sequence": execute_event.sequence,
                    "verification_sequence": verify_event.sequence,
                    "observation_id": observation_id,
                    "agent_version": episode_version,
                },
                address,
                verify_event.sequence,
            )
            self.transition("complete")
            return result
        finally:
            if sys.exc_info()[0] is None:
                pager.finish()
            else:
                try:
                    pager.finish()
                except Exception:
                    self.accounting.add("residency_cleanup_errors")

    def reconcile_costs(self, episode_id: str, prices: dict[str, float]) -> None:
        with self.store.lease(self.session_id):
            self._reconcile_costs(episode_id, prices)

    def _reconcile_costs(self, episode_id: str, prices: dict[str, float]) -> None:
        self._check_owner()
        if self._running:
            raise RuntimeError("cannot reconcile during explore")
        if episode_id in self.reconciled:
            raise ValueError("episode costs already reconciled")
        baseline = self.episode_metrics[episode_id]
        if not prices or set(prices) - {"verification", "materialization", "probe", "other"}:
            raise ValueError("unsupported price reconciliation stages")
        projected = deepcopy(self.accounting)
        for stage, price in prices.items():
            projected.reconcile(stage, price, float(baseline.get(stage + "_cost_usd", 0)))
        self.emit(
            "price_reconciliation",
            {"episode_id": episode_id, "prices": prices, "metrics": projected.snapshot()},
        )
        for stage, price in prices.items():
            self.accounting.reconcile(stage, price, float(baseline.get(stage + "_cost_usd", 0)))
        self.reconciled.add(episode_id)

    def explore(self, config: ExploreConfig) -> ExploreResult:
        self._check_owner()
        if self._running:
            raise RuntimeError("concurrent or recursive explore on the same session is unsupported")
        writer = getattr(self.store, "write_session", nullcontext)
        with self.store.lease(self.session_id), writer():
            return self._explore(config)

    def _explore(self, config: ExploreConfig) -> ExploreResult:
        if self._running:
            raise RuntimeError("concurrent or recursive explore on the same session is unsupported")
        self._running = True
        start = perf_counter()
        first = self.sequence
        episodes = []
        exhausted = False
        try:
            self.emit("explore", config)
            for _ in range(config.episodes):
                episode = self._episode(config)
                if episode is None:
                    exhausted = True
                    break
                episodes.append(episode)
        except Exception as exc:
            self._broken = True
            if not self._persistence_failed:
                self.emit(
                    "error",
                    {
                        "type": type(exc).__name__,
                        "message": "adapter or persistence operation failed; inspect category and stage",
                        "stage": self.stage,
                        "classification": (
                            "missing_resource"
                            if isinstance(exc, KeyError)
                            else "invalid_adapter_contract"
                            if isinstance(exc, (ValueError, TypeError))
                            else self.stage + "_failure"
                        ),
                        "status": "failed",
                    },
                )
            raise
        finally:
            try:
                self.accounting.add("wall_seconds", perf_counter() - start)
                # This event is a boundary snapshot. Returned counters also include its write.
                if not self._persistence_failed:
                    self.emit("metrics", self.accounting.snapshot())
            finally:
                self._running = False
        return ExploreResult(
            self.session_id,
            tuple(episodes),
            self.accounting.snapshot(),
            self.store.events(self.session_id, after_sequence=first),
            exhausted,
        )


class Engine:
    def __init__(
        self,
        *,
        store: EventStore | None = None,
        search: SearchStrategy | None = None,
        allocator: Allocator | None = None,
        cache_bytes: int = 1_048_576,
        content_store: ContentStore | None = None,
        residency_policy: ResidencyPolicy | None = None,
    ) -> None:
        self.store = store if store is not None else MemoryStore()
        self.search = search if search is not None else OrderedSearch()
        self.allocator = allocator if allocator is not None else OrderedSelector()
        self.cache_bytes = cache_bytes
        self.content_store = content_store
        self.residency_policy = residency_policy or LRUPolicy()
        self.sessions: dict[str, EngineSession] = {}

    def connect(
        self,
        *,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        learner: ExternalLearner | None = None,
        agent_version: str | None = None,
    ) -> str:
        if agent_version is not None and not agent_version.strip():
            raise ValueError("agent version must be nonempty")
        for value, methods in (
            (environment, ("plan", "source", "execute")),
            (environment.universe, ("propose", "probe")),
            (evaluator, ("verify",)),
        ):
            if any(not callable(getattr(value, name, None)) for name in methods):
                raise TypeError(f"{type(value).__name__} does not implement {methods}")
        session_id = uuid.uuid4().hex
        self.store.create_session(
            session_id,
            json_value(
                {
                    "schema_version": 2,
                    "agent_version": agent_version or f"local:{session_id}:initial",
                    "strategy_config": {
                        "search": strategy_record(self.search),
                        "allocator": strategy_record(self.allocator),
                    },
                    "universe": environment.universe.identity,
                    "version": environment.universe.version,
                    "environment": type(environment).__qualname__,
                    "agent": type(agent).__qualname__,
                    "evaluator": type(evaluator).__qualname__,
                    "external_learner": learner is not None,
                    "search": type(self.search).__qualname__,
                    "allocator": type(self.allocator).__qualname__,
                    "cache_bytes": self.cache_bytes,
                    "residency_policy": strategy_record(self.residency_policy),
                    "content_retention": "content-addressed"
                    if self.content_store is not None
                    else "metadata-only",
                }
            ),
        )
        self.sessions[session_id] = EngineSession(
            session_id=session_id,
            agent=agent,
            environment=environment,
            evaluator=evaluator,
            learner=learner,
            store=self.store,
            search=deepcopy(self.search),
            allocator=deepcopy(self.allocator),
            cache_bytes=self.cache_bytes,
            content_store=self.content_store,
            agent_version=agent_version,
            residency_policy=deepcopy(self.residency_policy),
        )
        return session_id

    def close(self, session_id: str) -> None:
        session = self.sessions[session_id]
        with self.store.lease(session_id):
            if session._running:
                raise RuntimeError("cannot close during explore")
            if threading.get_ident() != session.owner_thread:
                raise RuntimeError("sessions are thread-affine")
            del self.sessions[session_id]

    def explore(self, session_id: str, config: ExploreConfig) -> ExploreResult:
        return self.sessions[session_id].explore(config)

    def resume(
        self,
        session_id: str,
        *,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        agent_version: str,
        learner: ExternalLearner | None = None,
        abandon_incomplete: bool = False,
    ) -> str:
        with self.store.lease(session_id):
            return self._resume(
                session_id,
                agent=agent,
                environment=environment,
                evaluator=evaluator,
                agent_version=agent_version,
                learner=learner,
                abandon_incomplete=abandon_incomplete,
            )

    def _resume(
        self,
        session_id: str,
        *,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        agent_version: str,
        learner: ExternalLearner | None,
        abandon_incomplete: bool,
    ) -> str:
        if session_id in self.sessions:
            raise ValueError("session already bound in this engine")
        manifest = self.store.manifest(session_id)
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 2:
            raise ValueError("legacy journal remains readable; resume requires a v2 manifest")
        if (manifest["universe"], manifest["version"]) != (
            environment.universe.identity,
            environment.universe.version,
        ):
            raise ValueError("resume Universe/version mismatch")
        if manifest["external_learner"] != (learner is not None):
            raise ValueError("resume learner binding mismatch")
        if manifest["strategy_config"] != json_value(
            {"search": strategy_record(self.search), "allocator": strategy_record(self.allocator)}
        ):
            raise ValueError("resume strategy configuration mismatch")
        if (
            manifest["environment"] != type(environment).__qualname__
            or manifest["evaluator"] != type(evaluator).__qualname__
        ):
            raise ValueError("resume adapter binding types mismatch")
        if type(self.search).__module__ not in {"implicit.search", "implicit.selection"} or type(
            self.allocator
        ).__module__ not in {"implicit.allocation", "implicit.selection"}:
            raise ValueError("custom strategy state recovery requires an explicit adapter; built-ins only")
        if manifest.get("residency_policy") != json_value(strategy_record(self.residency_policy)):
            raise ValueError("resume residency policy mismatch")
        records = self.store.events(session_id)
        session = EngineSession(
            session_id=session_id,
            agent=agent,
            environment=environment,
            evaluator=evaluator,
            learner=learner,
            store=self.store,
            search=deepcopy(self.search),
            allocator=deepcopy(self.allocator),
            cache_bytes=int(str(manifest["cache_bytes"])),
            content_store=self.content_store,
            agent_version=str(manifest["agent_version"]),
            residency_policy=deepcopy(self.residency_policy),
        )
        verification = None
        faults: list[ExperienceFault] = []
        incomplete = False
        for event in records:
            if event.schema_version != 2:
                raise ValueError("unsupported event schema")
            payload = event.payload
            session.sequence = event.sequence
            if not isinstance(payload, dict):
                continue
            if event.kind == "attempt":
                session.attempts = int(str(payload["attempts"]))
                session.episode_id = event.episode_id
                incomplete = True
                faults = []
                verification = None
            elif event.kind == "verification":
                verification = restore(VerificationResult, payload)
            elif event.kind == "fault":
                faults.append(restore(ExperienceFault, payload))
            elif event.kind == "observation":
                if verification is None:
                    raise ValueError("observation missing verification")
                cost = payload["cost_usd"]
                session.state.observe(
                    restore(LogicalExperience, payload["experience"]),
                    verification,
                    tuple(faults),
                    float(cost) if isinstance(cost, (int, float)) else None,
                    str(payload["observation_id"]),
                    learner is not None,
                )
            elif event.kind == "agent_update":
                version = str(payload["version"])
                if version in session.agent_versions or payload["previous_version"] != session.agent_version:
                    raise ValueError("invalid checkpoint transition history")
                session.agent_version = version
                session.agent_versions.add(version)
                price = payload.get("cost_usd")
                session.accounting.cost(
                    "external_update", float(price) if isinstance(price, (int, float)) else None
                )
                session.accounting.add("external_updates")
            elif event.kind == "episode":
                metrics = payload.get("metrics")
                if isinstance(metrics, dict) and event.episode_id is not None:
                    session.episode_metrics[event.episode_id] = {
                        k: v for k, v in metrics.items() if isinstance(v, (int, float))
                    }
            elif event.kind == "price_reconciliation":
                session.reconciled.add(str(payload["episode_id"]))
                metrics = payload["metrics"]
                if isinstance(metrics, dict):
                    session.accounting.values.update(
                        {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
                    )
            elif event.kind == "metrics":
                session.accounting.values.update(
                    {k: v for k, v in payload.items() if isinstance(v, (int, float))}
                )
            elif event.kind == "lifecycle":
                metrics = payload.get("metrics")
                if isinstance(metrics, dict):
                    session.accounting.values.update(
                        {k: v for k, v in metrics.items() if isinstance(v, (int, float))}
                    )
                session.stage = str(payload["stage"])
                if session.stage == "complete":
                    incomplete = False
            elif event.kind == "recovery":
                incomplete = False
        if session.agent_version != agent_version:
            raise ValueError("rebound checkpoint identity does not match journal")
        if incomplete and not abandon_incomplete:
            raise ValueError(
                "incomplete episode: reconcile external effects, then explicitly abandon_incomplete"
            )
        session.emit(
            "recovery",
            {
                "abandoned_incomplete": incomplete,
                "cache": "cold",
                "unreturned_usage": "unknown" if incomplete else "none",
                "agent_version": agent_version,
            },
        )
        self.sessions[session_id] = session
        return session_id
