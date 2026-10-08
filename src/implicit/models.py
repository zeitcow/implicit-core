"""Typed, transport-serializable lifecycle records. No environment state in logical records."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, TypeAlias
from urllib.parse import quote

JSON: TypeAlias = None | bool | int | float | str | list["JSON"] | dict[str, "JSON"]


@dataclass(frozen=True, slots=True)
class Region:
    domain: str
    name: str
    capability: str = ""
    constraints: tuple[tuple[str, str], ...] = ()
    tools: tuple[str, ...] = ()
    policies: tuple[str, ...] = ()
    difficulty: float | None = None
    failure_family: str | None = None

    @property
    def key(self) -> str:
        return "/".join(quote(x, safe="") for x in (self.domain, self.name, self.capability))


@dataclass(frozen=True, slots=True)
class Address:
    universe: str
    version: str
    coordinate: str
    region: Region
    coordinates: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not all((self.universe, self.version, self.coordinate)):
            raise ValueError("address requires universe, version and coordinate")

    @property
    def uri(self) -> str:
        # Routing metadata is not identity. Versions isolate caches and provenance.
        return "implicit://" + "/".join(
            quote(x, safe="") for x in (self.universe, self.version, self.coordinate)
        )


@dataclass(frozen=True, slots=True)
class LogicalExperience:
    address: Address
    instruction: str
    features: tuple[tuple[str, float], ...] = ()
    tags: tuple[str, ...] = ()
    replay: Literal["exact", "frozen", "content"] = "exact"


@dataclass(frozen=True, slots=True)
class ProbeResult:
    experience: LogicalExperience
    estimated_cost: float = 1.0
    uncertainty: float = 0.5
    expected_value: float = 1.0
    cost_usd: float | None = None
    evidence: tuple[str, ...] = ()
    kind: str = "metadata"
    uncertainty_semantics: str = "heuristic"
    provenance: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.cost_usd is not None and (not math.isfinite(self.cost_usd) or self.cost_usd < 0):
            raise ValueError("probe cost must be finite and nonnegative")
        if not math.isfinite(self.estimated_cost) or self.estimated_cost <= 0:
            raise ValueError("estimated_cost must be finite and positive")
        if not 0 <= self.uncertainty <= 1:
            raise ValueError("uncertainty must be in [0, 1]")
        if not math.isfinite(self.expected_value) or self.expected_value < 0:
            raise ValueError("expected_value must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class CandidateExperience:
    probe: ProbeResult
    score: float
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not math.isfinite(self.score):
            raise ValueError("candidate score must be finite")

    @property
    def experience(self) -> LogicalExperience:
        return self.probe.experience


@dataclass(frozen=True, slots=True)
class ResourceKey:
    namespace: str
    key: str

    @property
    def uri(self) -> str:
        return "/".join(quote(x, safe="") for x in (self.namespace, self.key))


@dataclass(frozen=True, slots=True)
class MaterializationPlan:
    experience: LogicalExperience
    initial: tuple[ResourceKey, ...]
    source_version: str
    full_logical_bytes: int | None = None
    full_logical_records: int | None = None
    rationale: str = "initial dependency roots; remaining state is resolved on demand"


@dataclass(frozen=True, slots=True)
class MaterializationEvent:
    address: Address
    resource: ResourceKey
    content_hash: str
    serialized_bytes: int
    seconds: float
    cache_hit: bool
    phase: str
    source_version: str = ""


@dataclass(frozen=True, slots=True)
class MaterializedExperience:
    plan: MaterializationPlan
    resources: tuple[MaterializationEvent, ...]
    resident_bytes: int


@dataclass(frozen=True, slots=True)
class Action:
    tool: str
    arguments: dict[str, JSON] = field(default_factory=dict)
    observation: JSON = None
    stage: str = "execution"


@dataclass(frozen=True, slots=True)
class Execution:
    address: Address
    outcome: dict[str, JSON]
    actions: tuple[Action, ...] = ()
    cost_usd: float | None = None
    termination: str = "completed"
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationComponent:
    name: str
    score: float
    passed: bool
    stage: str = "verification"
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationResult:
    reward: float
    passed: bool
    authority: str
    components: tuple[VerificationComponent, ...] = ()
    cost_usd: float | None = None
    evidence: dict[str, JSON] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(self.reward) or not self.authority:
            raise ValueError("verification requires finite reward and explicit authority")


@dataclass(frozen=True, slots=True)
class ExperienceFault:
    fault_id: str
    address: Address
    component: str
    stage: str
    severity: float
    confidence: float
    uncertainty: float
    tool_context: tuple[str, ...]
    policy_context: tuple[str, ...]
    tags: tuple[str, ...]
    features: tuple[tuple[str, float], ...]
    cost_usd: float | None
    provenance: tuple[str, ...]
    hierarchy: tuple[str, ...]
    repeats: int = 1
    saturated: bool = False

    @property
    def signature(self) -> str:
        return "/".join(quote(x, safe="") for x in self.hierarchy)


@dataclass(frozen=True, slots=True)
class Alternative:
    address: Address
    utility: float
    estimated_cost: float
    value: float
    confidence: float
    influences: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AllocationDecision:
    selected: CandidateExperience
    mode: Literal["target", "explore", "abstain"]
    reason: str
    alternatives: tuple[Alternative, ...]
    observation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LearningEvent:
    address: Address
    observation_id: str
    region_visits: int
    posterior_failure: float
    mean_cost: float | None
    priority: float
    external_update: bool
    update_cost_usd: float | None = None


@dataclass(frozen=True, slots=True)
class AgentUpdate:
    """A replacement runtime bound to a declared checkpoint version.

    The opaque agent stays local; only checkpoint, version, cost and provenance are journaled.
    """

    agent: object = field(repr=False, compare=False)
    version: str
    cost_usd: float | None
    checkpoint: JSON = None
    provenance: tuple[str, ...] = ()
    expected_previous_version: str | None = None

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("updated agent requires a version")
        if self.cost_usd is not None and (not math.isfinite(self.cost_usd) or self.cost_usd < 0):
            raise ValueError("update cost must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class ResidencyEvent:
    cache_key: str
    action: Literal["retain", "reuse", "evict", "rematerialize"]
    bytes: int
    reason: str


@dataclass(frozen=True, slots=True)
class ExploreConfig:
    episodes: int = 8
    candidate_pool: int = 12
    seed: int = 0
    regions: tuple[Region, ...] = ()

    def __post_init__(self) -> None:
        if self.episodes < 1 or self.candidate_pool < 1:
            raise ValueError("episodes and candidate_pool must be positive")


@dataclass(frozen=True, slots=True)
class Event:
    session_id: str
    sequence: int
    kind: str
    payload: JSON
    address: str | None = None
    parent_sequence: int | None = None
    schema_version: int = 2
    episode_id: str | None = None


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    allocation: AllocationDecision
    materialization: MaterializedExperience
    execution: Execution
    verification: VerificationResult
    faults: tuple[ExperienceFault, ...]
    learning: LearningEvent
    agent_version: str = "unspecified"
    episode_id: str = ""
    metrics: dict[str, int | float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExploreResult:
    session_id: str
    episodes: tuple[EpisodeResult, ...]
    metrics: dict[str, int | float]
    events: tuple[Event, ...]
    exhausted: bool = False
