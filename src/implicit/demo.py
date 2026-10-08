"""Offline public demonstration of addressed experience materialization."""

from __future__ import annotations

from typing import Any

from .adapters.toy import ToyEnvironment, ToyEvaluator, ToySource
from .materialization import PagedState
from .models import ExploreConfig, LogicalExperience, ResourceKey
from .sdk import Implicit
from .serialization import canonical, content_hash


def benchmark() -> dict[str, Any]:
    environment = ToyEnvironment()

    def agent(experience: LogicalExperience, state: PagedState) -> str:
        item = state.read(ResourceKey("inventory", "item"))
        assert isinstance(item, dict)
        policy = state.read(ResourceKey("policies", str(item["policy_ref"])))
        assert isinstance(policy, dict)
        return str(policy["method"])

    session = Implicit().connect(agent=agent, environment=environment, evaluator=ToyEvaluator())
    result = session.explore(ExploreConfig(episodes=1, seed=0, candidate_pool=1))
    episode = result.episodes[0]
    experience = episode.allocation.selected.experience
    source = ToySource(experience.address)
    eager = {
        key.uri: source.load(key)
        for key in (
            ResourceKey("inventory", "item"),
            ResourceKey("policies", "shipping"),
            ResourceKey("payload", "unused"),
        )
    }
    full_bytes = sum(len(canonical(value).encode()) for value in eager.values())
    lazy_bytes = episode.materialization.resident_bytes
    eager_result = eager[ResourceKey("policies", "shipping").uri]
    assert isinstance(eager_result, dict)
    equivalent = eager_result["method"] == episode.execution.outcome["method"] and episode.verification.passed
    return {
        "possible_experiences": 10**18,
        "address": experience.address.uri,
        "eager_materialized_bytes": full_bytes,
        "implicit_materialized_bytes": lazy_bytes,
        "eager_resources": len(eager),
        "implicit_resources": len(episode.materialization.resources),
        "reduction": 1 - lazy_bytes / full_bytes,
        "semantic_equivalence": equivalent,
        "result": episode.execution.outcome,
        "seed": 0,
        "provenance_hash": content_hash(experience),
        "paid_calls": 0,
        "wall_seconds": result.metrics["wall_seconds"],
        "scope": "deterministic toy serialized state; not process memory",
    }
