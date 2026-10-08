"""Connect an existing runner/verifier without changing its model or runtime."""

from dataclasses import dataclass
from typing import Callable

from ..interfaces import ResourceSource, Universe
from ..materialization import PagedState
from ..models import Execution, LogicalExperience, MaterializationPlan, VerificationResult


@dataclass
class CallableEnvironment:
    universe: Universe
    planner: Callable[[LogicalExperience], MaterializationPlan]
    source_factory: Callable[[LogicalExperience], ResourceSource]
    executor: Callable[[object, LogicalExperience, PagedState], Execution]

    def plan(self, experience: LogicalExperience) -> MaterializationPlan:
        return self.planner(experience)

    def source(self, experience: LogicalExperience) -> ResourceSource:
        return self.source_factory(experience)

    def execute(self, agent: object, experience: LogicalExperience, state: PagedState) -> Execution:
        return self.executor(agent, experience, state)


@dataclass
class CallableEvaluator:
    verifier: Callable[[LogicalExperience, Execution, PagedState], VerificationResult]

    def verify(
        self, experience: LogicalExperience, execution: Execution, state: PagedState
    ) -> VerificationResult:
        return self.verifier(experience, execution, state)
