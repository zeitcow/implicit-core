"""Adaptive allocation state is distinct from an optional actual agent update."""

from dataclasses import dataclass, field
from math import sqrt

from .models import ExperienceFault, LearningEvent, LogicalExperience, VerificationResult
from .serialization import content_hash


@dataclass
class RegionStatistics:
    visits: int = 0
    failures: int = 0
    reward_sum: float = 0.0
    cost_sum: float = 0.0
    cost_reports: int = 0

    @property
    def posterior_failure(self) -> float:
        return (self.failures + 1) / (self.visits + 2)

    @property
    def mean_cost(self) -> float | None:
        return self.cost_sum / self.cost_reports if self.cost_reports else None


@dataclass
class FaultAggregate:
    representative: ExperienceFault
    count: int
    weight: float
    first_seen: str
    last_seen: str


@dataclass
class LearningState:
    regions: dict[str, RegionStatistics] = field(default_factory=dict)
    faults: list[ExperienceFault] = field(default_factory=list)
    visited: set[str] = field(default_factory=set)
    observations: list[str] = field(default_factory=list)
    fault_memory: dict[str, FaultAggregate] = field(default_factory=dict)
    hierarchy_counts: dict[tuple[str, ...], int] = field(default_factory=dict)
    _observation_ids: set[str] = field(default_factory=set)

    @property
    def fault_count(self) -> int:
        return sum(a.count for a in self.fault_memory.values()) if self.fault_memory else len(self.faults)

    def weighted_faults(self) -> list[tuple[ExperienceFault, float, int]]:
        if not self.fault_memory:
            return [(f, 1 / sqrt(f.repeats), 1) for f in self.faults]
        return [(a.representative, a.weight, a.count) for a in self.fault_memory.values()]

    def observe(
        self,
        experience: LogicalExperience,
        verification: VerificationResult,
        faults: tuple[ExperienceFault, ...],
        cost_usd: float | None,
        observation_id: str,
        external_update: bool,
        update_cost_usd: float | None = None,
    ) -> LearningEvent:
        if observation_id in self._observation_ids:
            raise ValueError("duplicate observation")
        self._observation_ids.add(observation_id)
        self.visited.add(experience.address.uri)
        self.observations.append(observation_id)
        for fault in faults:
            signature = content_hash(
                (
                    fault.hierarchy,
                    fault.address.region.key,
                    fault.features,
                    fault.tags,
                    fault.tool_context,
                    fault.policy_context,
                    fault.severity,
                    fault.confidence,
                )
            )
            aggregate = self.fault_memory.get(signature)
            if aggregate is None:
                aggregate = FaultAggregate(fault, 0, 0, observation_id, observation_id)
                self.fault_memory[signature] = aggregate
                self.faults.append(fault)
            aggregate.count += 1
            aggregate.weight += 1 / sqrt(fault.repeats)
            aggregate.last_seen = observation_id
            self.hierarchy_counts[fault.hierarchy] = self.hierarchy_counts.get(fault.hierarchy, 0) + 1
        stats = self.regions.setdefault(experience.address.region.key, RegionStatistics())
        stats.visits += 1
        stats.failures += int(not verification.passed)
        stats.reward_sum += verification.reward
        if cost_usd is not None:
            stats.cost_sum += cost_usd
            stats.cost_reports += 1
        priority = stats.posterior_failure / ((1 + stats.visits) ** 0.65)
        return LearningEvent(
            experience.address,
            observation_id,
            stats.visits,
            stats.posterior_failure,
            stats.mean_cost,
            priority,
            external_update,
            update_cost_usd,
        )
