"""A procedural, effectively unbounded CI-safe Universe with progressive state access."""

from __future__ import annotations

import random
from typing import Callable, Iterable, cast

from ..materialization import PagedState
from ..models import (
    JSON,
    Action,
    Address,
    Execution,
    LogicalExperience,
    MaterializationPlan,
    ProbeResult,
    Region,
    ResourceKey,
    VerificationComponent,
    VerificationResult,
)
from ..serialization import canonical


class ToyUniverse:
    identity = "warehouse"
    version = "1"

    def propose(
        self, *, regions: tuple[Region, ...], seed: int, limit: int, excluded: frozenset[str]
    ) -> Iterable[Address]:
        rng = random.Random(seed)
        for _ in range(limit):
            ordinal = rng.randrange(10**18)
            kind = ("standard", "fragile", "regulated")[ordinal % 3]
            region = Region(
                "warehouse",
                kind,
                "fulfillment",
                tools=("inventory", "policy"),
                policies=("shipping",),
                difficulty=(ordinal % 3) / 2,
            )
            address = Address(self.identity, self.version, str(ordinal), region)
            if (not regions or region in regions) and address.uri not in excluded:
                yield address

    def probe(self, address: Address) -> ProbeResult:
        ordinal = int(address.coordinate)
        return ProbeResult(
            LogicalExperience(
                address,
                "Choose the required shipping method.",
                (("fragility", float(ordinal % 3 == 1)), ("regulation", float(ordinal % 3 == 2))),
                ("shipping", address.region.name),
            ),
            uncertainty=0.7,
            cost_usd=0.0,
            evidence=("procedural metadata only; no policy answer read",),
        )


class ToySource:
    def __init__(self, address: Address) -> None:
        self.address = address
        self.version = f"warehouse:1:{address.coordinate}"
        self.loads: list[ResourceKey] = []

    def load(self, key: ResourceKey) -> JSON:
        self.loads.append(key)
        ordinal = int(self.address.coordinate)
        if key == ResourceKey("inventory", "item"):
            return {"kind": self.address.region.name, "policy_ref": "shipping"}
        if key == ResourceKey("policies", "shipping"):
            return {"method": ("ground", "padded", "certified")[ordinal % 3]}
        if key == ResourceKey("payload", "unused"):
            return cast(
                JSON,
                {"noise": "x" * 100_000},
            )
        raise KeyError(key.uri)

    def dependencies(self, key: ResourceKey, value: JSON) -> Iterable[ResourceKey]:
        return ()


class ToyEnvironment:
    def __init__(self) -> None:
        self.universe = ToyUniverse()
        self.sources: list[ToySource] = []

    def plan(self, experience: LogicalExperience) -> MaterializationPlan:
        ordinal = int(experience.address.coordinate)
        logical_bytes = 100_000 + len(canonical({"noise": ""}).encode("utf-8"))
        logical_bytes += len(
            canonical({"kind": experience.address.region.name, "policy_ref": "shipping"}).encode("utf-8")
        )
        logical_bytes += len(
            canonical({"method": ("ground", "padded", "certified")[ordinal % 3]}).encode("utf-8")
        )
        return MaterializationPlan(
            experience,
            (ResourceKey("inventory", "item"),),
            f"warehouse:1:{experience.address.coordinate}",
            full_logical_bytes=logical_bytes,
            full_logical_records=3,
        )

    def source(self, experience: LogicalExperience) -> ToySource:
        source = ToySource(experience.address)
        self.sources.append(source)
        return source

    def execute(self, agent: object, experience: LogicalExperience, state: PagedState) -> Execution:
        if not callable(agent):
            raise TypeError("Toy agent must be callable(experience, paged_state)")
        method = agent(experience, state)
        return Execution(
            experience.address,
            {"method": method},
            (Action("inventory", observation=state.read(ResourceKey("inventory", "item"))),),
            cost_usd=0.0,
            provenance=("deterministic toy runtime",),
        )


class ToyEvaluator:
    def verify(
        self, experience: LogicalExperience, execution: Execution, state: PagedState
    ) -> VerificationResult:
        policy = state.read(ResourceKey("policies", "shipping"))
        assert isinstance(policy, dict)
        passed = execution.outcome["method"] == policy["method"]
        return VerificationResult(
            float(passed),
            passed,
            "toy native shipping policy",
            (VerificationComponent("shipping_policy", float(passed), passed, "policy"),),
            0.0,
        )


def toy_agent(experience: LogicalExperience, state: PagedState) -> str:
    """Deliberately incomplete fixed policy, producing real faults for allocation feedback."""
    item = state.read(ResourceKey("inventory", "item"))
    assert isinstance(item, dict)
    if item["kind"] == "regulated":
        return "ground"
    policy = state.read(ResourceKey("policies", "shipping"))
    assert isinstance(policy, dict)
    return str(policy["method"])


def components() -> tuple[Callable[[LogicalExperience, PagedState], str], ToyEnvironment, ToyEvaluator]:
    return toy_agent, ToyEnvironment(), ToyEvaluator()
