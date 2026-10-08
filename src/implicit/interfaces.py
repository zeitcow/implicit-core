"""Adapter contracts. Enumeration and ownership of an agent runtime are not required."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Protocol

from .models import (
    JSON,
    Address,
    AgentUpdate,
    AllocationDecision,
    CandidateExperience,
    Execution,
    ExploreConfig,
    ExploreResult,
    LogicalExperience,
    MaterializationPlan,
    ProbeResult,
    Region,
    ResourceKey,
    VerificationResult,
)

if TYPE_CHECKING:
    from .learning import LearningState
    from .materialization import PagedState


class Universe(Protocol):
    identity: str
    version: str

    def propose(
        self, *, regions: tuple[Region, ...], seed: int, limit: int, excluded: frozenset[str]
    ) -> Iterable[Address]: ...
    def probe(self, address: Address) -> ProbeResult: ...


class ResourceSource(Protocol):
    version: str

    def load(self, resource: ResourceKey) -> JSON: ...
    def dependencies(self, resource: ResourceKey, value: JSON) -> Iterable[ResourceKey]: ...


class Environment(Protocol):
    @property
    def universe(self) -> Universe: ...

    def plan(self, experience: LogicalExperience) -> MaterializationPlan: ...
    def source(self, experience: LogicalExperience) -> ResourceSource: ...
    def execute(self, agent: object, experience: LogicalExperience, state: PagedState) -> Execution: ...


class Evaluator(Protocol):
    def verify(
        self, experience: LogicalExperience, execution: Execution, state: PagedState
    ) -> VerificationResult: ...


class ExternalLearner(Protocol):
    def update(
        self, experience: LogicalExperience, execution: Execution, verification: VerificationResult
    ) -> AgentUpdate | float | None:
        """Return a versioned replacement. Cost-only returns explicitly mean in-place mutation."""
        ...


class SearchStrategy(Protocol):
    def rank(
        self, probes: tuple[ProbeResult, ...], state: LearningState
    ) -> tuple[CandidateExperience, ...]: ...


class Allocator(Protocol):
    def select(
        self, candidates: tuple[CandidateExperience, ...], state: LearningState, *, seed: int
    ) -> AllocationDecision: ...


class Transport(Protocol):
    def connect(
        self,
        *,
        agent: object,
        environment: Environment,
        evaluator: Evaluator,
        learner: ExternalLearner | None = None,
    ) -> str: ...
    def explore(self, session_id: str, config: ExploreConfig) -> ExploreResult: ...
    def apply_update(self, session_id: str, update: AgentUpdate) -> None: ...
