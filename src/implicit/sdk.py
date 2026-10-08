"""Public client. Local runtime bindings are not a wire protocol for opaque Python objects."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from .interfaces import Environment, Evaluator, ExternalLearner, Transport
from .models import AgentUpdate, Event, ExploreConfig, ExploreResult
from .storage import SQLiteEventStore

if TYPE_CHECKING:
    from .engine import Engine


class LocalTransport:
    def __init__(self, engine: Engine | None = None, *, database: str | Path | None = None) -> None:
        if engine is not None and database is not None:
            raise ValueError("supply an engine or a database, not both")
        if engine is None:
            from .engine import Engine

            engine = Engine(store=SQLiteEventStore(database)) if database is not None else Engine()
        self.engine = engine

    def connect(
        self,
        *,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        learner: ExternalLearner | None = None,
        agent_version: str | None = None,
    ) -> str:
        return self.engine.connect(
            agent=agent,
            environment=environment,
            evaluator=evaluator,
            learner=learner,
            agent_version=agent_version,
        )

    def explore(self, session_id: str, config: ExploreConfig) -> ExploreResult:
        return self.engine.explore(session_id, config)

    def apply_update(self, session_id: str, update: AgentUpdate) -> None:
        self.engine.sessions[session_id].apply_update(update)


class Session:
    def __init__(self, transport: Transport, session_id: str) -> None:
        self.transport = transport
        self.session_id = session_id

    def events(self, *, after_sequence: int = 0) -> tuple[Event, ...]:
        if not isinstance(self.transport, LocalTransport):
            raise ValueError("journal inspection requires LocalTransport")
        return self.transport.engine.store.events(self.session_id, after_sequence=after_sequence)

    def metrics(self) -> dict[str, int | float]:
        if not isinstance(self.transport, LocalTransport):
            raise ValueError("metrics inspection requires LocalTransport")
        return self.transport.engine.sessions[self.session_id].accounting.snapshot()

    def close(self) -> None:
        """Release local runtime ownership; durable history remains available for rebinding."""
        if not isinstance(self.transport, LocalTransport):
            raise ValueError("runtime release requires LocalTransport")
        self.transport.engine.close(self.session_id)

    def reconcile_costs(self, episode_id: str, prices: dict[str, float]) -> None:
        if not isinstance(self.transport, LocalTransport):
            raise ValueError("cost reconciliation requires LocalTransport")
        self.transport.engine.sessions[self.session_id].reconcile_costs(episode_id, prices)

    def apply_update(self, update: AgentUpdate) -> None:
        """Continue this session with a replacement agent; keep intelligence and residency."""
        self.transport.apply_update(self.session_id, update)

    def explore(
        self, config: ExploreConfig | None = None, *, episodes: int | None = None, seed: int | None = None
    ) -> ExploreResult:
        config = config or ExploreConfig()
        if episodes is not None:
            config = replace(config, episodes=episodes)
        if seed is not None:
            config = replace(config, seed=seed)
        return self.transport.explore(self.session_id, config)


class Implicit:
    def __init__(self, *, transport: Transport | None = None, database: str | Path | None = None) -> None:
        if transport is not None and database is not None:
            raise ValueError("database is a LocalTransport option; do not supply both")
        self.transport = transport if transport is not None else LocalTransport(database=database)

    def connect(
        self,
        *,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        learner: ExternalLearner | None = None,
        agent_version: str | None = None,
    ) -> Session:
        if agent_version is not None:
            if not isinstance(self.transport, LocalTransport):
                raise ValueError("checkpoint runtime binding requires LocalTransport")
            session_id = self.transport.connect(
                agent=agent,
                environment=environment,
                evaluator=evaluator,
                learner=learner,
                agent_version=agent_version,
            )
        else:
            session_id = self.transport.connect(
                agent=agent, environment=environment, evaluator=evaluator, learner=learner
            )
        return Session(self.transport, session_id)

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
    ) -> Session:
        if not isinstance(self.transport, LocalTransport):
            raise ValueError("runtime rebinding requires LocalTransport")
        self.transport.engine.resume(
            session_id,
            agent=agent,
            environment=environment,
            evaluator=evaluator,
            agent_version=agent_version,
            learner=learner,
            abandon_incomplete=abandon_incomplete,
        )
        return Session(self.transport, session_id)
